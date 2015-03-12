# -*- coding: utf-8 -*-
"""
nidaba.tasks
==========

The tasks package contains all celery tasks used by nidaba. Tasks should not
contain any actual implementations but import them as separate packages and
just shim around them doing some initial setup, most commonly conversion
between storage module tuples and absolute paths.
"""

from __future__ import absolute_import

from nidaba.tasks import util
from nidaba.tasks import ocr
from nidaba.tasks import img
from nidaba.tasks import binarize
