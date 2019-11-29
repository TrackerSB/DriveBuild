from collections import defaultdict
from logging import getLogger, basicConfig, INFO
from socket import socket
from threading import Lock
from typing import Dict, List, Optional, Tuple, Union

from drivebuildclient import static_vars
from drivebuildclient.aiExchangeMessages_pb2 import SimulationID, User, SubmissionResult
from drivebuildclient.db_handler import DBConnection
from flask import Flask, Response

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
_DBCONNECTION = DBConnection("dbms.infosun.fim.uni-passau.de", 5432, "huberst", "huberst", "GAUwV5w72YvviLmb")
_logger = getLogger("DriveBuild.MainApp")
basicConfig(format='%(asctime)s: %(levelname)s - %(message)s', level=INFO)

# FIXME Handle unregister, check alive,...
# snid --> (socket, sid --> (vid --> socket))
_connected_sim_nodes: Dict[str, Tuple[socket, Dict[str, Dict[str, socket]]]] = {}


def _find_sim_node(sid: SimulationID) -> Optional[str]:
    for snid, (_, sid_entries) in _connected_sim_nodes.items():
        for sid_keys in sid_entries.keys():
            if sid.sid in sid_keys:
                return snid
    return None


# Setup routes for the app
@app.route("/", methods=["GET", "POST"])
def test_launcher():
    from flask import render_template, request, flash, redirect
    from drivebuildclient.httpUtil import do_post_request
    input_field_name = "testInput"
    if request.method == "POST":
        # check if the post request has the file part
        if input_field_name not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files[input_field_name]
        # if user does not select file, browser also submit a empty part without filename
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        def allowed_file(filename):
            return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]

        if file and allowed_file(file.filename):
            zip_content = file.readlines()
            # Redirect to this application itself
            response = do_post_request("localhost", 5000, "/runTests", zip_content)
            if response.status == 200:
                return render_template("testMonitor.html")
            else:
                return Response(response="The test could not be submitted.", status=500, mimetype="text/plain")
    else:
        return render_template("test_launcher.html")


# Contains tuples of vehicles in simulations that requested a socket from a simulation node
_requested_vehicle_sockets: Dict[str, Tuple[str, str]] = {}  # snid --> (sid, vid)


# FIXME How to recover failures?
@static_vars(locks=defaultdict(lambda: Lock()), requestLock=Lock())
def _send_message_to_sim_node(snid: str, action: bytes, data: List[bytes], sid: Optional[str] = None,
                              vid: Optional[str] = None) -> Optional[bytes]:
    from drivebuildclient import send_request
    _remove_dead_sockets()
    if snid in _connected_sim_nodes:
        main_socket, sid_entries = _connected_sim_nodes[snid]
        if sid and vid:
            _send_message_to_sim_node.requestLock.acquire()
            if sid not in sid_entries.keys():
                sid_entries[sid] = {}
            if vid not in sid_entries[sid].keys():
                _requested_vehicle_sockets[snid] = (sid, vid)
                send_request(main_socket, b"requestSocket", [])
            try:
                while not _connected_sim_nodes[snid] \
                        or vid not in _connected_sim_nodes[snid][1][sid]:
                    pass  # Wait for additional socket to be registered
                sock = _connected_sim_nodes[snid][1][sid][vid]
            except KeyError as ex:
                _logger.exception("Sending a message to the SimNode failed.")
            _send_message_to_sim_node.requestLock.release()
        else:
            sock = main_socket
        lock = _send_message_to_sim_node.locks[sock]
        lock.acquire()
        result = send_request(sock, action, data)
        lock.release()
        return result
    else:
        return None


