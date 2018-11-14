ftp-feeder
==========================================

Scripts for syncing data to an FTP server from various sources. 


Installation
------------

Install whatever isn't yet availble::

    $ sudo apt install python3-pip
    $ sudo pip3 install zc.buildout
    $ buildout

Configuration
-------------

::

    # Harmonie, Hirlam, Synops and KNMI_STN are synced to open KNMI data
    # m    h dom mon dow command
    44     * *   *   *   /srv/ftp-feeder/bin/sync  # synops is last written at about 38!
