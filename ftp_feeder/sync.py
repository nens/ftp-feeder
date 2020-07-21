# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
# -*- coding: utf-8 -*-
"""Sync configured datasets from the dataplatform API to an FTP server.
"""

from datetime import datetime as Datetime
from datetime import timedelta as Timedelta
from ftplib import FTP
from os.path import basename, join

import argparse
import logging
import io

import requests

from ftp_feeder import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    filename=join(settings.LOG_DIR, 'sync.log'),
)
logger = logging.getLogger(__name__)


class Dataset:
    URL = (
        "https://api.dataplatform.knmi.nl/open-data/"
        "datasets/{dataset}/versions/{version}/files/"
    )
    HEADERS = {"Authorization": settings.API_KEY}

    def __init__(self, dataset, version, step, pattern):
        """Represents a Dataplatform Dataset.

        Args:
            dataset (str): dataset name
            version (str): dataset version
        """
        self.url = self.URL.format(dataset=dataset, version=version)
        self.timedelta = Timedelta(**step)
        self.pattern = pattern

    def _verify(self, items, start_after_filename=""):
        """ Return verified items.

        This uses the files API to check if the items' files exist and have
        modificationDate after item's  datetime.
        """
        response = requests.get(
            self.url,
            headers=self.HEADERS,
            params={
                "maxKeys": len(items),
                "startAfterFilename": start_after_filename,
            }
        )

        # lookup dictionary for modification times
        last_modified = {}
        for record in response.json()["files"]:
            last_modified[record["filename"]] = record["lastModified"]

        # only items with modification date after product date are allowed
        verified = []
        for item in items:
            # note that "" will be smaller than any ISO datetime
            item_last_modified = last_modified.get(item["filename"], "")
            if item_last_modified > item["datetime"].isoformat():
                verified.append(item)

        return verified

    def latest(self, count=1):
        """Return list of (filename, datetime) tuples.

        Args:
            count (int): Number of files in the past to list.

        The result may be shorter then count because the API is actually used
        to check if the expected files are actually available.
        """
        # determine the timestamps where files are expected
        now = Datetime.utcnow()
        midnight = Datetime(now.year, now.month, now.day)
        step_of_day = ((now - midnight) // self.timedelta)
        dt_last = midnight + self.timedelta * step_of_day

        # note we generate one extra into the past for the
        # startAfterFilename parameter
        items = []
        for stepcount in range(-count, 1):
            datetime = dt_last + stepcount * self.timedelta
            filename = datetime.strftime(self.pattern)
            items.append({"filename": filename, "datetime": datetime})

        # make to lists for the verification
        start_after_filename = items[0]["filename"]
        from_start = []
        after_filename = []
        for item in items[1:]:
            if item["filename"] > start_after_filename:
                after_filename.append(item)
            else:
                from_start.append(item)

        # verify lists using API
        verified_from_start = self._verify(items=from_start)
        verified_after_filename = self._verify(
            items=after_filename, start_after_filename=start_after_filename,
        )
        return verified_after_filename + verified_from_start

    def _get_download_url(self, filename):
        """ Return temporary download url for filename.
        """
        response = requests.get(
            "{url}/{filename}/url".format(url=self.url, filename=filename),
            headers=self.HEADERS,
        )
        return response.json().get("temporaryDownloadUrl")

    def retrieve(self, filename):
        url = self._get_download_url(filename)
        return requests.get(url).content


class Synchronizer(object):
    """ Keep the connections and synchronize per dataset. """
    def __init__(self):
        self.target = FTP(**settings.TARGET)

    def synchronize(self, keep, source, target):
        # determine sources
        dataset = Dataset(**source)
        items = dataset.latest(Timedelta(**keep) // dataset.timedelta)
        transfer = {}
        for item in items:
            filename = item["filename"]
            transfer[item["datetime"].strftime(target["template"])] = filename

        # list and inspect target dir
        target_dir = target['dir']
        threshold = Datetime.utcnow() - Timedelta(**keep)
        for target_name_or_path in self.target.nlst(target_dir):
            # some servers return names, others return paths
            if target_name_or_path.startswith(target_dir):
                target_path = target_name_or_path
                target_name = basename(target_path)
            else:
                target_name = target_name_or_path
                target_path = join(target_dir, target_name)

            # remove from transfer dictionary if it is already present
            if target_name in transfer:
                del transfer[target_name]

            # find old targets by name parsing and delete them
            datetime = Datetime.strptime(
                target_name[target['timestamp']], '%Y%m%d%H',
            )
            if datetime < threshold:
                logger.info('Remove %s', target_name)
                self.target.delete(target_path)

        # transfer the rest
        for target_name, source_name in transfer.items():
            # read
            data = io.BytesIO(dataset.retrieve(source_name))
            logger.info('Retrieved %s', source_name)

            # write
            target_path = join(target_dir, target_name)
            target_path_in = target_path + '.in'
            self.target.storbinary('STOR ' + target_path_in, data)
            self.target.rename(target_path_in, target_path)
            logger.info('Stored %s', target_name)


def sync():
    synchronizer = Synchronizer()
    for dataset in settings.DATASETS:
        synchronizer.synchronize(**dataset)


def get_parser():
    """ Return argument parser. """
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    return parser


def main():
    """ Call hillshade with args from parser. """
    kwargs = vars(get_parser().parse_args())
    try:
        sync(**kwargs)
    except Exception:
        logger.exception('Error:')
