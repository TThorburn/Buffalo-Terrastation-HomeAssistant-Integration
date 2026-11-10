# Buffalo TeraStation Web API

The NAS inspected was a TS3410D running firmware 5.00-0.07. It reported JSON-RPC API version 1.0.0. The web interface sends JSON-RPC 2.0 requests by POST to `/nasapi/`. Authenticated calls put the session ID in `params.sid`. Expired or missing sessions return error `-119` and may return a null request ID. The browser sends `Auth.login` with `username` and `password`. Its persistent-login option adds `timeout: "0"`. The integration uses the firmware's default session lifetime.

## Monitoring methods

| Method | Role and evidence |
| --- | --- |
| `getapiversion` | Public call verified on the NAS. Returns `result.version`. |
| `getportalinfo` | Public call verified on the NAS. Its response includes hostname, product name, firmware fields, serial number, interfaces, and event lists. |
| `Auth.login`, `Auth.logout` | Session methods used by the browser and the integration. |
| `get_portal_info_authneed` | Authenticated device identity used by the dashboard. The integration can fall back to `getportalinfo`. |
| `device.getlist` | Dashboard storage source. `result.devices` contains disk and array records. The UI divides sizes by 1,048,576 to display its “GB” value. |
| `get_cpu_mem_info` | Dashboard CPU and memory source. The integration reads `cpu_usage_rate` and `mem_usage_rate`. |
| `network.list_interface_settings` | Dashboard network source. Each `result.interfaces` record has a `name` and can include cumulative `sent_bytes` and `recevied_bytes`. The dashboard derives traffic rates from differences between successive samples. The integration also accepts the spelling `received_bytes`. |
| `get_errors`, `get_informations` | The dashboard uses the result arrays directly for system errors and information events. |

The browser showed live CPU and memory, four drives in RAID 6, LAN 2 traffic and no current events. Separate requests without a SID verified the public calls and the `-119` response for protected calls. Protected response fields come from the firmware UI code and the previous integration. The static lists below include administration calls and feature-dependent entries. Individual support varies by model and firmware.

## Firmware registry

The following methods are declared in `/js/staticData/api.json`. The SID column records the registry's requirement.