def _remove_dead_sockets() -> None:
    def _is_dead(sock: socket) -> bool:
        try:
            sock.send(b"")
            return False
        except (ConnectionResetError, BrokenPipeError):
            return True

    to_delete_snids = []
    to_delete_vids = []
    sim_node_keys = _connected_sim_nodes.keys()
    for snid in sim_node_keys:
        sock, sid_entries = _connected_sim_nodes[snid]
        if _is_dead(sock):
            to_delete_snids.append(snid)
        else:
            if sid_entries:
                for sid, vid_entries in sid_entries.items():
                    for vid, sock in vid_entries.items():
                        if _is_dead(sock):
                            to_delete_vids.append((snid, sid, vid))
    for snid, sid, vid in to_delete_vids:
        del _connected_sim_nodes[snid][1][sid][vid]
    for snid in to_delete_snids:
        del _connected_sim_nodes[snid]


def _login_correct(user: User) -> bool:
    args = {
        "username": user.username,
        "password": user.password
    }
    result = _DBCONNECTION.run_query("""
    SELECT 1
    FROM users
    WHERE username = :username AND password = :password
    """, args)
    return result and result.rowcount > 0


def _get_running_tests(serialized_user: bytes) -> Union[SubmissionResult.Submissions, Response]:
    submissions = SubmissionResult.Submissions()
    for snid, (sock, _) in _connected_sim_nodes.items():
        if snid:
            submission_result = SubmissionResult()
            try:
                running_tests_result = _send_message_to_sim_node(snid, b"runningTests", [serialized_user])
                if running_tests_result:
                    submission_result.ParseFromString(running_tests_result)
                    if submission_result.WhichOneof("may_submissions") == "message":
                        if submission_result.message.message != "No simulations running":
                            message = "Determination of running tests currently unavailable."
                            return Response(response=message, status=503, mimetype="text/plain")
                    else:
                        for test_name, sid in submission_result.result.submissions.items():
                            submissions.submissions[test_name].sid = sid.sid
                else:
                    _logger.warning("SimNode " + snid + " did not respond to runningTests request.")
            except OSError:
                message = "The connection to a simulation node broke. It may not run anymore."
                return Response(response=message, status=503, mimetype="text/plain")
        else:
            _logger.warning("Found a snid in _connected_sim_nodes that is None.")
    return submissions


@app.route("/runTests", methods=["POST"])
@static_vars(sim_instance_quota=2)
def run_tests():
    from drivebuildclient.httpUtil import process_mixed_request

    def do() -> Response:
        from flask import request
        _remove_dead_sockets()
        serialized_user = request.args["user"].encode()
        user = User()
        user.ParseFromString(serialized_user)
        submission_result = SubmissionResult()
        if _login_correct(user):
            submissions = _get_running_tests(serialized_user)
            if isinstance(submissions, SubmissionResult.Submissions):
                if len(submissions.submissions) < run_tests.sim_instance_quota:
                    selected_snid = None
                    for snid, (sock, sid_entries) in _connected_sim_nodes.items():
                        if selected_snid is None or len(sid_entries) < len(_connected_sim_nodes[selected_snid][1]):
                            selected_snid = snid
                    if selected_snid:
                        # FIXME Find appropriate timeout
                        response = _send_message_to_sim_node(
                            selected_snid, b"runTests", [request.data, serialized_user])
                        if response:
                            submission_result.ParseFromString(response)
                            if submission_result.HasField("result"):
                                for _, sid in submission_result.result.submissions.items():
                                    _connected_sim_nodes[selected_snid][1][sid.sid] = {}
                                status = 200
                            else:
                                status = 400
                        else:
                            submission_result.message.message = "Failed to run tests"
                            status = 500
                    else:
                        submission_result.message.message = "There is currently no simulation node registered."
                        status = 503
                else:
                    submission_result.message.message = "You´re not allowed to run more than " \
                                                        + str(run_tests.sim_instance_quota) \
                                                        + " instances simultaneously (Running simulations: " \
                                                        + ", ".join(submissions.submissions) + ")."
                    status = 429
            elif isinstance(submissions, Response):
                return submissions
            else:
                submission_result.message.message = "The tests the user is running could not be determined."
                status = 503
        else:
            submission_result.message.message = "Login or password is incorrect."
            status = 401
        return Response(response=submission_result.SerializeToString(), status=status,
                        mimetype="application/x-protobuf")

    return process_mixed_request(["user"], do)


