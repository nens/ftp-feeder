# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""
Sync configured datasets from one FTP server to another.

SYNC operations can be defined in a localsettings file. A number of factors
make this complicated.

- The source files may have no full timestamp.
- Missing timestamp are inferred from modification time.
- Only FTP LIST command is available to get modification times.
- Some datasets have enumerations in them.
- Some datasets have a significantly different naming.
- Some sources share a folder with other datasets.
- We retain only a partial history on the target FTP.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from datetime import datetime as Datetime
from datetime import timedelta as Timedelta
from ftplib import FTP
from os.path import basename, join

import argparse
import logging
import io

from ftp_feeder import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    filename=join(settings.LOG_DIR, 'sync.log'),
)
logger = logging.getLogger(__name__)


class Parser(object):
    """ Parse the results of the FTP LIST command. """
    def __init__(self):
        self.data = io.BytesIO()

    def __call__(self, data):
        """ Decode and split. """
        self.data.write(data)

    def __iter__(self):
        """ Return generator of (name, datetime) tuples. """
        lines = self.data.getvalue().decode('ascii').split('\r\n')[:-1]
        now = Datetime.now()
        for line in lines:
            # take it apart
            fields = line.split()
            name = fields[8]
            time = ' '.join(fields[5:8])

            if ':' in time:
                # Mmm dd hh:mm, within past 180 days
                datetime = Datetime.strptime(
                    time, '%b %d %H:%M',
                ).replace(year=now.year, minute=0)
                if datetime > now:
                    datetime = datetime.replace(year=datetime.year - 1)
            else:
                # Mmm dd yyyy, older than 180 days
                datetime = Datetime.strptime(time, '%b %d %Y')

            yield name, datetime


class Synchronizer(object):
    """ Keep the connections and synchronize per dataset. """
    def __init__(self):
        # connect
        self.source = FTP(**settings.SOURCE)
        self.target = FTP(**settings.TARGET)

    def synchronize(self, dataset):
        # determine sources
        source = dataset['source']
        self.source.cwd(source['dir'])
        parser = Parser()
        self.source.retrbinary('LIST', parser)

        # make a dict of available sources by date
        threshold = Datetime.now() - Timedelta(**dataset['keep'])
        work = []  # name, datetime tuples
        for name, datetime in parser:
            # skip ignored sources
            ignore = source.get('ignore')
            if ignore and ignore in name:
                continue
            # skip outdated sources
            if datetime < threshold:
                continue
            # use the parse item to use specific time attributes from filename
            replace_kwargs = {k: int(name[v])
                              for k, v in source['parse'].items()}
            work.append((name, datetime.replace(**replace_kwargs)))

        # make a dict of target: source names
        target = dataset['target']
        transfer = {}
        for name, datetime in work:
            # construct target name from template items
            parts = []
            for item in target['template']:
                if isinstance(item, slice):
                    parts.append(name[item])
                else:
                    parts.append(datetime.strftime(item))
            transfer[''.join(parts)] = name

        target_dir = target['dir']
        for target_path in self.target.nlst(target_dir):
            target_name = basename(target_path)

            # remove from transfer dictionary if it is already present
            if target_name in transfer:
                del transfer[target_name]

            # find old targets by name parsing and delete them
            datetime = Datetime.strptime(
                target_name[target['timestamp']], '%Y%m%d%H',
            )
            if datetime < threshold:
                logger.info('Remove %s', name)
                self.target.delete(join(target_dir, name))

        # transfer the rest
        for target_name, source_name in transfer.items():
            logger.info('Copy %s to %s', source_name, target_name)
            data = io.BytesIO()
            self.source.retrbinary('RETR ' + source_name, data.write)
            data.seek(0)
            target_path = join(target_dir, target_name)
            target_path_in = target_path + '.in'
            self.target.storbinary('STOR ' + target_path_in, data)
            self.target.rename(target_path_in, target_path)


def sync():
    synchronizer = Synchronizer()
    for dataset in settings.DATASETS:
        synchronizer.synchronize(dataset)


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(description=__doc__)
    return parser


def main():
    """ Call hillshade with args from parser. """
    # TODO logging
    kwargs = vars(get_parser().parse_args())
    try:
        sync(**kwargs)
    except:
        logger.exception('Error:')
