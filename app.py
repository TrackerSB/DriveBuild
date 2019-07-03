import copyreg
from threading import Thread
from typing import Dict, Optional

from flask import Flask, Response
from lxml.etree import _Element
from redis import StrictRedis

from aiExchangeMessages_pb2 import SimulationID, Control, TestResult
from db_handler import DBConnection
from dbtypes import SimulationData
from sim_controller import Simulation

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
redis_server = StrictRedis(host=app.config["REDIS_HOST"], port=app.config["REDIS_PORT"])
db_handler = DBConnection(app.config["DBMS_HOST"], app.config["DBMS_PORT"], app.config["DBMS_NAME"],
                          app.config["DBMS_USERNAME"], app.config["DBMS_PASSWORD"])


# Register pickler for _Element
def element_unpickler(data: bytes) -> _Element:
    from io import BytesIO
    from lxml.etree import parse
    return parse(BytesIO(data)).getroot()


def element_pickler(element: _Element):
    from lxml.etree import tostring
    return element_unpickler, (tostring(element),)


copyreg.pickle(_Element, element_pickler, element_unpickler)

_all_tasks: Dict[Simulation, SimulationData] = {}


# FIXME Any way to avoid these methods?
def _get_simulation(sid: SimulationID) -> Optional[Simulation]:
    global _all_tasks
    for sim, _ in _all_tasks.items():
        if sim.sid.sid == sid.sid:
            return sim
    return None


def _get_data(sid: SimulationID) -> Optional[SimulationData]:
    global _all_tasks
    for sim, data in _all_tasks.items():
        if sim.sid.sid == sid.sid:
            return data
    return None


# Setup routes for the app
@app.route("/runTests", methods=["POST"])
def test_launcher():
    from flask import request
    from tc_manager import run_tests
    from warnings import warn
    from aiExchangeMessages_pb2 import SimulationIDs
    global _all_tasks
    file_content = request.data
    new_tasks = run_tests(file_content)
    sids = SimulationIDs()
    for sim, data in new_tasks.items():
        if sim.sid.sid in [s.sid.sid for s in _all_tasks]:
            warn("The simulation ID " + sim.sid.sid + " already exists and is getting overwritten.")
            _all_tasks.pop(_get_simulation(sim.sid))
        sids.sids.append(sim.sid.sid)
        _all_tasks[sim] = data
    return Response(response=sids.SerializeToString(), status=200, mimetype="application/x-protobuf")


def is_simulation_running(sid: SimulationID) -> bool:
    return _get_data(sid).scenario.bng is not None


def _check_simulation_running(sid: SimulationID) -> Optional[Response]:
    if not is_simulation_running(sid):
        return Response(response="There is no running simulation with ID " + sid.sid, status=400)


@app.route("/sim/requestAiFor", methods=["GET"])
def request_ai_for():
    from httpUtil import process_get_request

    def do() -> Response:
        from communicator import sim_request_ai_for
        from httpUtil import extract_vid, extract_sid
        _, sid = extract_sid()
        response = _check_simulation_running(sid)
        if response is None:
            _, vid = extract_vid()
            sim_request_ai_for(sid, vid)
            return Response(response="AI showed up and got permission to request data.", status=200,
                            mimetype="text/plain")
        else:
            return response

    return process_get_request(["sid", "vid"], do)


# FIXME How to banish this?
@app.route("/sim/verify", methods=["GET"])
def verify():
    from httpUtil import process_get_request, extract_sid

    def do() -> Response:
        from aiExchangeMessages_pb2 import VerificationResult
        _, sid = extract_sid()
        response = _check_simulation_running(sid)
        if response is None:
            precondition, failure, success = _get_simulation(sid).verify()
            verification = VerificationResult()
            verification.precondition = precondition.name
            verification.failure = failure.name
            verification.success = success.name
            return Response(response=verification.SerializeToString(), status=200, mimetype="text/plain")
        else:
            return response

    return process_get_request(["sid"], do)


