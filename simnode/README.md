# SimNode
The variables `%REPO_HOME%` and `%BEAMNG_HOME%` are placeholders for the path to this repo and to BeamNG.

## Prepare BeamNG
1. Clone BeamNG.research-unlimited to `%BEAMNG_HOME%`
1. Modify BeamNG
    1. Add content of `%REPO_HOME%\simnode\scenariohelper_extension.lua` to `%BEAMNG_HOME%\trunk\lua\ge\extensions\scenario\scenariohelper.lua`
    1. Add line `M.setAiLine = setAiLine` to the end of edited file
    1. Go to `%BEAMNG_HOME\trunk\levels`
    1. Open CMD in this directory
    1. Execute `mklink /J drivebuild %REPO_HOME\levels\drivebuild`

## Install requirements
- Windows (since BeamNG is Windows-only)
- Python3 (minimum version 3.6)

## Install
These install instructions use PowerShell, WinPython and VirtualEnv which are recommended.
1. `cd %REPO_HOME%\simnode`
1. Create VirtualEnv (`python3 -m venv venv`)
1. Activate VirtualEnv (`.\venv\Scripts\Activate.ps1`)
1. Install dependencies
    1. Download a wheel file for shapely ([https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely](https://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely))
    1. Install Shapely (`pip install path\to\shapely.whl`)
    1. Install remaining dependencies (`pip install -r requirements.txt`)

## Config SimNode
1. `cd %REPO_HOME%\simnode`
1. Edit `config.py`
1. Setup connection to MainApp
    - Change MainApp host
    - Change MainApp port (Specify the **internal** DriveBuild port and **not** the micro service port)
1. Setup connection to DBMS
    - Specify DBMS host
    - Specify DBMS port
    - Specify DBMS database name
    - Specify DBMS username
    - Specify DBMS password
1. Setup BeamNG config
    - Specify BeamNG install folder like `%BEAMNG_HOME%\\trunk`
    - Specify user path directory for temporary generated BeamNG scenarios (This should be an empty folder which is not part of the repository)
1. Optionally specify timeout for simulations (default: 10 min)

## Start SimNode
1. `cd %REPO_HOME%\simnode`
1. Activate VirtualEnv (`.\venv\Scripts\Activate.ps1`)
1. Start SimNode (`python start.py`)

