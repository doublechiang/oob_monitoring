# from isc_dhcp_leases import Lease, IscDhcpLeases
#!/usr/bin/evn python3
from iscdhcpleases import Lease, IscDhcpLeases
import time
import logging
import threading
import gc

import uut


if __name__ == '__main__':
    LEASE_FILE = '/var/lib/dhcpd/dhcpd.leases'
    LOG_FILE = '/var/log/oob_monitoring.log'
    # logging.basicConfig(filename=LOG_FILE, format='%(asctime)s - %(message)s', level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)
    leases = IscDhcpLeases(LEASE_FILE)
    base = leases.get_current()
    app_log_handler= logging.FileHandler(LOG_FILE)
    app_log_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', "%Y-%m-%d %H:%M:%S"))
    logger = logging.getLogger('app')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(app_log_handler)

    while True:
        time.sleep(60)
        gc.collect()
        logger.debug("Checking if new lease")
        current = IscDhcpLeases(LEASE_FILE).get_current()
        for lease in current.keys():
            if lease not in base.keys():
                logger.debug("new lease found for {0}".format(lease))
                u = uut.Uut(current.get(lease))
                threading.Thread(target=u.startSol).start()

        base = current