@app.route("/sim/stop", methods=["GET"])
def stop():
    from drivebuildclient.httpUtil import process_get_request

    def do() -> Response:
        from drivebuildclient.httpUtil import extract_sid
        from flask import request
        serialized_sid, sid = extract_sid()
        snid = _find_sim_node(sid)
        if snid:
            serialized_result = request.args["result"].encode()
            response = _send_message_to_sim_node(snid, b"stop", [serialized_sid, serialized_result])
            return Response(response=response, status=200, mimetype="application/x-protobuf")
        else:
            return Response(response="Simulation node with ID " + sid.sid + " not found",
                            status=400, mimetype="text/plain")

    return process_get_request(["sid", "result"], do)


# FIXME There is much duplication concerning sid, vid, _find_sim_node, checking existence of a SimNode and redirecting


@app.route("/ai/waitForSimulatorRequest", methods=["GET"])
def wait_for_simulator_request():
    from drivebuildclient.httpUtil import process_get_request

    def do() -> Response:
        from drivebuildclient.httpUtil import extract_sid, extract_vid
        serialized_vid, vid = extract_vid()
        serialized_sid, sid = extract_sid()
        snid = _find_sim_node(sid)
        if snid:
            response = _send_message_to_sim_node(snid, b"waitForSimulatorRequest",
                                                 [serialized_sid, serialized_vid], sid.sid, vid.vid)
            return Response(response=response, status=200, mimetype="application/x-protobuf")
        else:
            return Response(response="Simulation node with hosting simulation with ID " + sid.sid + " not found",
                            status=400, mimetype="text/plain")

    return process_get_request(["sid", "vid"], do)


@app.route("/ai/requestData", methods=["GET"])
def request_data():
    from drivebuildclient.httpUtil import process_get_request

    def do() -> Response:
        from flask import request
        from drivebuildclient.httpUtil import extract_sid, extract_vid
        serialized_sid, sid = extract_sid()
        serialized_request = request.args["request"].encode()
        serialized_vid, vid = extract_vid()
        snid = _find_sim_node(sid)
        if snid:
            response = _send_message_to_sim_node(snid, b"requestData",
                                                 [serialized_sid, serialized_vid, serialized_request], sid.sid, vid.vid)
            return Response(response=response, status=200, mimetype="application/x-protobuf")
        else:
            return Response(response="Simulation node with ID " + sid.sid + " not found",
                            status=400, mimetype="text/plain")

    return process_get_request(["sid", "vid", "request"], do)


@app.route("/ai/control", methods=["POST"])
def control():
    from drivebuildclient.httpUtil import process_mixed_request

    def do() -> Response:
        from flask import request
        from drivebuildclient.httpUtil import extract_vid, extract_sid
        serialized_sid, sid = extract_sid()
        serialized_vid, vid = extract_vid()
        serialized_control = request.data
        snid = _find_sim_node(sid)
        if snid:
            response = _send_message_to_sim_node(snid, b"control", [serialized_sid, serialized_vid, serialized_control],
                                                 sid.sid, vid.vid)
            return Response(response=response, status=200, mimetype="application/x-protobuf")
        else:
            return Response(response="Simulation node with ID " + sid.sid + " not found",
                            status=400, mimetype="text/plain")

    return process_mixed_request(["sid", "vid"], do)


@app.route("/stats/getRunningSids", methods=["GET"])
def get_running_sids():
    from drivebuildclient.httpUtil import process_get_request

    def do() -> Response:
        from flask import request
        serialized_user = request.args["user"]
        submissions = _get_running_tests(serialized_user)
        if isinstance(submissions, Response):
            return submissions
        elif isinstance(submissions, SubmissionResult.Submissions):
            submission_result = SubmissionResult()
            submission_result.result.submissions.extend(submissions)
            return Response(response=submission_result.SerializeToString(), status=200,
                            mimetype="x-application/protobuf")
        else:
            return Response(response="getRunningSids can not handle " + str(type(submissions)) + ".",
                            status=501, mimetype="text/plain")

    return process_get_request(["user"], do)


