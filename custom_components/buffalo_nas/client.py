"""Client for the Buffalo TeraStation web interface's JSON-RPC API."""

from __future__ import annotations

import asyncio
from itertools import count
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout
from yarl import URL

from .const import NASAPI_PATH

SESSION_EXPIRED = -119
METHOD_UNSUPPORTED = {-32601, -109, -121}
TIMEOUT = ClientTimeout(total=8)


class BuffaloError(Exception):
    """The NAS could not fulfill a request."""


class BuffaloAuthError(BuffaloError):
    """The NAS rejected the credentials or a new session."""


class BuffaloRpcError(BuffaloError):
    """An error returned by the NAS."""

    def __init__(self, method: str, code: int) -> None:
        super().__init__(f"{method} returned error {code}")
        self.code = code


def base_url(host: str) -> URL:
    """Accept an HTTP(S) origin or a bare address (HTTPS by default)."""
    host = host.strip()
    try:
        url = URL(host if "://" in host else f"https://{host}")
        if (
            url.scheme in {"http", "https"}
            and url.host
            and url.path in {"", "/"}
            and not any(char in host for char in "@?#\\")
            and not any(char.isspace() for char in host)
            and url.port is not None
            and 0 < url.port < 65536
        ):
            return url.origin()
    except (ValueError, UnicodeError):
        pass
    raise ValueError("Enter an HTTP(S) origin without a path or credentials")


class BuffaloNASClient:
    """Reuse a NAS login and renew it only when the firmware rejects the SID."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        username: str,
        password: str,
        verify_ssl: bool,
    ) -> None:
        self.url = base_url(host)
        self._session = session
        self._username = username
        self._password = password
        self._verify_ssl = verify_ssl
        self._ids = count(1)
        self._sid: str | None = None
        self._closed = False
        self._login_lock = asyncio.Lock()
        self._method_aliases: dict[str, str] = {}

    async def _rpc(self, method: str, params: dict[str, Any]) -> Any:
        request_id = next(self._ids)
        try:
            async with self._session.post(
                self.url.with_path(NASAPI_PATH),
                json={
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": request_id,
                },
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": str(self.url.with_path("/detail.html")),
                },
                ssl=self._verify_ssl,
                timeout=TIMEOUT,
                allow_redirects=False,
            ) as response:
                if not 200 <= response.status < 300:
                    raise BuffaloRpcError(method, response.status)
                # Some firmware serves JSON without an application/json MIME type.
                payload = await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise BuffaloError(f"{method} could not read a NAS response") from err

        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                try:
                    code = int(error.get("code"))
                except (TypeError, ValueError):
                    pass
                else:
                    # Firmware uses a null ID on session errors.
                    if payload.get("id") in (request_id, None):
                        raise BuffaloRpcError(method, code)
            elif payload.get("id") == request_id and "result" in payload:
                return payload["result"]
        raise BuffaloError(f"{method} returned an invalid JSON-RPC response")

    async def login(self, expired_sid: str | None = None) -> str:
        """Open one session even if multiple in-flight calls encounter expiry."""
        async with self._login_lock:
            if self._closed:
                raise BuffaloError("NAS client is closed")
            if self._sid and self._sid != expired_sid:
                return self._sid
            self._sid = None
            try:
                result = await self._rpc(
                    "Auth.login",
                    {"username": self._username, "password": self._password},
                )
            except BuffaloRpcError as err:
                if err.code in {-110, -118, SESSION_EXPIRED, 401, 403}:
                    raise BuffaloAuthError("NAS login was rejected") from err
                raise
            if not isinstance(result, dict):
                raise BuffaloError("NAS login returned an invalid response")
            if not isinstance(sid := result.get("sid"), str) or not sid:
                raise BuffaloAuthError("NAS login returned no session ID")
            self._sid = sid
            return sid

    async def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        """Call an authenticated read method and retry an expired session once."""
        sid = await self.login()
        try:
            return await self._rpc(method, {**(params or {}), "sid": sid})
        except BuffaloRpcError as err:
            if err.code not in {SESSION_EXPIRED, 401}:
                raise
        sid = await self.login(expired_sid=sid)
        try:
            return await self._rpc(method, {**(params or {}), "sid": sid})
        except BuffaloRpcError as err:
            if err.code in {SESSION_EXPIRED, 401}:
                if self._sid == sid:
                    self._sid = None
                # A login just succeeded. Treat session churn as a polling failure.
                raise BuffaloError("NAS rejected a newly opened session") from err
            raise

    async def read(self, method: str, alias: str | None = None, **params: Any) -> Any:
        """Use the firmware registry spelling if the dashboard spelling fails."""
        if alias is None or method in self._method_aliases:
            return await self.call(self._method_aliases.get(method, method), params)
        try:
            return await self.call(method, params)
        except BuffaloRpcError as err:
            if err.code not in METHOD_UNSUPPORTED:
                raise
        result = await self.call(alias, params)
        self._method_aliases[method] = alias
        return result

    async def portal_info(self) -> dict[str, Any]:
        """Get device identity from the dashboard or its public counterpart."""
        try:
            result = await self.read("get_portal_info_authneed")
        except BuffaloRpcError as err:
            if err.code not in METHOD_UNSUPPORTED | {-118, 403}:
                raise
            result = await self._rpc("getportalinfo", {})
        if not isinstance(result, dict):
            raise BuffaloError("NAS returned invalid device information")
        return result

    async def logout(self) -> None:
        """Close this client's own session when it is no longer needed."""
        async with self._login_lock:
            self._closed = True
            sid, self._sid = self._sid, None
            if sid and not self._session.closed:
                try:
                    await self._rpc("Auth.logout", {"sid": sid})
                except BuffaloError:
                    pass
