"""A setuptools based setup module."""

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="python3-cyberfusion-borg-support",
    version="1.5.4",
    description="Library for Borg.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Cyberfusion",
    author_email="support@cyberfusion.io",
    url="https://github.com/CyberfusionIO/python3-cyberfusion-borg-support",
    platforms=["linux"],
    packages=[
        "cyberfusion.BorgSupport",
        "cyberfusion.BorgSupport.exceptions",
    ],
    data_files=[],
    package_dir={"": "src"},
    install_requires=["cached_property==1.5.2"],
)
