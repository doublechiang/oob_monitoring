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

    def __init__(self):
        pass

    def requestSfUutConfig(self, mbsn):
        """ Write a $MBSN.txt """

        qcisn = None
        req_fn = f'{mbsn}.txt'
        with open(req_fn, 'w') as fp:
            fp.write(f'MBSN={mbsn}\n')
            fp.write(f'IP=0.0.0.0\n')
            fp.write('Request=UUTconfig2\n')

        shutil.copyfile(req_fn, self.REQ_FOLDER + req_fn)
        if self.__wait_for(self.RES_FOLDER + req_fn):
            qcisn=self.__parse_qcisn(self.RES_FOLDER + req_fn)
            os.unlink(self.RES_FOLDER + req_fn)
            os.unlink(req_fn)
        return qcisn
            
        

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
    qcisn=sf.requestSfUutConfig('B41222305059903A')
    print(qcisn)
