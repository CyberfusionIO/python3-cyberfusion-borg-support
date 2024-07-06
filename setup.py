"""A setuptools based setup module."""

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="python3-cyberfusion-borg-support",
    version="1.5.3.1",
    description="Library for Borg.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
    author="William Edwards",
    author_email="wedwards@cyberfusion.nl",
    url="https://github.com/CyberfusionIO/python3-cyberfusion-borg-support",
    platforms=["linux"],
    packages=[
        "cyberfusion.BorgSupport",
        "cyberfusion.BorgSupport.exceptions",
    ],
    data_files=[],
    package_dir={"": "src"},
    install_requires=["cached_property==1.5.2"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=["cyberfusion", "borg", "borgbackup"],
    license="MIT",
)
