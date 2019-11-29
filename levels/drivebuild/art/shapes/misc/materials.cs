singleton Material(road_rubber_sticky) {
    mapTo = "unmapped_mat";
    diffuseMap[0] = "road_asphalt_2lane_d.dds";
    doubleSided = "0";
    translucentBlendOp = "LerpAlpha";
    normalMap[0] = "road_asphalt_2lane_n.dds";
    specularPower[0] = "1";
    useAnisotropic[0] = "1";
    materialTag0 = "RoadAndPath";
    materialTag1 = "beamng";
    specularMap[0] = "road_asphalt_2lane_s.dds";
    reflectivityMap[0] = "road_rubber_sticky_d.dds";
    cubemap = "global_cubemap_metalblurred";
    translucent = "1";
    translucentZWrite = "1";
    alphaTest = "0";
    alphaRef = "255";
    castShadows = "0";
    specularStrength[0] = "0";
};

singleton Material(line_white) {
    mapTo = "unmapped_mat";
    doubleSided = "0";
    translucentBlendOp = "LerpAlpha";
    normalMap[0] = "line_white_n.dds";
    specularPower[0] = "1";
    useAnisotropic[0] = "1";
    materialTag0 = "RoadAndPath";
    materialTag1 = "beamng";
    translucent = "1";
    translucentZWrite = "1";
    alphaTest = "0";
    alphaRef = "255";
    castShadows = "0";
    specularStrength[0] = "0";
    colorMap[0] = "line_white_d.dds";
    annotation = "SOLID_LINE";
    specularStrength0 = "0";
    specularColor0 = "1 1 1 1";
};

singleton Material(line_dashed_short)
{
    mapTo = "unmapped_mat";
    diffuseMap[0] = "line_dashed_short_d.dds";
    doubleSided = "0";
    translucentBlendOp = "LerpAlpha";
    specularPower[0] = "1";
    useAnisotropic[0] = "1";
    materialTag0 = "RoadAndPath";
    materialTag1 = "beamng";
    translucent = "1";
    translucentZWrite = "1";
    alphaTest = "0";
    alphaRef = "255";
    castShadows = "0";
    specularStrength[0] = "0";
    annotation = "DASHED_LINE";
};

singleton Material(line_yellow) {
    mapTo = "unmapped_mat";
    doubleSided = "0";
    translucentBlendOp = "LerpAlpha";
    normalMap[0] = "line_white_n.dds";
    specularPower[0] = "1";
    useAnisotropic[0] = "1";
    materialTag0 = "RoadAndPath";
    materialTag1 = "beamng";
    translucent = "1";
    translucentZWrite = "1";
    alphaTest = "0";
    alphaRef = "255";
    castShadows = "0";
    specularStrength[0] = "0";
    annotation = "SOLID_LINE";
    colorMap[0] = "line_yellow_d.dds";
    specularStrength0 = "0";
};

singleton Material(line_yellow_double)
{
    mapTo = "unmapped_mat";
    diffuseMap[0] = "line_yellow_double_d.dds";
    normalMap[0] = "line_yellow_double_n.dds";
    specularMap[0] = "line_yellow_double_s.dds";
    doubleSided = "0";
    translucentBlendOp = "LerpAlpha";
    specularPower[0] = "1";
    useAnisotropic[0] = "1";
    materialTag0 = "RoadAndPath";
    materialTag1 = "beamng";
    translucent = "1";
    translucentZWrite = "1";
    alphaTest = "0";
    alphaRef = "255";
    castShadows = "0";
    specularStrength[0] = "0";
    annotation = "SOLID_LINE";
};
