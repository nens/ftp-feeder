# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
""" Sync configured sources to FTP server. """

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from ftplib import FTP
import argparse

from ftp_feeder import settings


def sync():
    for sync in settings.SYNCS:
        # source
        source = sync['source']
        with FTP(**source['connect']) as source_ftp:
            source_ftp.cwd(source['dir'])
            print(source_ftp.nlst())

        # target
        target = sync['target']
        with FTP(**target['connect']) as target_ftp:
            target_ftp.cwd(target['dir'])
            print(target_ftp.mlsd())


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(description=__doc__)
    return parser


def main():
    """ Call hillshade with args from parser. """
    # TODO logging
    kwargs = vars(get_parser().parse_args())
    sync(**kwargs)
