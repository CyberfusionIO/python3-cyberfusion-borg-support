"""A setuptools based setup module."""

from setuptools import setup

setup(
    name="python-cyberfusion-borg-support",
    version="1.0",
    description="BorgSupport Python library/tools",
    author="William Edwards",
    author_email="wedwards@cyberfusion.nl",
    url="https://vcs.cyberfusion.nl/cyberfusion/python-cyberfusion-borg-support",
    license="Closed",
    packages=[
        "cyberfusion.BorgSupport",
    ],
    package_dir={"": "src"},
    platforms=["linux"],
    data_files=[],
)