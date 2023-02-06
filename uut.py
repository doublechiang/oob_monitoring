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
    PRODUCT_DURATION = settings.PRODUCT_DURATIONS

    def startSol(self):
        if self.bmc_ip is None:
            self.app_logger.debug('UUT is not initialized by a validated IP address')
            return

        self.app_logger.info(f'UUT OOB Logging starting on IP:{self.bmc_ip},MBSN:{self.mbsn}')
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

        #Time Duration based on Product Name ---------
        cmdForFruPrint = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} -I lanplus fru print"
        fruPrint  = (((subprocess.run(cmdForFruPrint.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=None, shell=False)).stdout.decode('utf-8')).split('\n'))
        fru = {}
        for line in fruPrint:
            data = line.split(':')
            try:
                fru[data[0].strip()] = data[1].strip()
            except Exception as e:
                self.app_logger.error(e)
        productName = fru['Product Name']
        if (productName in self.PRODUCT_DURATION):
            logging_durations_secs = self.PRODUCT_DURATION[productName]
        else:
            logging_durations_secs = self.PRODUCT_DURATION['Default'] 
        # print (logging_durations_secs)    
        
        self.sol_proc = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=None, shell=False)
  
        sol_endtime = time.time()  + logging_durations_secs  # Target to capture in seconds

#        if there is no output, stdout, this iter object will block call
#        for line in iter(self.sol_proc.stdout.readline, b''):
#            if line:
#                oob_logger.info(line.decode(errors='ignore').strip())
#            if time.time() > sol_endtime:
#                cmd = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} -I lanplus sol deactivate"
#                os.system(cmd)
#                self.sol_proc.kill()
#                outs,errs = self.sol_proc.communicate(b'~.', timeout=5)
#                self.sol_proc.stdout.close()
#                del self.sol_proc
#                break

        os.set_blocking(self.sol_proc.stdout.fileno(), False)           # set non block for readline
        while time.time() < sol_endtime:
            line = self.sol_proc.stdout.readline()
            if line:
                oob_logger.info(line.decode(errors='ignore').strip())
            time.sleep(0.1)

        cmd = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} -I lanplus sol deactivate"
        os.system(cmd)
        outs,errs = self.sol_proc.communicate(b'~.', timeout=5)
        self.sol_proc.stdout.close()
        del self.sol_proc

        self.app_logger.debug(f"deactivated sol logging IP:{self.bmc_ip}, MBSN:{self.mbsn}")

        # Write the post code to end of file
        cmd = f"ipmitool -H {self.bmc_ip} -U {self.USERNAME} -P {self.USERPASS} raw 0x32 0x73 0x0"
        output = subprocess.run(cmd.split(), shell=False, stdout=subprocess.PIPE).stdout.decode(errors='ignore')
        sep = '\n--------------------- POST code below ---------------------\n'
        oob_logger.info(cmd + sep + output.rstrip())
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")

        # We have MBSN, try to use sfhand to retrieve the CSN
        log_fn = f'OOB_LOG_MBSN_{self.mbsn}_{date_str}.log'
        if self.sfhand:
            # IP field is not required. Requested by ITE team since they suspect the missing IP field, can be removed without issue.
            csn, error = self.sfhand.requestSfUutConfig(MBSN=self.mbsn, IP='0.0.0.0')
            if csn:
                log_fn = f'OOB_LOG_{csn}_{date_str}.log'
            else:
                oob_logger.error(error)

        error = self.__parse_log(path)
        if error is not None:
            # send to SF status
            if self.sfhand:
                self.sfhand.sendSfStatus(self.mbsn, error)

        handler.flush()
        handler.close()

        dest_path = settings.LOG_FOLDER + log_fn
        try:
            shutil.copyfile(path, dest_path)
            self.app_logger.info(f'OOB logger {dest_path} has been saved')
            os.unlink(path)
        except:
            self.app_logger.error(f'Unable to copy OOB log file to {dest_path}')

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
                    self.app_logger.debug(f"fru print get board serial number: {self.mbsn}, IP:{self.bmc_ip}")
                    continue
                if 'Chassis Serial' in line:
                    self.csn = line.split(':')[1].strip()
                    continue
        except Exception as e:
            self.app_logger.error(e)
            self.app_logger.error(f'OOB fru print command error, ip:{ip} is possbile not bound to a BMC or credential is wrong')


    def __init_uut_from_lease(self, lease):
        self.__init_uut_from_ipstr(lease.ip)

    def __init__(self, param=None):
        self.sol_proc = None
        self.bmc_ip = None
        self.sfhand = Sfhand()
        self.app_logger = logging.getLogger('app')

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
    Uut.USERNAME = 'admin'
    Uut.USERPASS = 'admin'
    u = Uut('10.16.0.21')
    u.startSol()
    # out = u.stopSol()
    # with open('result.txt', 'w') as r:
    #     r.write(out)
    # print(out)
