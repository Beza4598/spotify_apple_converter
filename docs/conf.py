from importlib.metadata import version as package_version

project = 'Spotify to Apple Music Converter'
copyright = '2023-2026, Beza Amsalu'
author = 'Beza Amsalu'
release = package_version('spotify-to-apple-py')
version = '.'.join(release.split('.')[:2])

extensions = ['myst_parser', 'sphinx.ext.autodoc', 'sphinx.ext.napoleon']
source_suffix = {'.rst': 'restructuredtext', '.md': 'markdown'}
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
autodoc_member_order = 'bysource'
myst_heading_anchors = 3

html_theme = 'sphinx_rtd_theme'
suppress_warnings = ['myst.header']