| Method | SID required |
| --- | --- |
| `afp.detail` | Yes |
| `afp.edit` | Yes |
| `amazons3.detail` | Yes |
| `amazons3.edit` | Yes |
| `amazons3.remount` | Yes |
| `applysettings` | Yes |
| `auth.clearallsessions` | Yes |
| `auth.decryptdisk` | Yes |
| `auth.getuid` | Yes |
| `auth.login` | No |
| `auth.logout` | Yes |
| `auth.passcode` | Yes |
| `azure.change_task` | Yes |
| `azure.create_task` | Yes |
| `azure.delete_task` | Yes |
| `azure.edit_task` | Yes |
| `azure.list_tasks` | Yes |
| `backup.abortjob` | Yes |
| `backup.addoffsubnet` | Yes |
| `backup.count` | Yes |
| `backup.countsources` | Yes |
| `backup.counttargets` | Yes |
| `backup.createjob` | Yes |
| `backup.deletejob` | Yes |
| `backup.deleteoffsubnet` | Yes |
| `backup.detailjob` | Yes |
| `backup.editjob` | Yes |
| `backup.getfolderattribute` | Yes |
| `backup.getpassword` | Yes |
| `backup.listhosts` | Yes |
| `backup.listjobs` | Yes |
| `backup.listoffsubnet` | Yes |
| `backup.listsources` | Yes |
| `backup.listtargets` | Yes |
| `backup.setfolderattribute` | Yes |
| `backup.setpassword` | Yes |
| `backup.updatefolders` | Yes |
| `bittorrent.detail` | Yes |
| `bittorrent.edit` | Yes |
| `bittorrent.initsettings` | Yes |
| `bootauth.getSettings` | Yes |
| `bootauth.setSettings` | Yes |
| `btcloud.detailservice` | Yes |
| `btcloud.edit` | Yes |
| `btcloud.editservice` | Yes |
| `clear_information` | Yes |
| `cloudservice.CommonSettingDetail` | Yes |
| `cloudservice.CommonSettingEdit` | Yes |
| `cloudservice.ConnectControl` | Yes |
| `cloudservice.delete` | Yes |
| `cloudservice.detail` | Yes |
| `cloudservice.edit` | Yes |
| `cloudservice.list` | Yes |
| `cloudservice.log` | Yes |
| `cloudservice.remount` | Yes |
| `device.check` | Yes |
| `device.format` | Yes |
| `device.get_supported_type` | Yes |
| `device.getlist` | Yes |
| `device.remove` | Yes |
| `device.rescan` | Yes |
| `device.spare` | Yes |
| `device.usbdisk_rescan` | Yes |
| `dfs.addlink` | Yes |
| `dfs.deletelink` | Yes |
| `dfs.getconfig` | Yes |
| `dfs.listlinks` | Yes |
| `dfs.setconfig` | Yes |
| `directcopy.getconfig` | Yes |
| `directcopy.setconfig` | Yes |
| `display.getlcdsetting` | Yes |
| `display.getledsetting` | Yes |
| `display.setlcdsetting` | Yes |
| `display.setledsetting` | Yes |
| `dlna.detail` | Yes |
| `dlna.detailservice` | Yes |
| `dlna.dtcpinstalled` | Yes |
| `dlna.edit` | Yes |
| `dlna.editclients` | Yes |
| `dlna.editservice` | Yes |
| `dlna.initializedb` | Yes |
| `dlna.listclients` | Yes |
| `dlna.refreshdb` | Yes |
| `dlna.restart` | Yes |
| `dlna.updatedtcpip` | Yes |
| `drive.edit_storagespace_warning` | Yes |
| `drive.get_storagespace_warning` | Yes |
| `dropbox.create_task` | Yes |
| `dropbox.delete_task` | Yes |
| `dropbox.detail` | Yes |
| `dropbox.detail_proxy` | Yes |
| `dropbox.detail_task` | Yes |
| `dropbox.edit` | Yes |
| `dropbox.edit_proxy` | Yes |
| `dropbox.edit_task` | Yes |
| `dropbox.generate_token_key` | Yes |
| `dropbox.get_auth_url` | Yes |
| `dropbox.get_share_url` | Yes |
| `dropbox.list_folders` | Yes |
| `dropbox.list_tasks` | Yes |
| `dropbox.log` | Yes |
| `dropbox.remount` | Yes |
| `dropbox.test_connect` | Yes |
| `eyefi.detail` | Yes |
| `eyefi.edit` | Yes |
| `eyefi.listcards` | Yes |
| `eyefi.login` | Yes |
| `failover.accept` | Yes |
| `failover.backup_raise_to_main` | Yes |
| `failover.deny` | Yes |
| `failover.forcestop` | Yes |
| `failover.get_virtual_network_config` | Yes |
| `failover.getadvancedconfig` | Yes |
| `failover.getconfig` | Yes |
| `failover.getnetworkconfig` | Yes |
| `failover.gettarget` | Yes |
| `failover.set_virtual_network_config` | Yes |
| `failover.setadvancedconfig` | Yes |
| `failover.setnetworkconfig` | Yes |
| `failover.start` | Yes |
| `failover.startmaintenancemode` | Yes |
| `failover.stop` | Yes |
| `failover.stopmaintenancemode` | Yes |
| `flickr.detail` | Yes |
| `flickr.edit` | Yes |
| `flickr.logout` | Yes |
| `flickr.remount` | Yes |
| `ftp.detail` | Yes |
| `ftp.edit` | Yes |
| `get_cloud_status` | Yes |
| `get_portal_info_authneed` | Yes |
| `getapiversion` | No |
| `getcpumeminfo` | Yes |
| `getcpustatus` | No |
| `getdirtyflags` | Yes |
| `geterrors` | Yes |
| `getinformations` | Yes |
| `getnasfeature` | No |
| `getportalinfo` | No |
| `getservicestatus` | Yes |
| `group.count` | Yes |
| `group.create` | Yes |
| `group.delete` | Yes |
| `group.detail` | Yes |
| `group.edit` | Yes |
| `group.getaccessrestrictions` | Yes |
| `group.getlist` | Yes |
| `group.setaccessrestrictions` | Yes |
| `hostip.editlist` | Yes |
| `isconnectedinternet` | Yes |
| `iscsi.count` | Yes |
| `iscsi.create` | Yes |
| `iscsi.delete` | Yes |
| `iscsi.detail` | Yes |
| `iscsi.detailservice` | Yes |
| `iscsi.edit` | Yes |
| `iscsi.editservice` | Yes |
| `iscsi.getlist` | Yes |
| `iscsi.iscreatable` | Yes |
| `iscsi.log` | Yes |
| `itunes.detail` | Yes |
| `itunes.edit` | Yes |
| `job.detail` | Yes |
| `job.listjobs` | Yes |
| `listfolders` | Yes |
| `log.getconfig` | Yes |
| `log.setconfig` | Yes |
| `lvm.getlvlist` | Yes |
| `lvm.getvglist` | Yes |
| `lvm.lvchange` | Yes |
| `lvm.lvcreate` | Yes |
| `lvm.lvextend` | Yes |
| `lvm.lvremove` | Yes |
| `lvm.vgcreate` | Yes |
| `lvm.vgremove` | Yes |
| `mailnotification.detail` | Yes |
| `mailnotification.edit` | Yes |
| `mailnotification.report_detail` | Yes |
| `mailnotification.report_edit` | Yes |
| `mailnotification.sendtestmessage` | Yes |
| `mysql.getconfig` | Yes |
| `mysql.setconfig` | Yes |
| `nassetting.createinitializepasswdusb` | Yes |
| `nassetting.createinitializeusb` | Yes |
| `nassetting.restore` | Yes |
| `nassetting.save` | Yes |
| `network.aossconnect` | Yes |
| `network.createporttrunk` | Yes |
| `network.deleteporttrunks` | Yes |
| `network.editporttrunk` | Yes |
| `network.getauthsettings` | Yes |
| `network.getipsettings` | Yes |
| `network.isportavailable` | Yes |
| `network.listaccesspoints` | Yes |
| `network.listinterfacesettings` | Yes |
| `network.listporttrunks` | Yes |
| `network.listserviceports` | Yes |
| `network.ping` | Yes |
| `network.set_default_proxy` | Yes |
| `network.setauthsettings` | Yes |
| `network.setinterfacesettings` | Yes |
| `network.setipsettings` | Yes |
| `network.setserviceports` | Yes |
| `nfs.clientadd` | Yes |
| `nfs.clientdelete` | Yes |
| `nfs.clientdetail` | Yes |
| `nfs.folderdetail` | Yes |
| `nfs.folderedit` | Yes |
| `nfs.getconfig` | Yes |
| `nfs.setconfig` | Yes |
| `nop` | Yes |
| `onedrive.create_task` | Yes |
| `onedrive.delete_task` | Yes |
| `onedrive.edit_logsetting` | Yes |
| `onedrive.edit_task` | Yes |
| `printserver.deljob` | Yes |
| `proxy.get` | Yes |
| `raid.abortraidmodemaintenance` | Yes |
| `raid.create` | Yes |
| `raid.delete` | Yes |
| `raid.detailmisc` | Yes |
| `raid.detailraidmodemaintenance` | Yes |
| `raid.editmisc` | Yes |
| `raid.editraidmodemaintenance` | Yes |
| `raid.iscreatable` | Yes |
| `raid.rebuild` | Yes |
| `raid.rmm` | Yes |
| `replace.nas_cancel_replace` | Yes |
| `replace.nas_start_replace` | Yes |
| `replace.ts_cancel_replace` | Yes |
| `replace.ts_collect_folder_info` | Yes |
| `replace.ts_edit_settings` | Yes |
| `replace.ts_get_folder_info` | Yes |
| `replace.ts_get_settings` | Yes |
| `replace.ts_get_source_list` | Yes |
| `replace.ts_migrate_network_settings` | Yes |
| `replace.ts_migrate_ups_settings` | Yes |
| `replace.ts_set_source` | Yes |
| `replace.ts_start_datacopy` | Yes |
| `replace.ts_start_replace` | Yes |
| `replace.ts_stop_replace_mode` | Yes |
| `replication.check` | Yes |
| `replication.create` | Yes |
| `replication.createjob` | Yes |
| `replication.delete` | Yes |
| `replication.deletejob` | Yes |
| `replication.get_tasks` | Yes |
| `replication.listjobs` | Yes |
| `replication.resync` | Yes |
| `replication.resyncjob` | Yes |
| `servicecontrol` | Yes |
| `setflag` | Yes |
| `sftp.detail` | Yes |
| `sftp.edit` | Yes |
| `share.count` | Yes |
| `share.create` | Yes |
| `share.delete` | Yes |
| `share.detail` | Yes |
| `share.edit` | Yes |
| `share.emptyalltrashboxes` | Yes |
| `share.getlist` | Yes |
| `share.iscreatable` | Yes |
| `sleeptimer.detail` | Yes |
| `sleeptimer.edit` | Yes |
| `smb.detail` | Yes |
| `smb.detail_service` | Yes |
| `smb.edit` | Yes |
| `smb.edit_service` | Yes |
| `snmp.detail` | Yes |
| `snmp.edit` | Yes |
| `sound.detail` | Yes |
| `sound.edit` | Yes |
| `sound.findlocationdevice` | Yes |
| `squeezebox.clearcache` | Yes |
| `squeezebox.detail` | Yes |
| `squeezebox.edit` | Yes |
| `squeezebox.restart` | Yes |
| `sugarsync.detail` | Yes |
| `sugarsync.edit` | Yes |
| `sugarsync.remount` | Yes |
| `surveillance.detail` | Yes |
| `surveillance.edit` | Yes |
| `surveillance.initsettings` | Yes |
| `system.checkupdate` | Yes |
| `system.detailinitializebutton` | Yes |
| `system.detailmanager` | Yes |
| `system.detailnotifyupdate` | Yes |
| `system.detailplace` | Yes |
| `system.editinitializebutton` | Yes |
| `system.editmanager` | Yes |
| `system.editnotifyupdate` | Yes |
| `system.editplace` | Yes |
| `system.erasealldata` | Yes |
| `system.executerecoverysystem` | Yes |
| `system.getdatetime` | Yes |
| `system.gethostname` | Yes |
| `system.getlanguage` | Yes |
| `system.getrecoveryinto` | Yes |
| `system.initialize` | Yes |
| `system.installupdate` | Yes |
| `system.listlanguage` | Yes |
| `system.listtimezone` | Yes |
| `system.nasconfig_migrate` | Yes |
| `system.nasconfig_migrate_status` | Yes |
| `system.reboot` | Yes |
| `system.setdatetime` | Yes |
| `system.sethostname` | Yes |
| `system.setlanguage` | Yes |
| `system.shutdown` | Yes |
| `terasearch.detail` | Yes |
| `terasearch.edit` | Yes |
| `terasearch.getconfig` | Yes |
| `terasearch.setconfig` | Yes |
| `terasearch.update` | Yes |
| `timemachine.detail` | Yes |
| `timemachine.edit` | Yes |
| `TODO-0` | Yes |
| `TODO-2` | Yes |
| `ups.getconfig` | Yes |
| `ups.setconfig` | Yes |
| `user.convert` | Yes |
| `user.count` | Yes |
| `user.create` | Yes |
| `user.delete` | Yes |
| `user.detail` | Yes |
| `user.edit` | Yes |
| `user.getaccessrestrictions` | Yes |
| `user.getlist` | Yes |
| `user.setaccessrestrictions` | Yes |
| `virusscan.getconfig` | Yes |
| `virusscan.getfolderconfig` | Yes |
| `virusscan.init` | Yes |
| `virusscan.setconfig` | Yes |
| `virusscan.setfolderconfig` | Yes |
| `webaxs.detail` | Yes |
| `webaxs.detailservice` | Yes |
| `webaxs.easysetup` | Yes |
| `webaxs.edit` | Yes |
| `webaxs.editservice` | Yes |
| `webaxssync.detail` | Yes |
| `webaxssync.edit` | Yes |
| `webaxssync.remount` | Yes |
| `webserver.detailphp` | Yes |
| `webserver.editphp` | Yes |
| `webserver.getconfig` | Yes |
| `webserver.restorephp` | Yes |
| `webserver.setconfig` | Yes |
| `workingfolder.CommonSettingDetail` | Yes |
| `workingfolder.CommonSettingEdit` | Yes |
| `workingfolder.ConnectCreate` | Yes |
| `workingfolder.ConnectDelete` | Yes |
| `workingfolder.ConnectDetail` | Yes |
| `workingfolder.ConnectEdit` | Yes |
| `workingfolder.createJob` | Yes |
| `workingfolder.deleteJob` | Yes |
| `workingfolder.detailJob` | Yes |
| `workingfolder.editJob` | Yes |
| `workingfolder.listDrawers` | Yes |
| `workingfolder.listJobs` | Yes |
| `workingfolder.listSources` | Yes |
| `workingfolder.listTargets` | Yes |

