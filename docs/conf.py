import os, re, sys, time, html

sys.path.insert(0, os.path.abspath('..'))

import hy; hy.I = type(hy.I)  # A trick to enable `hy:autoclass:: hy.I`

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autodoc',
    'sphinxcontrib.hydomain']

import warnings; import sphinx.deprecation as SD
for c in (SD.RemovedInSphinx60Warning, SD.RemovedInSphinx70Warning):
    warnings.filterwarnings('ignore', category = c)

project = 'Hy'
copyright = '%s the authors' % time.strftime('%Y')
version = '.'.join(hy.__version__.split('.')[:-1])
  # The short dotted version identifier
release = hy.__version__ + ('' if hy.nickname is None else f' ({hy.nickname})')
  # The full version identifier, including alpha, beta, and RC tags
html_title = f'Hy {release} manual'
  # Ultimately this will only appear on the page itself. The actual HTML title
  # will be simplified in post-processing.

hyrule_version = 'v0.7.0'

source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['_build', 'coreteam.rst']

html_theme = 'nature'
html_theme_options = dict(
    nosidebar = True,
    body_min_width = 0,
    body_max_width = 'none')
html_css_files = ['custom.css']
html_static_path = ['_static']
html_copy_source = False
html_show_sphinx = False

add_module_names = True
smartquotes = False
nitpicky = True

highlight_language = 'hylang'

intersphinx_mapping = dict(
    py = ('https://docs.python.org/3/', None),
    hyrule = (f'http://hylang.org/hyrule/doc/{hyrule_version}', None))
