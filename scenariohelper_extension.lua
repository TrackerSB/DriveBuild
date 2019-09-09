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
    -- NOTE obj is nil
    -- if cling then
    --   z = obj:getSurfaceHeightBelow(pos:toFloat3())
    -- else
    --   z = n['pos'][3]
    -- end
    pos.z = z
    local fauxNode = {
      pos = pos,
      radius = 0,
      radiusOrig = 0,
    }
    table.insert(speedList, n['speed'])
    table.insert(fauxPath, fauxNode)
  end

  local arg = {
    script = fauxPath,
    wpSpeeds = speedList
  }

  queueLuaCommandByName(vehicleName, 'ai.driveUsingPath({script = '..serialize(fauxPath)..', wpSpeeds = '..serialize(speedList)..'})')
end