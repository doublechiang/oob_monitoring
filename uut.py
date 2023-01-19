#!/usr/bin/env python3
import subprocess
import logging
from subprocess import Popen
import os
import time
import datetime
import tempfile
import shutil

from iscdhcpleases import Lease
from sfhand import Sfhand
import settings


class Uut:

    USERNAME = 'admin'
    USERPASS = 'admin'

    def startSol(self):
        if self.bmc_ip is None:
            self.logger.debug('UUT is not initialized by a validated IP address')
            return

        self.logger.info(f'UUT OOB Logging starting on IP:{self.bmc_ip},MBSN:{self.mbsn}')
        cmd = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} -I lanplus sol activate"
        # self.sol_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=None, shell=False)
        fd, path = tempfile.mkstemp()
        with open(path, 'wb') as tempfp:
            log =f"logging BMC IP:{self.bmc_ip}, MBSN:{self.mbsn}" 
            self.logger.debug(log)
            tempfp.write(bytes(f"Sol Starting: {log}\n", 'utf-8'))
            tempfp.flush()
            self.sol_proc = subprocess.Popen(cmd.split(), stdout=tempfp, stderr=None, shell=False)
            current_time = time.time()
            sol_endtime = current_time  + 60*20  # Target to capture 20 minutes.

            while time.time() < sol_endtime:
                time.sleep(10)

            # Write the post code to end of file
            cmd = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} -I lanplus sol deactivate"
            os.system(cmd)
            self.sol_proc.terminate()
            self.sol_proc.wait()
            self.logger.debug(f"logging IP:{self.bmc_ip}, MBSN:{self.mbsn} stopped")

            cmd = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} raw 0x32 0x73 0x0"
            output = subprocess.run(cmd.split(), shell=False, stdout=subprocess.PIPE).stdout
            tempfp.write(b'\n--------------------- POST code below ---------------------\n')
            tempfp.write(output)

            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")

            # We have MBSN, try to use sfhand to retrieve the CSN
            log_fn = f'OOB_LOG_MBSN_{self.mbsn}_{date_str}.log'
            if self.sfhand:
                csn, error = self.sfhand.requestSfUutConfig(MBSN=self.mbsn)
                if csn:
                    log_fn = f'OOB_LOG_{csn}_{date_str}.log'
                    self.logger.info(f'IP:{self.bmc_ip}, MBSN:{self.mbsn}, CSN:{csn}')
                else:
                    tempfp.write(bytes(error, 'utf-8'))
        error = self.__parse_log(path)
        if error is not None:
            # send to SF status
            if self.sfhand:
                self.sfhand.sendSfStatus(self.mbsn, error)

        dest_path = settings.LOG_FOLDER + log_fn
        try:
            shutil.copyfile(path, dest_path)
            self.logger.info(f'OOB logger {dest_path} has been saved')
            os.unlink(path)
        except:
            logging.error(f'Unable to copy file to {dest_path}')

        self.sol_proc.stdout.close()
        del self.sol_proc

        return

    def __parse_log(self, path):
        with open(path, 'r') as oobfp:
            contents = oobfp.read()

        error = None
        if 'No Media Present' in contents:
            error = 'FAIL, No Media Present'
        if 'No Bootable Device Detected' in contents:
            error = 'FAIL, No Bootable Device Detected'
        if 'Traceback' in contents:
            error = 'ERROR, Diag program Crashed.'
        if 'has no sf config' in contents:
            error = 'ERROR, Cannot get SF config'
        return error


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
    def __init_uut_from_ipstr(self, ip):
        cmd = f'ipmitool -H {ip} -U {self.USERNAME} -P {self.USERPASS} fru print'
        self.csn = None
        self.mbsn = None
        try:
            output = subprocess.run(cmd.split(), shell=False, stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()
            for line in output:
                if 'Board Serial' in line:
                    self.mbsn = line.split(':')[1].strip()
                    self.bmc_ip =  ip
                    self.logger.debug(f"fru print get board serial number: {self.mbsn}, IP:{self.bmc_ip}")
                    continue
                if 'Chassis Serial' in line:
                    self.csn = line.split(':')[1].strip()
                    continue
        except:
            self.logger.info(f'OOB fru print command error, ip:{ip} is possbile not bound to a BMC or credential is wrong')


    def __init_uut_from_lease(self, lease):
        self.__init_uut_from_ipstr(lease.ip)

    def __init__(self, param=None):
        self.sol_proc = None
        self.bmc_ip = None
        self.logger = logging.getLogger(__name__)
        self.sfhand = Sfhand()

        if isinstance(param, Lease):
            vendor_str = param.sets.get('vendor-string')
            if vendor_str is None:
                vendor_str=param.sets.get('vendor-class-identifier') 
            if vendor_str is not None:
                if 'udhcp' in vendor_str:
                    self.__init_uut_from_lease(param)
        if isinstance(param, str):
            self.__init_uut_from_ipstr(param)

                    



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    Uut.USERNAME = 'root'
    Uut.USERPASS = 'db9b3748e18a'
    u = Uut('10.16.1.149')
    u.startSol()
    # out = u.stopSol()
    # with open('result.txt', 'w') as r:
    #     r.write(out)
    # print(out)
