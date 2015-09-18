# -*- coding: utf-8 -*-
"""
nidaba.plugins
==============

"""

from __future__ import unicode_literals, print_function, absolute_import

from nidaba.config import nidaba_cfg

import stevedore


def setup(ext, data):
    ext.plugin.setup(**data[ext.name])

mgr = stevedore.NamedExtensionManager(namespace='nidaba.plugins',
                                      names=nidaba_cfg['plugins_load'].keys(),
                                      propagate_map_exceptions=True)

# only initialize extensions if any are loaded
if mgr.extensions:
    mgr.map(setup, nidaba_cfg['plugins_load'])
