# Design document

## Daemon
Scan the dhcpd lease file for new lease. When find a new lease, probe that lease
with BMC default credential with "fru print" command. If resposne, then we get 
Chassis serial number. 

Start a new process to collect the OOB logs for 10 minutes. 
After 10 minutes
Scan filesystem if RTP logs is generated. If generated, then drop the OOB logs.
If no RTP logs is found, then save the OOB logs with chassis SN pattern.
OOB log filename pattern [chassis_sn]_OOB_[datetime].txt

## UUT Class

Provide the feature to collect OOB serial console log.