## JavaScript method references

Literal method names found in the web interface scripts, including examples, inactive features and alternate spellings. This is a source inventory, so a reference does not establish that a method is available on the inspected unit.

```text
acl.clearFinishedJobs
acl.getFolderList
acl.getJobList
acl.killJob
acl.setACL
Afp.edit
amazons3.detail
amazons3.edit
amazons3.log
amazons3.remount
apply_settings
Auth.authPasscode
Auth.check_sid
auth.clear_all_sessions
Auth.clear_all_sessions
Auth.decryptDisk
auth.get_uid
Auth.get_uid
Auth.login
Auth.logout
azure.change_task
azure.check_account
azure.check_sync_container
azure.check_sync_folder
azure.create_task
azure.delete_task
azure.detail_proxy
azure.detail_task
azure.edit_proxy
azure.edit_task
azure.list_tasks
Backup.abortJob
backup.addOffsubnet
Backup.addOffsubnet
Backup.createJob
Backup.deleteJob
backup.deleteOffsubnet
Backup.deleteOffsubnet
backup.deregister_rsync_credential
backup.detailJob
Backup.detailJob
backup.edit_rsync_credential
Backup.editJob
backup.get_rsync_config
backup.get_rsync_credentials
Backup.getPassword
Backup.list_hosts
Backup.listJobs
Backup.listOffsubnet
Backup.listSources
Backup.listTargets
backup.register_rsync_credential
Backup.set_folder_attribute
backup.set_rsync_config
Backup.setPassword
backup.updateFolders
Backup.updateFolders
BitTorrent.detail
BitTorrent.edit
BitTorrent.initSettings
bootauth.check_condition
bootauth.get_config
bootauth.set_config
btcloud.detail_service
btcloud.edit
btcloud.edit_service
clear_information
cloudservice.CommonSettingDetail
cloudservice.CommonSettingEdit
cloudservice.delete
cloudservice.detail
cloudservice.edit
cloudservice.list
cloudservice.log
cloudservice.remount
crmm.check_connection
crmm.get_simple_operation
crmm.registkey
crmm.registkey_status
crmm.set_simple_operation
crmm.status
crmm.unregistkey
device.check
device.edit_storagespace_warning
device.format
device.get_list
device.get_storagespace_warning
device.get_supported_type
device.getlist
device.remove
device.rescan
device.spare
device.usbdisk_rescan
dfs.add_link
dfs.delete_link
dfs.get_config
dfs.list_links
dfs.set_config
directcopy.get_config
directcopy.set_config
display.get_lcd_setting
display.get_led_setting
display.set_lcd_setting
display.set_led_setting
dlna.detail_service
dlna.dtcp_installed
dlna.edit
dlna.edit_clients
dlna.edit_service
dlna.list_clients
dlna.refresh_db
dlna.restart
dlna.update_dtcpip
dropbox.create_task
dropbox.delete_task
dropbox.detail_proxy
dropbox.detail_task
dropbox.edit_proxy
dropbox.edit_task
dropbox.generate_token_key
dropbox.get_auth_url
dropbox.list_folders
dropbox.list_tasks
EyeFi.detail
EyeFi.edit
EyeFi.listCards
EyeFi.login
failover.accept
failover.backup_raise_to_main
failover.deny
failover.force_stop
failover.get_advanced_config
failover.get_config
failover.get_config_light
failover.get_resync_schedule
failover.get_tasks
failover.get_virtual_network_config
failover.set_advanced_config
failover.set_resync_schedule
failover.set_virtual_network_config
failover.start_maintenance_mode
Flickr.detail
Flickr.edit
Flickr.logout
Flickr.remount
Ftp.edit
get_cloud_status
get_cpu_mem_info
get_cpu_status
get_dirty_flags
get_errors
get_flag
get_flags
get_informations
get_nas_feature
get_portal_info
get_portal_info_authneed
get_service_status
getNasFeature
Group.count
Group.create
Group.delete
Group.detail
Group.edit
Group.get_access_restrictions
Group.getList
Group.set_access_restrictions
hostip.editlist
hostip.getlist
isconnected_internet
iscsi.create
iscsi.delete
iscsi.detail
iscsi.detail_service
iscsi.edit
iscsi.edit_service
iscsi.get_list
iscsi.getlist
iscsi.log
iscsi.update_tgpg_status
iTunes.detail
iTunes.edit
job.detail
Job.detail
Job.listJobs
list_folders
log.get_config
log.get_rotate_config
log.remove_rotated
log.set_config
log.set_rotate_config
lvm.get_lvlist
lvm.get_vglist
lvm.lvchange
lvm.lvcreate
lvm.lvextend
lvm.lvremove
lvm.vgcreate
lvm.vgremove
MailNotification.detail
MailNotification.edit
mailnotification.report_detail
mailnotification.report_edit
MailNotification.send_test_message
mysql.get_config
mysql.set_config
nassetting.createinitializepasswdusb
nassetting.createinitializeusb
nassetting.restore
nassetting.save
Network.get_ad_domain_info
network.get_default_proxy
network.get_ip_settings
Network.getAuthSettings
network.is_port_available
network.list_interface_settings
network.list_serviceports
network.listinterfacesettings
network.listInterfaceSettings
network.ping
network.set_default_proxy
network.set_interface_settings
network.set_ip_settings
network.set_serviceports
Network.setAuthSettings
nfs.acl_detail
nfs.acl_edit
nfs.client_add
nfs.client_delete
nfs.client_detail
nfs.folder_edit
nfs.get_config
nfs.set_config
onedrive.check_sync_container
onedrive.check_sync_folder
onedrive.create_task
onedrive.delete_task
onedrive.detail_proxy
onedrive.detail_task
onedrive.edit_common_setting
onedrive.edit_logsetting
onedrive.edit_proxy
onedrive.edit_task
onedrive.generate_token_key
onedrive.get_auth_url
onedrive.get_common_setting
onedrive.get_logsetting
onedrive.list_folders
onedrive.list_tasks
printserver.del_job
psu.get_config
psu.set_config
raid.abort_raidmode_maintenance
raid.create
raid.delete
raid.detail_misc
raid.detail_raidmode_maintenance
raid.edit_misc
raid.edit_raidmode_maintenance
raid.get_assemble_errors
raid.iscreatable
raid.rebuild
raid.resolve_assemble_errors
raid.rmm
replace.nas_cancel_replace
replace.nas_get_folder_list
replace.nas_kill_job
replace.nas_peek_estimation
replace.nas_set_source
replace.nas_start_estimation
replace.nas_start_replace
replace.nas_stop_replace_mode
replace.ts_cancel_replace
replace.ts_edit_settings
replace.ts_get_folder_list
replace.ts_get_settings
replace.ts_get_source_list
replace.ts_kill_job
replace.ts_migrate_network_settings
replace.ts_migrate_ups_settings
replace.ts_peek_estimation
replace.ts_set_source
replace.ts_start_datacopy
replace.ts_start_Estimation
replace.ts_start_replace
replace.ts_stop_replace_mode
replication.createJob
replication.deleteJob
replication.get_resync_schedule
replication.get_tasks
replication.listJobs
replication.resyncJob
Replication.resyncJob
replication.set_resync_schedule
service_control
set_flag
settings_manager.execute_settings_export
settings_manager.get_last_settings_edit_time
sftp.edit
Share.count
share.create
Share.create
share.delete
Share.delete
Share.detail
Share.edit
share.empty_all_trashboxes
share.get_list
Share.get_list
share.getlist
Share.getList
Share.has_freespace
simplewebserver.get_config
simplewebserver.get_server_config
simplewebserver.set_server_config
SleepTimer.detail
SleepTimer.edit
smart.get_disk
smb.detail
smb.detail_service
Smb.edit
smb.edit_service
snmp.detail
snmp.edit
sound.detail
sound.edit
sound.find_location_device
squeezebox.clear_cache
squeezebox.detail
squeezebox.edit
squeezebox.restart
ssd.detail_trim_maintenance
ssd.edit_trim_maintenance
surveillance.detail
surveillance.edit
System.checkUpdate
system.detail_initialize_button
system.detail_manager
system.detail_notify_update
system.detail_place
system.edit_initialize_button
system.edit_manager
system.edit_notify_update
system.edit_place
System.eraseAllData
System.execute_recovery_system
system.get_recovery_into
System.getDatetime
system.getHostname
System.getHostname
System.getLanguage
System.initialize
System.installUpdate
System.listLanguage
System.listTimezone
system.nasconfig_migrate
system.nasconfig_migrate_status
System.reboot
system.restore_db
System.setDatetime
system.setHostname
System.setHostname
System.setLanguage
System.shutdown
terasearch.edit
terasearch.get_config
terasearch.set_config
terasearch.update
TimeMachine.detail
TimeMachine.edit
ups.get_config
ups.set_config
user_.get_username
User.convert
user.count
User.count
User.create
User.delete
user.detail
User.detail
user.edit
User.edit
User.get_access_restrictions
user.get_list
user.getlist
User.getUidByName
User.set_access_restrictions
virusscan.get_config
virusscan.init
virusscan.repair
virusscan.set_config
virusscan.set_folder_config
webaxs.detail_service
webaxs.edit
webaxs.edit_service
WebAxsSync.detail
WebAxsSync.edit
WebAxsSync.remount
webserver.detail_php
webserver.edit_php
webserver.get_config
webserver.restore_php
webserver.set_config
workingfolder.CommonSettingDetail
workingfolder.CommonSettingEdit
workingfolder.ConnectCreate
workingfolder.ConnectDelete
workingfolder.ConnectEdit
workingfolder.createJob
workingfolder.deleteJob
workingfolder.detailJob
workingfolder.editJob
workingfolder.listDrawers
workingfolder.listJobs
workingfolder.listSources
workingfolder.listTargets
workingfolder.log
```

## HTTP file routes

The web interface also references query-string routes under `/nasapi` for file transfers. The values below come from the firmware scripts.

| `action` | `object` values |
| --- | --- |
| `download_html` | `html` |
| `download_log` | `azure`, `dropbox`, `onedrive`, `replication`, `rnspath`, `smb`, `system`, `tgz` |
| `upload` | `nasconfig_migrate_preparation`, `php_ini`, `private_key`, `server_certificate`, `user_csv` |

The cloud log links also include an `options` field with `azuretask`, `dropboxtask`, or `onedrivetask`. These routes are cataloged from source. The integration uses JSON-RPC for monitoring.
