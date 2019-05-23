# Request types
struct PositionRequest {
}

struct SpeedRequest {
}

struct SteeringAngleRequest {
}

struct LidarRequest {
    # TODO Specify parameters
}

struct CameraRequest {
    # TODO Specify parameters
}

struct DamageRequest {
}

struct Request {
    1:optional PositionRequest position,
    2:optional SpeedRequest speed,
    3:optional SteeringAngleRequest steering_angle,
    4:optional LidarRequest lidar,
    5:optional list<CameraRequest> cameras,
    6:optional DamageRequest damage
}

# Request result types
struct PositionData {
    1:i32 x,
    2:i32 y
}

struct SpeedData {
    1:i32 speed
}

struct SteeringAngleData {
    1:i32 steering_angle
}

struct LidarData {
    # TODO Specify request result content
}

struct CameraData {
    1:list<list<list<i32>>> pixels
}

struct DamageData {
    1:bool is_damaged  # TODO Extend to detailed damage of certain parts?
}

struct Data {
    1:optional PositionData position,
    2:optional SpeedData speed,
    3:optional SteeringAngleData steering_angle,
    4:optional LidarData lidar,
    5:optional list<CameraData> cameras,
    6:optional DamageData damage
}

# Commands
struct AVCommand {
    1:i32 accelerate,  # TODO Negative accelerate is brake?
    2:i32 steer  # positive left, negative right
}

enum SimCommand {
    RESUME,
    FAIL,
    CANCEL
}

# The AIExchangeService
service AIExchangeService {
    void register_ai(1:string host_url, 2:string vehicle_id),
    void wait_for_simulator_request(),
    Data request_data(1:Request request),
    void control_av(1:AVCommand command),
    void control_simulator(1:SimCommand command, 2:string message)
}