# -*- coding: utf-8 -*-
"""
iris.tasks
==========

The tasks package contains all celery tasks used by iris. Tasks should not
contain any actual implementations but import them as separate packages and
just shim around them doing some initial setup, most commonly conversion
between storage module tuples and absolute paths.
"""

from __future__ import absolute_import

from iris.tasks import util
from iris.tasks import ocr
from iris.tasks import img
from iris.tasks import binarize
