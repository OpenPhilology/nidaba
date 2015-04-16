# -*- coding: utf-8 -*-
"""
nidaba.plugins
==============

"""

from __future__ import absolute_import, print_function

import os
import importlib

from functools import partial
from pluginbase import PluginBase

from nidaba.config import nidaba_cfg

# For easier usage calculate the path relative to here.

plugin_base = PluginBase(package='nidaba.plugins')
plugin_source = plugin_base.make_plugin_source(searchpath=[os.path.dirname(__file__)])

with plugin_source:
    __import__('nidaba.plugins', globals(), locals(), plugin_source.list_plugins(), -1)
