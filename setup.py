#!/usr/bin/env python

from setuptools import setup, find_packages

# Load module version from ovr/version.py
__version__ = "0.0.0"  # value will be replaced on the next line
exec(open("schmereo/version.py").read())

setup(
    name="schmereo",
    author="Christopher M. Bruns",
    author_email="cmbruns@rotatingpenguin.com",
    description="stereograph restoration application",
    download_url="https://github.com/cmbruns/schmereo/tarball/" + __version__,
    entry_points={"console_scripts": [
        "schmereo = schmereo.__main__:main"
    ]},
    keywords="stereograph stereoscopic 3D restoration",
    # TODO: "PyQt5" in install_requires makes the schmereo entry_point fail at runtime
    install_requires=["numpy", "pillow", "PyOpenGL", ],  # "PyQt5"],
    license="GPL",
    package_data={"": ["*.frag", "*.png", "*.ui", "*.vert"]},
    packages=find_packages(),
    scripts=["scripts/split_stereo.py"],
    url="https://github.com/cmbruns/schmereo",
    version=__version__,
)
