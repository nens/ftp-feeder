ftp-feeder
==========

Scripts for syncing data to an FTP server from various sources. 

Development installation
------------------------

For development, you can use a docker-compose setup::

    $ docker-compose build --build-arg uid=`id -u` --build-arg gid=`id -g` lib
    $ docker-compose up --no-start
    $ docker-compose start
    $ docker-compose exec lib bash

(Re)create & activate a virtualenv::

    (docker)$ rm -rf .venv
    (docker)$ virtualenv .venv
    (docker)$ source .venv/bin/activate

Install dependencies & package and run tests::

    (docker)(virtualenv)$ pip install -r requirements.txt
    (docker)(virtualenv)$ pip install -e .[test]
    (docker)(virtualenv)$ pytest

Update requirements.txt::
    
    (docker)$ rm -rf .venv
    (docker)$ virtualenv .venv
    (docker)$ source .venv/bin/activate
    (docker)(virtualenv)$ pip install .
    (docker)(virtualenv)$ pip uninstall ftp-feeder --yes
    (docker)(virtualenv)$ pip freeze > requirements.txt


Server installation
-------------------

Global dependencies (apt)::

    git

Installation::

    $ sudo pip3 install --upgrade pip virtualenv
    $ virtualenv --system-site-packages .venv
    $ source .venv/bin/activate
    (virtualenv)$ pip install -r requirements.txt
    (virtualenv)$ pip install -e .


Staging server installation
---------------------------

On the staging server currently the target ftp role is performed by a local
vsftpd server, and a dedicated user. Its credentials are in the
localsettings.py on that server.


Configuration
-------------

Source and target FTP servers, as well as paths, templates and timestamps are
all configured in a localsettings.py file on the server. This may be symlinks
to the configuration defined in the private enens/rr-task repository.

Note that the sync script currently does not create directories, that has to be
done manually.

Synchronization is handled using cronjobs on the server, which can be found in
the private nens/rr-task repository.
