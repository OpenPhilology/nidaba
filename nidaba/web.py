# -*- coding: utf-8 -*-
"""
nidaba.web
~~~~~~~~~~

A web interface for the REST API. 

For a documentation of the interface see the :ref:`API docs <api>`.
"""

from __future__ import unicode_literals, print_function, absolute_import

import logging

from flask import Blueprint, render_template

log = logging.getLogger(__name__)
log.propagate = False
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(process)d] [%(levelname)s] %(message)s', 
                              datefmt='[%Y-%m-%d %H:%M:%S %z]')
ch.setFormatter(formatter)
log.addHandler(ch)

web = Blueprint('web', __name__, template_folder='templates')

def get_blueprint():
    return web

@web.route('/', defaults={'path': ''})
@web.route('/<path:path>')
def indexRoute(path):
    log.debug('Routing to index')
    return render_template('index.html')
