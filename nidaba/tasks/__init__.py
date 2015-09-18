# -*- coding: utf-8 -*-
"""
nidaba.tasks
============

The tasks package contains all built-in celery tasks used by nidaba. Tasks
should not contain any actual implementations but import them as separate
packages and just shim around them doing some initial setup, most commonly
conversion between storage module tuples and absolute paths.

Additional tasks depending on external or complex dependencies are contained in
plugins found in the plugins directory.
"""

from __future__ import unicode_literals, print_function, absolute_import

from nidaba.tasks import util
from nidaba.tasks import img
from nidaba.tasks import binarize
from nidaba.tasks import stats
from nidaba.tasks import postprocessing
from nidaba.tasks import output
