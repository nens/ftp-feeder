# -*- coding: utf-8 -*<F7>-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
This is the global settings file. It imports from a localsettings.py, if it is
available.
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

from os.path import dirname, join

# logging
LOG_DIR = join(dirname(dirname(__file__)), 'var', 'log')

# import local settings
try:
    from .localsettings import *  # NOQA
except ImportError:
    pass