# FIXME How to banish this?
@app.route("/sim/pollSensors", methods=["GET"])
def poll_sensors():
    from httpUtil import process_get_request

    def do() -> Response:
        from httpUtil import extract_sid, extract_vid
        from aiExchangeMessages_pb2 import Void
        _, sid = extract_sid()
        response = _check_simulation_running(sid)
        if response is None:
            _, vid = extract_vid()
            bng_scenario = _get_data(sid).scenario
            vehicle = bng_scenario.get_vehicle(vid.vid)
            bng_instance = bng_scenario.bng
            bng_instance.poll_sensors(vehicle)
            void = Void()
            return Response(response=void.SerializeToString(), status=200, mimetype="application/x-protobuf")
        else:
            return response

    return process_get_request(["sid", "vid"], do)


# FIXME How to banish this?
@app.route("/sim/steps", methods=["GET"])
def steps():
    from httpUtil import process_get_request

    def do() -> Response:
        from httpUtil import extract_sid
        from flask import request
        from aiExchangeMessages_pb2 import Void
        _, sid = extract_sid()
        response = _check_simulation_running(sid)
        if response is None:
            num_steps = int(request.args["steps"])
            _get_data(sid).scenario.bng.step(num_steps)
            void = Void()
            return Response(response=void.SerializeToString(), status=200, mimetype="application/x-protobuf")
        else:
            return response

    return process_get_request(["sid", "steps"], do)


# FIXME How to banish this?
@app.route("/sim/vids", methods=["GET"])
def vids():
    from httpUtil import process_get_request

    def do() -> Response:
        from httpUtil import extract_sid
        from aiExchangeMessages_pb2 import VehicleIDs
        _, sid = extract_sid()
        response = _check_simulation_running(sid)
        if response is None:
            vids = VehicleIDs()
            vids.vids.extend([v.vid for v in _get_data(sid).scenario.vehicles])
            return Response(response=vids.SerializeToString(), status=200, mimetype="application/x-protobuf")
        else:
            return response

    return process_get_request(["sid"], do)


@app.route("/sim/stop", methods=["GET"])
def stop():
    from httpUtil import process_get_request

    def do() -> Response:
        from httpUtil import extract_sid
        from aiExchangeMessages_pb2 import Void
        from flask import request
        _, sid = extract_sid()
        response = _check_simulation_running(sid)
        if response is None:
            result = TestResult()
            result.ParseFromString(request.args["result"].encode())
            control_sim(_get_simulation(sid), result.result, False)
            void = Void()
            return Response(response=void.SerializeToString(), status=200, mimetype="application/x-protobuf")
        else:
            return response

    return process_get_request(["sid", "result"], do)


@app.route("/ai/waitForSimulatorRequest", methods=["GET"])
def wait_for_simulator_request():
    from httpUtil import process_get_request

    def do() -> Response:
        from communicator import ai_wait_for_simulator_request
        from aiExchangeMessages_pb2 import SimStateResponse
        from httpUtil import extract_vid, extract_sid
        _, sid = extract_sid()
        _, vid = extract_vid()
        ai_wait_for_simulator_request(sid, vid)
        response = SimStateResponse()
        scenario = _get_data(sid).scenario
        if scenario.bng is None:
            task = _get_data(sid).simulation_task
            if task.get_state() is TestResult.Result.SUCCEEDED \
                    or task.get_state() is TestResult.Result.FAILED:
                response.state = SimStateResponse.SimState.FINISHED
            elif task.get_state() is TestResult.Result.SKIPPED:
                response.state = SimStateResponse.SimState.CANCELED
            else:
                response.state = SimStateResponse.SimState.ERRORED  # FIXME Can this be assumed?
        else:
            response.state = SimStateResponse.SimState.RUNNING
        return Response(response=response.SerializeToString(), status=200, mimetype="application/x-protobuf")

    return process_get_request(["sid", "vid"], do)


@app.route("/ai/requestData", methods=["GET"])
def request_data():
    from httpUtil import process_get_request

    def do() -> Response:
        from flask import request
        from aiExchangeMessages_pb2 import DataRequest
        from communicator import ai_request_data
        from httpUtil import extract_vid, extract_sid
        _, sid = extract_sid()
        response = _check_simulation_running(sid)
        if response is None:
            data_request = DataRequest()
            data_request.ParseFromString(request.args["request"].encode())
            _, vid = extract_vid()
            data_response = ai_request_data(sid, vid, data_request)
            return Response(response=data_response.SerializeToString(), status=200, mimetype="application/x-protobuf")
        else:
            return response

    return process_get_request(["vid", "sid", "request"], do)


