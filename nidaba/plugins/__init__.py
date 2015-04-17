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
sp = [os.path.dirname(__file__)]
if 'plugin_path' in nidaba_cfg:
    sp.extend(nidaba_cfg['plugin_path'])
plugin_source = plugin_base.make_plugin_source(searchpath=sp)

with plugin_source:
    if 'plugins_load' in nidaba_cfg:
        for plugin in nidaba_cfg['plugins_load']:
            pl = plugin_source.load_plugin(plugin)
            pl.setup(**nidaba_cfg['plugins_load'][plugin])
    else:
        __import__('nidaba.plugins', globals(), locals(), plugin_source.list_plugins(), -1)
