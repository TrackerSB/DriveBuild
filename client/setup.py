import setuptools
import os

with open(os.path.join(os.path.dirname(__file__), "drivebuildclient/README.md"), "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="drivebuild-client",
    version="0.39",
    author="Stefan Huber",
    author_email="huberst@fim.uni-passau.de",
    description="A client for accessing a DriveBuild MainApp.",
    long_description=long_description,
    long_description_content_type="text/markdown",
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
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