def control_sim(sim: Simulation, command: int, direct: bool) -> None:
    """
    Stops a simulation and sets its associated test result.
    :param sim: The simulation to stop.
    :param command: The command controlling the simulation or the test result of the simulation to set. (Its "type" is
    Union[Control.SimCommand.Command, TestResult.Result]).
    :param direct: True only if the given command represents a Control.SimCommand.Command controlling the simulation
    directly. False only if the given command represents a TestResult.Result to be associated with the given simulation.
    """
    from shutil import rmtree
    data = _get_data(sim.sid)
    task = data.simulation_task
    if direct:
        if command is Control.SimCommand.Command.SUCCEED:
            task.set_state(TestResult.Result.SUCCEEDED)
        elif command is Control.SimCommand.Command.FAIL:
            task.set_state(TestResult.Result.FAILED)
        elif command is Control.SimCommand.Command.CANCEL:
            task.set_state(TestResult.Result.SKIPPED)
        else:
            raise NotImplementedError("Handling of the SimCommand " + str(command) + " is not implemented, yet.")
    else:
        task.set_state(command)

    data.scenario.bng.close()
    db_handler.store_data(data)

    # Make sure there is no inference with following tests
    rmtree(sim.get_user_path(), ignore_errors=True)


@app.route("/ai/control", methods=["POST"])
def control():
    from httpUtil import process_mixed_request

    def do() -> Response:
        from flask import request
        from communicator import ai_control
        from httpUtil import extract_sid, extract_vid
        _, sid = extract_sid()
        response = _check_simulation_running(sid)
        if response is None:
            _, vid = extract_vid()
            control_msg = Control()
            control_msg.ParseFromString(request.data)
            void = ai_control(_get_simulation(sid), vid, control_msg)
            return Response(response=void.SerializeToString(), status=200, mimetype="application/x-protobuf")
        else:
            return response

    return process_mixed_request(["sid", "vid"], do)


@app.route("/stats/status", methods=["GET"])
def status():
    from httpUtil import process_get_request

    def do() -> Response:
        from flask import request
        from aiExchangeMessages_pb2 import SimulationID
        global _all_tasks
        serialized_sid = request.args.get("sid", default=None)
        if serialized_sid:
            sid = SimulationID()
            sid.ParseFromString(serialized_sid.encode())
            data = _get_data(sid)
            if data:
                return Response(response=data.simulation_task.state(), status=200, mimetype="text/plain")
            else:
                return Response(response="Simulation node with ID " + sid.sid + " not found",
                                status=400, mimetype="text/plain")
        else:
            if _all_tasks:
                def _to_str(sim: Simulation, data: SimulationData) -> str:
                    return "Simulation: " + sim.sid.sid + ": " + data.simulation_task.state()

                status_text = \
                    "<br />".join([_to_str(sim, data) for sim, data in _all_tasks.items()])
            else:
                status_text = "There were no test executions so far"
            return Response(response=status_text, status=200, mimetype="text/html")

    return process_get_request([], do)


def do_after_flask_started() -> None:
    from httpUtil import do_get_request
    from socket import socket, AF_INET, SOCK_DGRAM
    from redis import Redis

    def get_ip():
        s = socket(AF_INET, SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        except:  # TODO Find more precise exception
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def register_sim_node():
        from util import eprint
        from aiExchangeMessages_pb2 import SimNode
        from httpUtil import do_post_request
        sim_node = SimNode()
        sim_node.host = get_ip()
        sim_node.port = app.config["PORT"]
        response = do_post_request(app.config["MAIN_HOST"], app.config["MAIN_PORT"], "/sim/register",
                                   sim_node.SerializeToString())
        if response.status == 200:
            print("Registered this node at the main application.")
        else:
            eprint("Could not register this node at the main application.")
            exit(1)

    registered = False
    while not registered:
        # NOTE Which url does not matter
        check_response = do_get_request("localhost", app.config["PORT"], "/stats/status", {})
        if check_response.status == 200:
            with Redis().lock("register node lock"):
                if not registered:
                    register_sim_node()
                    registered = True
        else:
            print("This simulation node is not registered, yet.")
            print(check_response.status)
            print(check_response.reason)


# FIXME Check frequently whether the main application is still running
thread = Thread(target=do_after_flask_started)  # NOTE The main method is not called by PyCharm
thread.start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["PORT"])
