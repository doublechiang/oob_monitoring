#!/usr/bin/env python3
import subprocess
import logging
from subprocess import Popen
import os
import time



class Uut:

    def startSol(self):
        cmd = "ipmitool -H 10.16.1.149 -U root -P db9b3748e18a -I lanplus sol activate"
        # self.sol_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=None, shell=False)
        self.sol_proc = subprocess.Popen(cmd.split(), stdout=open('result.txt', 'wb'), stderr=None, shell=False)

    def stopSol(self):
        if self.sol_proc is not None:
            # cmd = "ipmitool -H 10.16.1.149 -U root -P db9b3748e18a -I lanplus sol deactivate"
            # os.system(cmd)
            self.sol_proc.terminate()
            self.sol_proc.wait()
            # with self.sol_proc.stdout:
            #     for line in iter(self.sol_proc.stdout.readline, b''):
            #         print(line,)
            # self.sol_proc.stdout.flush()
            # output, errs = self.sol_proc.communicate()
            # logging.error(f"errors:{errs}")
            # self.sol_proc.poll()
            # return output.decode('utf-8', 'ignore')

    def __getSn(self):
        pass

    def __init__(self, lease=None):
        self.sol_proc = None
        self.bmc_ip = None

        if lease is not None:
            vendor_str = lease.sets.get('vendor-string')
            if vendor_str is not None:
                if 'udhcp' in vendor_str:
                    self.lease = lease
                    



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    u = Uut()
    u.startSol()
    print('start the sol then sleep')
    time.sleep(90)
    print('sleep seconds finished')
    # out = u.stopSol()
    # with open('result.txt', 'w') as r:
    #     r.write(out)
    # print(out)
