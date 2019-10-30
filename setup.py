#!/usr/bin/env python

from setuptools import setup

# Load module version from ovr/version.py
__version__ = "0.0.0"  # value will be replaced on the next line
exec(open("schmereo/version.py").read())

setup(
    name="schmereo",
    version=__version__,
    author="Christopher M. Bruns",
    author_email="cmbruns@rotatingpenguin.com",
    description="stereograph restoration application",
    url="https://github.com/cmbruns/schmereo",
    download_url="https://github.com/cmbruns/schmereo/tarball/" + __version__,
    packages=["schmereo"],
    scripts=["scripts/schmereo_app.py", "scripts/split_stereo.py"],
    keywords="stereograph stereoscopic 3D restoration",
    license="GPL",
    install_requires=["numpy", "pillow", "PyOpenGL", "PyQt5"],
    extras_require={},
)
