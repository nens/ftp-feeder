# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
""" Sync configured sources to FTP server. """

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from datetime import datetime as Datetime
from ftplib import FTP

import argparse

from ftp_feeder import settings


class Parser(object):
    """ Parse the results of the FTP LIST command. """
    def __call__(self, data):
        """ Decode and split. """
        self.lines = data.decode('ascii').split('\r\n')[:-1]

    def __iter__(self):
        """ Return generator of (name, datetime) tuples. """
        utcnow = Datetime.utcnow()
        for line in self.lines:
            # take it apart
            fields = line.split()
            name = fields[8]
            time = ' '.join(fields[5:8])
            
            if ':' in time:
                # Mmm dd hh:mm, within past 180 days
                datetime = Datetime.strptime(
                    time, '%b %d %H:%M',
                ).replace(year=utcnow.year)
                if datetime < utcnow:
                    yield name, datetime
                else:
                    yield name, datetime.replace(now.year - 1)
            else:
                # Mmm dd yyyy, older than 180 days
                yield Datetime.strptime(time, '%b %d %Y')
        


def sync():
    for sync in settings.SYNCS:
        # source
        source = sync['source']
        with FTP(**source['connect']) as source_ftp:
            source_ftp.cwd(source['dir'])
            parser = Parser()
            source_ftp.retrbinary('LIST', parser)
            for name, datetime in parser:
                print(name, datetime)
            exit()

        # target
        target = sync['target']
        with FTP(**target['connect']) as target_ftp:
            target_ftp.cwd(target['dir'])


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(description=__doc__)
    return parser


def main():
    """ Call hillshade with args from parser. """
    # TODO logging
    kwargs = vars(get_parser().parse_args())
    sync(**kwargs)
