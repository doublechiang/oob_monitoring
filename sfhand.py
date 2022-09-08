#!/usr/bin/env python3

""" This program was re-wrote from sfhand bash script
"""

import os
import time

class Sfhand:
    def __init__(self):
        pass

    def requestSfUutConfig(self, mbsn):
        """ Write a $MBSN.txt """

        req_fn = f'{mbsn}.txt'
        with open(req_fn, 'w') as fp:
            fp.write(f'MBSN={mbsn}\n')
            fp.write(f'IP=0.0.0.0\n')
            fp.write('Request=UUTconfig2\n')

        self.__send_to_folder(req_fn, '/mnt/monitor/NetApp/Request')

    def __send_to_folder(self, fn, fpath):
        os.rename(fn)

    def __get_ConfigResponse(self, fn):
        
        if os.path.isfile(fn)
