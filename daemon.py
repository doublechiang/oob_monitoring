# from isc_dhcp_leases import Lease, IscDhcpLeases
#!/usr/bin/evn python3
from iscdhcpleases import Lease, IscDhcpLeases
import time
import logging
import threading

import uut


if __name__ == '__main__':
    LEASE_FILE = '/var/lib/dhcpd/dhcpd.leases'
    leases = IscDhcpLeases(LEASE_FILE)
    base = leases.get_current()
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    while True:
        time.sleep(30)
        logger.debug("Checking if new lease")
        current = IscDhcpLeases(LEASE_FILE).get_current()
        for lease in current.keys():
            if lease not in base.keys():
                logger.debug("new lease found for {0}".format(lease))
                u = uut.Uut(current.get(lease))
                threading.Thread(target=u.startSol).start()

        base = current
