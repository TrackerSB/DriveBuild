# MainApp
The variable `%REPO_HOME%` is a placeholders for the path to this repo.

## Install requirements
- Python3 (minimum version 3.6)

## Install
These install instructions use Linux, ZSH and VirtualEnv which is recommended.
1. `cd %REPO_HOME%/mainapp`
1. Create VirtualEnv (`python -m venv venv`)
1. Activate VirtualEnv (`source ./venv/bin/activate`)
1. Install dependencies (`pip install -r requirements.txt`)

## Config MainApp
1. `cd %REPO_HOME%/mainapp`
1. Edit `app.cfg`
1. Setup connection to DBMS
    - Specify DBMS host
    - Specify DBMS port
    - Specify DBMS database name
    - Specify DBMS username
    - Specify DBMS password

## Start MainApp
1. `cd %REPO_HOME%/mainapp`
1. Activate VirtualEnv (`source ./venv/bin/activate`)
1. Start Flask server (`flask run --host=0.0.0.0 --port=8383`)

