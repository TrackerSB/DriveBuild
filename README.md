# DriveBuild
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=code)](https://github.com/TrackerSB/DriveBuild)
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=blanks)](https://github.com/TrackerSB/DriveBuild)
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=files)](https://github.com/TrackerSB/DriveBuild)
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=lines)](https://github.com/TrackerSB/DriveBuild)
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=comments)](https://github.com/TrackerSB/DriveBuild)

[![](https://img.shields.io/badge/git--lfs-required-informational?logo=git)]()

![PyPI - Package](https://img.shields.io/badge/PyPI-drivebuild--client-informational?logo=pypi)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/drivebuild-client?logo=python)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/drivebuild-client)

## Directory structure
    ├── client - The DriveBuild client (which is also available as Python package)
    ├── examples - A simple example of a formalized test
    ├── levels - The custom BeamNG level
    ├── mainapp - The MainApp
    ├── simnode - The SimNode
    └── ai_stub - Basic scheme for AIs

## Setup DBMS
DriveBuild uses PostgreSQL.
1. Install PostgreSQL
1. Open psql command command line
1. Create a database (`CREATE DATABASE drivebuild;`)
1. Create a database user and grant access (`CREATE USER drivebuild WITH LOGIN SUPERUSER CREATEDB CREATEROLE INHERIT NOREPLICATION CONNECTION LIMIT -1 PASSWORD 'password';`)
1. Connect to the database (`\c drivebuild`)
1. Apply database scheme (`\i absolute/path/to/tableScheme.sql`)
1. Create DriveBuild user (`INSERT INTO users VALUES ('test', 'test');`)

## Install
The instructions for installing the MainApp and SimNodes as well as for using the client can be found in the appropriate subdirectories.
All projects come with `requirements.txt` files which specify all dependencies.

