# -*- coding: utf-8 -*-
#
# This file is execfile()d with the current directory set to its containing dir.

import os, sys, time
sys.path.append(os.path.abspath(".."))

from get_version import __version__ as hy_version
if hy_version.endswith(".dirty"):
    # Read the Docs might dirty its checkout, so ignore this.
    hy_version = hy_version[:-len(".dirty")]

templates_path = ['_templates']
source_suffix = '.rst'

master_doc = 'index'

# General information about the project.
project = u'hy'
copyright = u'%s the authors' % time.strftime('%Y')

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = ".".join(hy_version.split(".")[:-1])
# The full version, including alpha/beta/rc tags.
release = hy_version

exclude_patterns = ['_build', 'coreteam.rst']

pygments_style = 'sphinx'

import sphinx_rtd_theme
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_use_smartypants = False
html_show_sphinx = False
