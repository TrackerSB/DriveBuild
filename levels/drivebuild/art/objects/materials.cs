singleton Material(german_road_signs_solid)
{
    mapTo = "german_road_signs_solid";
    doubleSided = "1";
    translucentBlendOp = "None";
    detailScale[0] = "2 2";
    materialTag0 = "beamng";
    useAnisotropic[0] = "1";
	annotation = "BUILDINGS";
   colorMap[0] = "/levels/drivebuild/art/objects/german_road_signs_solid_d.dds";
   pixelSpecular[0] = "1";
   vertColor[0] = "1";
};

singleton Material(trafficlight)
{
    mapTo = "trafficlight";
    diffuseMap[0] = "levels/drivebuild/art/objects/traffic_cycle.png";
    specularPower[0] = "32";
    pixelSpecular[0] = "1";
    diffuseColor[0] = "1 1 1 1";
    useAnisotropic[0] = "1";
    castShadows = "0";
    translucent = "0";
    emissive[0] = "1";
    glow[0] = "1";
    translucentBlendOp = "None";
    alphaTest = "0";
    alphaRef = "0";
    animFlags[0] = "0x00000010";
    sequenceFramePerSec[0] = "10";
    sequenceSegmentSize[0] = "0.0014";
    materialTag0 = "beamng"; materialTag1 = "vehicle";
    annotation = "TRAFFIC_SIGNALS";
};
