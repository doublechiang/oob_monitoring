""" Setting file for the OOB config 
"""

LOG_FOLDER='/RACKLOG/OOB/'

PRODUCT_DURATIONS={
    # "Name" : "Time"
    "Default" : 60*15,
    # Due to S2290 will reboot 2 times and, it need 50 minutes to collect the log
    "S2290" : 60*50,
    "C2190" : 60*15,
    "C2192" : 60*15
}
