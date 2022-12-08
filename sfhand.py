#!/usr/bin/env python3

""" This program was re-wrote from sfhand bash script
"""

import os
import time
import logging
import shutil

class Sfhand:
    SF_FOLDER='/WIN/NetApp/'
    REQ_FOLDER= SF_FOLDER + 'Request/'
    RES_FOLDER = SF_FOLDER + 'Response/'
    STS_FOLDER = SF_FOLDER + 'Status/'

    def __init__(self):
        pass

    def requestSfUutConfig(self, mbsn):
        """ Write a $MBSN.txt """

        qcisn = None
        error = ''
        req_fn = f'{mbsn}.txt'
        with open(req_fn, 'w') as fp:
            fp.write(f'MBSN={mbsn}\n')
            fp.write('Request=UUTconfig2\n')

        shutil.copyfile(req_fn, self.REQ_FOLDER + req_fn)
        os.system(f'rm -f {req_fn}')
        if self.__wait_for(self.RES_FOLDER + req_fn):
            qcisn=self.__parse_qcisn(self.RES_FOLDER + req_fn)
            
            if qcisn == None:
                error = 'QCISN not found in Response file\n'
                error += '-----------------------------------\n'
                with open(self.RES_FOLDER + req_fn, 'r') as response:
                    error += response.read()
                os.unlink(self.RES_FOLDER + req_fn)
        else:
            error = f'shopflow respone file {self.RES_FOLDER + req_fn} not found.'
        return qcisn, error

    def sendSfStatus(self, mbsn, msg):
        qcisn = None
        error = ''
        req_fn = f'{mbsn}.txt'
        with open(req_fn, 'w') as fp:
            fp.write(f'MBSN={mbsn}\n')
            fp.write(f'Station=FAT\n')
            fp.write(f'Status=FAT test FAIL, {msg}')

        shutil.copyfile(req_fn, self.STS_FOLDER + req_fn)
        return 
 
        

    def __wait_for(self, fn, timeout=100):
        timeout = time.time() + timeout
        while os.path.isfile(fn) is not True:
            time.sleep(5)
            if time.time() > timeout:
                return False
        return True

    def __parse_qcisn(self, fn):
        qcisn = None
        with open(fn, 'r') as fp:
            for line in fp.readlines():
                if 'QCISN=' in line:
                    qcisn = line.split('=')[1].strip()
                    break
        return qcisn

            

if __name__ == '__main__':
    sf=Sfhand()
    sf.sendSfStatus('B41222372021903A', 'retest=Y;FAT test FAIL, Ping BMC Management DHCP port FAIL===T6UB FAT test FAIL===')
