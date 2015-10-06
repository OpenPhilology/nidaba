# -*- coding: utf-8 -*-
#
# nidaba documentation build configuration file, created by
# sphinx-quickstart on Tue Nov  4 18:48:48 2014.

from subprocess import Popen, PIPE

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'celery.contrib.sphinx',
    'sphinxcontrib.httpdomain',
    'sphinxcontrib.autohttp.flask',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = u'nidaba'
copyright = u'2014-2015, Open Greek and Latin'

pipe = Popen('git describe --tags --always master', stdout=PIPE, shell=True)
version = pipe.stdout.read()
release = version

exclude_patterns = ['_build']

html_theme = 'alabaster'
html_static_path = ['_static']
htmlhelp_basename = 'nidabadoc'

html_theme_options = {
    'description': "An expandable and scalable OCR pipeline",
    'github_user': 'openphilology',
    'github_repo': 'nidaba',
    'travis_button': 'OpenPhilology/nidaba',
}


html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'searchbox.html',
        'donate.html',
    ]
}

pygments_style = 'sphinx'
latex_elements = {}
latex_documents = [('index', 'nidaba.tex', u'nidaba Documentation', u'Open\
                     Greek and Latin', 'manual')]
man_pages = [('index', 'nidaba', u'nidaba Documentation', [u'Open Greek and\
                                                            Latin'], 1)]
texinfo_documents = [('index', 'nidaba', u'nidaba Documentation', u'Open Greek\
                       and Latin', 'nidaba', 'Expandable and scalable OCR\
                       pipeline', 'Miscellaneous')]
