from distutils.core import setup

import py2exe

setup(windows=[{'script': 'reactor-3.py'}],
               options = {"py2exe": {"packages": ['alife']}})