@app.route("/stats/<action>", methods=["GET"])
def status(action: str):
    from drivebuildclient.httpUtil import process_get_request

    def do() -> Response:
        from drivebuildclient.httpUtil import extract_sid, extract_vid
        import dill as pickle
        _, sid = extract_sid()
        if sid:
            response = None
            if action == "result":
                args = {
                    "sid": sid.sid
                }
                query_result = _DBCONNECTION.run_query("""
                SELECT result
                FROM tests
                WHERE "sid" = :sid;
                """, args)
                result = query_result.fetchall()[0][0]
            elif action == "status":
                args = {
                    "sid": sid.sid
                }
                query_result = _DBCONNECTION.run_query("""
                SELECT status
                FROM tests
                WHERE "sid" = :sid;
                """, args)
                result = query_result.fetchall()[0][0]
            elif action == "trace":
                _, vid = extract_vid()
                if vid:
                    args = {
                        "sid": sid.sid,
                        "vid": vid.vid
                    }
                    query_result = _DBCONNECTION.run_query("""
                    SELECT *
                    FROM verificationcycles
                    WHERE "sid" = :sid AND "vid" = :vid;
                    """, args)
                else:
                    args = {
                        "sid": sid.sid
                    }
                    query_result = _DBCONNECTION.run_query("""
                    SELECT *
                    FROM verificationcycles
                    WHERE "sid" = :sid;
                    """, args)
                result = query_result.fetchall()
            else:
                response = Response(response="The action \"" + action + "\" is not implemented.", status=501,
                                    mimetype="text/plain")
                result = None
            if result:
                response = Response(response=pickle.dumps(result), status=200, mimetype="application/octet-stream")
            elif not response:
                response = Response(response="The action \"" + action + "\" returned no result.", status=444,
                                    mimetype="text/plain")
        else:
            response = Response(response="sid could not be extracted. Was it empty?", status=400, mimetype="text/plain")
        return response

    return process_get_request(["sid"], do)


@app.errorhandler(404)
def page_not_found(error):
    from flask import render_template
    return render_template("error404.html", error=error), 404


@app.errorhandler(500)
def page_not_found(error):
    from flask import render_template
    return render_template("error500.html", error=error), 500


@app.errorhandler(501)
def page_not_implemented(error):
    from flask import render_template
    return render_template("error501.html", error=error), 501


def _wait_for_sim_node_registers() -> None:
    from threading import Thread
    from drivebuildclient import static_vars, create_server, accept_at_server
    from drivebuildclient.aiExchangeMessages_pb2 import SimulationNodeID

    @static_vars(prefix="snid_", counter=0)
    def generate_snid() -> str:
        while True:
            snid = generate_snid.prefix + str(generate_snid.counter)
            if snid in _connected_sim_nodes.keys():
                generate_snid.counter += 1
            else:
                break
        return snid

    def on_register(conn: socket, addr: Tuple[str, int]) -> None:
        _remove_dead_sockets()
        snid = None
        for cur_snid, (main_sock, _) in _connected_sim_nodes.items():
            if main_sock.getpeername()[0] == addr[0]:
                snid = cur_snid
                break
        if snid:
            if snid in _requested_vehicle_sockets.keys():
                sid, vid = _requested_vehicle_sockets[snid]
                del _requested_vehicle_sockets[snid]
                _connected_sim_nodes[snid][1][sid][vid] = conn
            else:
                _logger.debug("Got superfluous socket for " + str(addr))
        else:
            snid = generate_snid()
            _connected_sim_nodes[snid] = (conn, {})
            snid_obj = SimulationNodeID()
            snid_obj.snid = snid
            conn.send(snid_obj.SerializeToString())

    sim_node_register_thread = Thread(target=accept_at_server, args=(create_server(5001), on_register))
    sim_node_register_thread.start()


_wait_for_sim_node_registers()
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=app.config["PORT"])
