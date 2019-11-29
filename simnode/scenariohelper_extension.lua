-- This function has to be integrated into the file %BeamNGHome%/lua/ge/extensions/scenario/scenariohelper.lua of BeamNG
-- Don't forget to add it to the module to make it visisble!
local function setAiLine(vehicleName, arg)
  local nodes = arg['line']
  local fauxPath = {}
  local cling = arg['cling'] or 'true'
  local z = 0
  local speedList = {}
  for idx, n in ipairs(nodes) do
    local pos = vec3(n['pos'][1], n['pos'][2], 10000)
    pos.z = z
    local fauxNode = {
      pos = pos,
      radius = 0,
      radiusOrig = 0,
    }
    table.insert(fauxPath, fauxNode)
  end

  local routeSpeed = arg['routeSpeed'] or 0
  local routeSpeedMode = arg['routeSpeedMode'] or 'off'

  queueLuaCommandByName(vehicleName, 'ai.driveUsingPath({script = '..serialize(fauxPath)..', routeSpeed = '..routeSpeed..', routeSpeedMode = "'..routeSpeedMode..'"})')
end

