# -*- coding: utf-8 -*-
#
# nidaba documentation build configuration file, created by
# sphinx-quickstart on Tue Nov  4 18:48:48 2014.

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'toctree'

project = u'nidaba'
copyright = u'2014, Open Greek and Latin'

version = '0.1'
release = '0.1'

exclude_patterns = ['_build']

pygments_style = 'sphinx'
html_theme = 'default'
html_static_path = ['_static']
htmlhelp_basename = 'irisdoc'
latex_elements = {
}
latex_documents = [('index', 'nidaba.tex', u'nidaba Documentation', u'Open\
                     Greek and Latin', 'manual')]
man_pages = [('index', 'nidaba', u'nidaba Documentation', [u'Open Greek and\
                                                            Latin'], 1)]
texinfo_documents = [('index', 'nidaba', u'nidaba Documentation', u'Open Greek\
                       and Latin', 'nidaba', 'Expandable and scalable OCR\
                       pipeline', 'Miscellaneous')]
