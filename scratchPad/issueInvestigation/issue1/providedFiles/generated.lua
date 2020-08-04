local M = {}
local sh = require('ge/extensions/scenario/scenariohelper')

local function onRaceStart()
    local modeFile = io.open('ego_movementMode', 'w')

    modeFile:write('MANUAL')

    modeFile:close()

    sh.setAiLine('ego', {line={{pos={1.0, 0.0, 0}}, {pos={56.0, 3.0, 0}}, {pos={56.0, 3.0, 0}}}, routeSpeed=13.88888888888889, routeSpeedMode='set'})

end

M.onRaceStart = onRaceStart
return M