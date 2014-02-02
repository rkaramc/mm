from distutils.core import setup

setup(
    name='mm',
    version='1.0',
    namespace_packages = ['abc'],
    packages=['mm', 'mm.test'],
    test_suite='nose.collector',
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description=open('README.md').read(),
)
