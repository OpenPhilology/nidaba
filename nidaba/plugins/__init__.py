# -*- coding: utf-8 -*-
"""
nidaba.plugins
==============

"""

from __future__ import absolute_import, print_function

import os

from pluginbase import PluginBase
from nidaba.config import nidaba_cfg


plugin_base = PluginBase(package='nidaba.plugins')
plugin_source = plugin_base.make_plugin_source(searchpath=[os.path.dirname(__file__)])

with plugin_source:
    if 'plugins_load' in nidaba_cfg:
        plugin_list = [p['name'] for p in nidaba_cfg['plugins_load']]
    else:
        plugin_list = plugin_source.list_plugins()
    __import__('nidaba.plugins', globals(), locals(), plugin_list, -1)
