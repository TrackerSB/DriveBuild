import setuptools
import os

with open(os.path.join(os.path.dirname(__file__), "README.md"), "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="drivebuild-client",
    version="0.41",
    author="Stefan Huber",
    author_email="huberst@fim.uni-passau.de",
    description="A client for accessing a DriveBuild MainApp.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=setuptools.find_packages(
        include=("drivebuildclient",)
    ),
    python_requires=">=3.6",
    install_requires=[
        "dill",
        "flask",
        "protobuf"
    ],
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    project_urls={
        "Source": "https://github.com/TrackerSB/DriveBuild"
    }
)
