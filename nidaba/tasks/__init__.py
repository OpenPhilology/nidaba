# -*- coding: utf-8 -*-
"""
nibada.tasks
==========

The tasks package contains all celery tasks used by nibada. Tasks should not
contain any actual implementations but import them as separate packages and
just shim around them doing some initial setup, most commonly conversion
between storage module tuples and absolute paths.
"""

from __future__ import absolute_import

from nibada.tasks import util
from nibada.tasks import ocr
from nibada.tasks import img
from nibada.tasks import binarize
