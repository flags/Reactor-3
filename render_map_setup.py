from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("render_map", ["render_map.pyx"])]

setup(
  name = 'Render Map',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)