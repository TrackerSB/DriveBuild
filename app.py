from typing import Callable, List, Tuple

from celery.result import AsyncResult
from flask import Flask, Response
from redis import StrictRedis

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
# app.app_context().push()  # FIXME Do I need this?
redis_server = StrictRedis(host=app.config["REDIS_HOST"], port=app.config["REDIS_PORT"])

all_tasks: List[Tuple[str, AsyncResult]] = []


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


@app.route("/", methods=["GET", "POST"])
def test_launcher():
    from flask import render_template, request, flash, redirect
    from tc_manager import run_tests
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
        if file and allowed_file(file.filename):
            all_tasks.extend(run_tests(file))
            return render_template("testMonitor.html")
    return render_template("test_launcher.html")


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


def _ai_get_request_stub(min_params: List[str], on_parameter_available: Callable[[], Response]) -> Response:
    """
    This stub is designed for GET requests.
    """
    from flask import request
    missing_params = list(filter(lambda p: p not in request.args, min_params))
    if missing_params:
        return Response(response="The request misses one of the parameters [\"" + "\", ".join(missing_params) + "\"]",
                        status=400, mimetype="text/plain")
    else:
        return on_parameter_available()


@app.route("/ai/waitForSimulatorRequest", methods=["GET"])
def wait_for_simulator_request():
    def do() -> Response:
        from flask import request
        from communicator import ai_wait_for_simulator_request
        from aiExchangeMessages_pb2 import SimStateResponse, AiID
        aid = AiID()
        aid.ParseFromString(request.args["aid"].encode())
        ai_wait_for_simulator_request(aid)
        response = SimStateResponse()
        response.state = SimStateResponse.SimState.RUNNING
        return Response(response=response.SerializeToString(), status=200, mimetype="application/x-protobuf")

    return _ai_get_request_stub(["aid"], do)


@app.route("/ai/requestData", methods=["GET"])
def request_data():
    def do() -> Response:
        from flask import request
        from aiExchangeMessages_pb2 import DataRequest
        from communicator import ai_request_data
        data_request = DataRequest()
        data_request.ParseFromString(request.args["request"].encode())
        data_response = ai_request_data(data_request)
        return Response(response=data_response.SerializeToString(), status=200, mimetype="application/x-protobuf")

    return _ai_get_request_stub(["request"], do)


@app.route("/ai/control", methods=["POST"])
def control():
    from aiExchangeMessages_pb2 import Control
    from flask import request
    from communicator import ai_control
    control_msg = Control()
    control_msg.ParseFromString(request.data)
    void = ai_control(control_msg)
    return Response(response=void.SerializeToString(), status=200, mimetype="application/x-protobuf")


@app.route("/stats/status", methods=["GET"])
def status():
    from flask import render_template
    if all_tasks:
        status_text = "<br />".join(["Simulation: " + task[0] + ": " + task[1].state for task in all_tasks])
    else:
        status_text = "There were no test executions so far"
    return render_template("status.html", status_text=status_text), 200


if __name__ == "__main__":
    app.run()
