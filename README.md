# DriveBuild
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=code)](https://github.com/TrackerSB/DriveBuild)
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=blanks)](https://github.com/TrackerSB/DriveBuild)
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=files)](https://github.com/TrackerSB/DriveBuild)
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=lines)](https://github.com/TrackerSB/DriveBuild)
[![](https://tokei.rs/b1/github/TrackerSB/DriveBuild?category=comments)](https://github.com/TrackerSB/DriveBuild)

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
1. Create a database user (e.g. `drivebuild`)
1. Create a database (e.g. `drivebuild`)
1. Grant access rights to user `drivebuild` for database `drivebuild`
1. Apply database scheme (`tableScheme.sql`)

## Install
The instructions for installing the MainApp and SimNodes as well as for using the client can be found in the appropriate subdirectories.
All projects come with `requirements.txt` files which specify all dependencies.

