service AIExchangeService {
void registerAI(1:string hostUrl, 2:string vehicleID),
void waitForSimulatorRequest(),
void requestData()
}