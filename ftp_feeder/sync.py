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

import argparse

from ftp_feeder import settings


class Parser(object):
    """ Parse the results of the FTP LIST command. """
    def __call__(self, data):
        """ Decode and split. """
        self.lines = data.decode('ascii').split('\r\n')[:-1]

    def __iter__(self):
        """ Return generator of (name, datetime) tuples. """
        now = Datetime.now()
        for line in self.lines:
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

            yield datetime, name


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
        inserts = []
        for datetime, name in parser:
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
            inserts.append({
                'datetime': datetime.replace(**replace_kwargs),
                'source': name,
            })

        # make a dict of possible targets by date
        target = dataset['target']
        for insert in inserts:
            # construct target name from template items
            parts = []
            for item in target['template']:
                if isinstance(item, slice):
                    parts.append(name[item])
                else:
                    parts.append(datetime.strftime(item))
            insert['target'] = ''.join(parts)
            del insert['datetime']

        print(inserts)
        return

        self.target.cwd(target['dir'])
        # make similar dict for target (parse by template)
        # TODO
        # get nlst as set
        # drop inserts if name already there
        # parse names
        # populate delete list

        # implement atomic copier with a .in file and a rename operation
        # delete according to delete list
        # insert according to insert list


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
    sync(**kwargs)
