from distutils.core import setup
import py2exe

setup(console=['reactor-3.py'], options = {"py2exe": {"packages": ['alife']}})