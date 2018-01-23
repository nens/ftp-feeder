# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
""" Sync configured sources to FTP server. """

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import argparse
import ftplib

from ftp_feeder import settings


def sync():
    print(settings.msg)


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(description=__doc__)
    return parser


def main():
    """ Call hillshade with args from parser. """
    # TODO logging
    kwargs = vars(get_parser().parse_args())
    sync(**kwargs)
