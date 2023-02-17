# Design document

## Daemon
Scan the DHCP lease file for a new lease. When finding a new IP lease, probe that IP lease
with BMC default credential with "fru print" command. If that IP responds, then we know it's BMC, and we get the Chassis serial number. 

Start a new process to collect the OOB logs for 10 (TBD) minutes. 
After 10 minutes, save the logs, then drop the OOB logs. A Valid BMC response will have the Board serial number in the response text. Query the Shopflow with the Baseboard serial number. If get the Chassis Serial number, then save it with Chassis serial number [chassis_sn]_OOB_[datetime].txt . If can't get the the right response, then keep it with OOB log filename pattern [chassis_sn]_OOB_MBSN_[datetime].txt

## UUT Class

Provide the feature to collect OOB serial console log.