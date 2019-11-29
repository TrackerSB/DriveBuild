from http.client import HTTPResponse
from logging import getLogger
from pathlib import Path
from typing import Optional, List, Tuple

from drivebuildclient.aiExchangeMessages_pb2 import VehicleID, SimulationID, TestResult, SubmissionResult, User, \
    DataResponse, Void, \
    SimStateResponse, Control, DataRequest

_logger = getLogger("DriveBuild.Client.AIExchangeService")


class AIExchangeService:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    @staticmethod
    def _print_error(response: HTTPResponse) -> None:
        _logger.warning("Response status: " + str(response.status) + "\n"
                        + "Reason: " + response.reason + "\n"
                        + "Messsage:\n"
                        + str(b"\n".join(response.readlines())))

    def wait_for_simulator_request(self, sid: SimulationID, vid: VehicleID) -> SimStateResponse.SimState:
        """
        Waits for the simulation with ID sid to request the car with ID vid. This call blocks until the simulation
        requests the appropriate car in the given simulation.
        :param sid: The ID of the simulation the vehicle is included in.
        :param vid: The ID of the vehicle in the simulation to wait for.
        :return: The current state of the simulation at the point when the call to this function returns. The return
        value should be used to check whether the simulation is still running. Another vehicle or the even user may have
        stopped the simulation.
        """
        from drivebuildclient.httpUtil import do_get_request
        response = do_get_request(self.host, self.port, "/ai/waitForSimulatorRequest", {
            "sid": sid.SerializeToString(),
            "vid": vid.SerializeToString()
        })
        if response.status == 200:
            result = b"".join(response.readlines())
            sim_state = SimStateResponse()
            sim_state.ParseFromString(result)
            return sim_state.state
        else:
            AIExchangeService._print_error(response)

    def request_data(self, sid: SimulationID, vid: VehicleID, request: DataRequest) -> DataResponse:
        """
        Request data of a certain vehicle contained by a certain simulation.
        :param sid: The ID of the simulation the vehicle to request data about is part of.
        :param vid: The ID of the vehicle to get collected data from.
        :param request: The types of data to be requested about the given vehicle. A DataRequest object is build like
        the following:
        request = DataRequest()
        request.request_ids.extend(["id_1", "id_2",..., "id_n"])
        NOTE: You have to use extend(...)! An assignment like request.request_ids = [...] will not work due to the
        implementation of Googles protobuffer.
        :return: The data the simulation collected about the given vehicle. The way of accessing the data is dependant
        on the type of data you requested. To find out how to access the data properly you should set a break point and
        checkout the content of the returned value using a debugger.
        """
        from drivebuildclient.httpUtil import do_get_request
        response = do_get_request(self.host, self.port, "/ai/requestData", {
            "request": request.SerializeToString(),
            "sid": sid.SerializeToString(),
            "vid": vid.SerializeToString()
        })
        if response.status == 200:
            result = b"".join(response.readlines())
            data_response = DataResponse()
            data_response.ParseFromString(result)
            return data_response
        else:
            AIExchangeService._print_error(response)

    def control(self, sid: SimulationID, vid: VehicleID, commands: Control) -> Optional[Void]:
        """
        Control the simulation or a certain vehicle in the simulation.
        :param sid: The ID the simulation either to control or containing th vehicle to control.
        :param vid: The ID of the vehicle to possibly control.
        :param commands: The command either controlling a simulation or a vehicle in a simualtion. To define a command
        controlling a simulation you can use commands like:
        control = Control()
        control.simCommand.command = Control.SimCommand.Command.SUCCEED  # Force simulation to succeed
        control.simCommand.command = Control.SimCommand.Command.FAIL  # Force simulation to fail
        control.simCommand.command = Control.SimCommand.Command.CANCEL  # Force simulation to be cancelled/skipped
        For controlling a vehicle you have to define steering, acceleration and brake values:
        control = Control()
        control.avCommand.accelerate = <Acceleration intensity having a value between 0.0 and 1.0>
        control.avCommand.steer = <A steering value between -1.0 and 1.0 (Negative value steers left; a positive one
        steers right)>
        control.avCommand.brake = <Brake intensity having a value between 0.0 and 1.0>
        :return: A Void object possibly containing a info message.
        """
        from drivebuildclient.httpUtil import do_mixed_request
        response = do_mixed_request(self.host, self.port, "/ai/control", {
            "sid": sid.SerializeToString(),
            "vid": vid.SerializeToString()
        }, commands.SerializeToString())
        if response.status == 200:
            void = Void()
            void.ParseFromString(b"".join(response.readlines()))
            return void
        else:
            AIExchangeService._print_error(response)

    def control_sim(self, sid: SimulationID, result: TestResult) -> Optional[Void]:
        """
        Force a simulation to end having the given result.
        :param sid: The simulation to control.
        :param result: The test result to be set to the simulation.
        :return: A Void object possibly containing a info message.
        """
        from drivebuildclient.httpUtil import do_get_request
        response = do_get_request(self.host, self.port, "/sim/stop", {
            "sid": sid.SerializeToString(),
            "result": result.SerializeToString()
        })
        if response.status == 200:
            void = Void()
            void.ParseFromString(b"".join(response.readlines()))
            return void
        else:
            AIExchangeService._print_error(response)

    def get_status(self, sid: SimulationID) -> str:
        """
        Check the status of the given simulation.
        :param sid: The simulation to get the status of.
        :return: A string representing the status of the simulation like RUNNING, FINISHED or ERRORED.
        """
        from drivebuildclient.httpUtil import do_get_request
        import dill as pickle
        response = do_get_request(self.host, self.port, "/stats/status", {
            "sid": sid.SerializeToString()
        })
        if response.status == 200:
            return pickle.loads(b"".join(response.readlines()))
        else:
            AIExchangeService._print_error(response)
            return "Status could not be determined."

    def get_result(self, sid: SimulationID) -> str:
        """
        Get the test result of the given simulation. This call blocks until the test result of the simulation is known.
        :param sid: The simulation to get the test result of.
        :return: The current test result of the given simulation like SUCCEEDED, FAILED or CANCELLED.
        """
        from drivebuildclient.httpUtil import do_get_request
        import dill as pickle
        from time import sleep
        while True:  # Pseudo do-while-loop
            response = do_get_request(self.host, self.port, "/stats/result", {
                "sid": sid.SerializeToString()
            })
            if response.status == 200:
                result = pickle.loads(b"".join(response.readlines()))
                if result == "UNKNOWN":
                    sleep(1)
                else:
                    return result
            else:
                AIExchangeService._print_error(response)
                return "Result could not be determined."

    def get_trace(self, sid: SimulationID, vid: Optional[VehicleID] = None) -> List[Tuple[str, str, int, DataResponse]]:
        """
        Return all the collected data of a single or all participants in a simulation.
        :param sid: The simulation to request all the collected data from.
        :param vid: The vehicle whose collected data has to be returned. If None this method returns all the collected
        data.
        :return: The JSON serialized object representing all the collected data of a simulation or a participant in a
        simulation.
        """
        from drivebuildclient.httpUtil import do_get_request
        import dill as pickle
        args = {
            "sid": sid.SerializeToString()
        }
        if vid:
            args["vid"] = vid.SerializeToString()
        response = do_get_request(self.host, self.port, "/stats/trace", args)
        if response.status == 200:
            response_content = b"".join(response.readlines())
            trace_data = pickle.loads(response_content)
            trace = []
            for entry in trace_data:
                sid = SimulationID()
                sid.sid = str(entry[0])
                vid = VehicleID()
                vid.vid = entry[1]
                data = DataResponse()
                data.ParseFromString(entry[3])
                trace.append((sid, vid, entry[2], data))
            return trace
        else:
            AIExchangeService._print_error(response)
            return "The trace could not be retrieved."

    def get_running_tests(self, user: User) -> SubmissionResult.Submissions:
        """
        Return the currently running tests of the given user.
        :param user: The user to get a list of running simulation for.
        :return: The list of running simulations initiated by the given user.
        """
        from drivebuildclient.httpUtil import do_get_request
        response = do_get_request(self.host, self.port, "/stats/getRunningSids", {
            "user": user.SerializeToString()
        })
        if response.status == 200:
            submission_result = SubmissionResult()
            submission_result.ParseFromString(b"".join(response.readlines()))
            return submission_result.result
        else:
            AIExchangeService._print_error(response)

    def run_tests(self, username: str, password: str, *paths: Path) -> Optional[SubmissionResult.Submissions]:
        """
        Upload the sequence of given files to DriveBuild, execute them and get their associated simulation IDs.
        :param username: The username for login.
        :param password: The password for login.
        :param paths: The sequence of file paths of files or folders containing files to be uploaded.
        :return: A sequence containing simulation IDs for all *valid* test cases uploaded. Returns None iff the upload
        of tests failed or the tests could not be run. Returns an empty list of none of the given test cases was valid.
        """
        from drivebuildclient.httpUtil import do_mixed_request
        from tempfile import NamedTemporaryFile
        from zipfile import ZipFile
        from os import remove
        temp_file = NamedTemporaryFile(mode="w", suffix=".zip", delete=False)
        temp_file.close()

        with ZipFile(temp_file.name, "w") as write_zip_file:
            def _add_all_files(path: Path) -> None:
                if path.is_file():
                    write_zip_file.write(path.absolute(), path.name)
                elif path.is_dir():
                    for sub_path in path.iterdir():
                        _add_all_files(sub_path)
                elif not path.exists():
                    _logger.warning("Path \"" + str(path) + "\" does not exist.")
                else:
                    _logger.warning("Can not handle path \"" + str(path) + "\".")

            for p in paths:
                _add_all_files(p)
            if len(write_zip_file.filelist) < 2:
                _logger.error("runTests(...) requires at least two valid files.")
                return None
        user = User()
        user.username = username
        user.password = password
        with open(temp_file.name, "rb") as read_zip_file:
            response = do_mixed_request(self.host, self.port, "/runTests", {
                "user": user.SerializeToString()
            }, b"".join(read_zip_file.readlines()))
        remove(temp_file.name)
        submission_result = SubmissionResult()
        submission_result.ParseFromString(b"".join(response.readlines()))
        if response.status == 200:
            return submission_result.result
        else:
            _logger.error("Running tests errored:\n"
                          + submission_result.message.message)
            return None
