# -*- coding: utf-8 -*-
#
# lewis documentation build configuration file, created by
# sphinx-quickstart on Wed Nov  9 16:42:53 2016.
import os

# -- General configuration ------------------------------------------------

needs_sphinx = '1.4.5'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

# General information about the project.
project = u'lewis'
copyright = u'2016-2017, European Spallation Source ERIC'
author = u'Michael Hart, Michael Wedel, Owen Arnold'

version = u'1.2'
release = u'1.2.0'

language = None

exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

pygments_style = 'sphinx'
todo_include_todos = False

modindex_common_prefix = ['lewis.']

# -- Options for HTML output ---------------------------------------------

# This is from the sphinx_rtd_theme documentation to make the page work with RTD
on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_logo = 'resources/logo/lewis-logo.png'
html_static_path = []
html_show_sourcelink = True
htmlhelp_basename = 'lewisdoc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    'papersize': 'a4paper',
}

latex_documents = [
    (master_doc, 'lewis.tex', u'lewis Documentation',
     u'Michael Hart, Michael Wedel, Owen Arnold', 'manual'),
]
