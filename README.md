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

