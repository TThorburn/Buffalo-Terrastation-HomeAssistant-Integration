from __future__ import annotations
import time
import aiohttp
import async_timeout


class BuffaloNASClient:
    def __init__(self, host: str, username: str, password: str):
        self._base_url = f"https://{host}"
        self._username = username
        self._password = password
        self._sid: str | None = None

    async def _rpc(self, session, method, params):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": int(time.time()),
        }
        async with async_timeout.timeout(10):
            resp = await session.post(
                self._base_url + "/nasapi/",
                json=payload,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": self._base_url + "/login.html",
                },
                ssl=False,
            )
            resp.raise_for_status()
            return await resp.json()

    async def _ensure_sid(self, session):
        if self._sid:
            return self._sid

        resp = await self._rpc(
            session,
            "Auth.login",
            {
                "username": self._username,
                "password": self._password,
                "timeout": "0",
            },
        )
        self._sid = resp["result"]["sid"]
        return self._sid

    async def call(self, session, method, params=None):
        params = params or {}
        try:
            sid = await self._ensure_sid(session)
            params["sid"] = sid
            return await self._rpc(session, method, params)
        except Exception:
            self._sid = None
            sid = await self._ensure_sid(session)
            params["sid"] = sid
            return await self._rpc(session, method, params)