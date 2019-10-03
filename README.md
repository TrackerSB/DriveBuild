# SimNode
## Setup of a DriveBuild SimNode
### Prepare BeamNG
The variables `%REPO_HOME%` and `%BEAMNG_HOME%` are placeholders for the path to this repo and to BeamNG.
1. Clone BeamNG.research-unlimited
1. Modify BeamNG
    1. Add content of `%REPO_HOME%/code/drivebuild/scenariohelper_extension.lua` to `%BEAMNG_HOME%/trunk/lua/ge/extensions/scenario/scenariohelper.lua`
    1. Add line `M.setAiLine = setAiLine` to the end of edited file
    1. Go to `%BEAMNG_HOME/trunk/levels`
    1. Open CMD
    1. Execute `mklink /J drivebuild %REPO_HOME/code/levels/drivebuild`
### Modify BeamNGpy
BeamNGpy may have problems with concurrent calls to the same vehicle in a simulation, i.e. the same socket.
The following modification does avoid the bug or at least make it more unlikely.
1. Install BeamNGpy using pip
1. Modify beamngpycommon.py
    1. Add the import `from threading import Lock`
    1. Create a global lock `lock = Lock()`
    1. Go to the method `recv_msg(...)`
    1. Add `lock.acquire()` right after the imports
    1. Add `lock.release()` right before the call to `msgpack.unpackb(...)`
