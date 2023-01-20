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
            self.logger.debug(f'UUT is not initialized by a validated IP address')
            return

        logging.info(f'UUT OOB Logging starting on IP:{self.bmc_ip},MBSN:{self.mbsn}')
        fd, path = tempfile.mkstemp()

        # Setup logger using the tempfile
        handler= logging.FileHandler(path)
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', "%Y-%m-%d %H:%M:%S"))
        oob_logger = logging.getLogger(self.mbsn)
        oob_logger.setLevel(logging.INFO)
        oob_logger.addHandler(handler)

        log =f"start logging BMC IP:{self.bmc_ip}, MBSN:{self.mbsn}" 
        oob_logger.info(log)
        cmd = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} -I lanplus sol activate"
        self.sol_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=None, shell=False)
        current_time = time.time()
        sol_endtime = current_time  + 360  # Target to capture in seconds

        for line in iter(self.sol_proc.stdout.readline, b''):
            oob_logger.info(line.decode(errors='ignore').strip())
            if time.time() > sol_endtime:
                cmd = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} -I lanplus sol deactivate"
                os.system(cmd)
                logging.info(f"logging IP:{self.bmc_ip}, MBSN:{self.mbsn} stopped")
                break

        # Write the post code to end of file
        self.sol_proc.terminate()
        self.sol_proc.kill()

        cmd = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} raw 0x32 0x73 0x0"
        output = subprocess.run(cmd.split(), shell=False, stdout=subprocess.PIPE, text=True).stdout
        sep = '\n--------------------- POST code below ---------------------\n'
        oob_logger.info(cmd + sep + output.strip())
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")

        # We have MBSN, try to use sfhand to retrieve the CSN
        log_fn = f'OOB_LOG_MBSN_{self.mbsn}_{date_str}.log'
        if self.sfhand:
            csn, error = self.sfhand.requestSfUutConfig(self.mbsn)
            if csn:
                log_fn = f'OOB_LOG_{csn}_{date_str}.log'
            else:
                oob_logger.error(bytes(error, 'utf-8'))

        error = self.__parse_log(path)
        if error is not None:
            # send to SF status
            if self.sfhand:
                self.sfhand.sendSfStatus(self.mbsn, error)

        dest_path = settings.LOG_FOLDER + log_fn
        try:
            shutil.copyfile(path, dest_path)
            logging.info(f'OOB logger {dest_path} has been saved')
            os.unlink(path)
        except:
            logging.error(f'Unable to copy file to {dest_path}')


        self.sol_proc.stdout.close()
        del self.sol_proc
        return

    def __parse_log(self, path):
        with open(path, 'rb') as oobfp:
            contents = oobfp.read()

        error = None
        if b'No Media Present' in contents:
            error = 'No Media Present'
        if b'No Bootable Device Detected' in contents:
            error = 'No Bootable Device Detected'
        if b'Traceback' in contents:
            error = 'Diag program Crashed.'
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
        except Exception as e:
            logging.error(e)
            logging.error(f'OOB fru print command error, ip:{ip} is possbile not bound to a BMC or credential is wrong')


    def __init_uut_from_lease(self, lease):
        self.__init_uut_from_ipstr(lease.ip)

    def __init__(self, param=None):
        self.sol_proc = None
        self.bmc_ip = None
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
