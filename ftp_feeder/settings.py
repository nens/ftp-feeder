# -*- coding: utf-8 -*<F7>-
# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.rst.
"""
This is the global settings file. It imports from a localsettings.py, if it is
available.
"""
import pathlib

# directories
PACKAGE_DIR = pathlib.Path(__file__).parent.parent
LOG_DIR = PACKAGE_DIR / "var" / "log"

# make sure they exist - there must be a better way
LOG_DIR.mkdir(parents=True, exist_ok=True)

# import local settings
try:
    from .localsettings import *  # NOQA
except ImportError:
    pass
