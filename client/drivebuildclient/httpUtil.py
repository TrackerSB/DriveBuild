from http.client import HTTPResponse
from typing import List, Callable, Union, Tuple, Any, Dict, AnyStr, Optional

from flask import Response

from drivebuildclient.aiExchangeMessages_pb2 import SimulationID, VehicleID, SimulationNodeID

AnyResponse = Union[Response, Tuple[Any, int]]


# FIXME Merge methods into only two methods?


def do_post_request(host: str, port: int, address: str, content: bytes) -> HTTPResponse:
    from http.client import HTTPConnection
    connection = HTTPConnection(host=host, port=port)
    connection.request("POST", address, body=content, headers={"content-type": "application/x-protobuf"})
    return connection.getresponse()


def do_get_request(host: str, port: int, address: str, params: Dict[str, AnyStr]) -> HTTPResponse:
    """
    :return: The response object of the request
    """
    from urllib.parse import urlencode
    from http.client import HTTPConnection
    connection = HTTPConnection(host=host, port=port)
    connection.request("GET", address + "?" + urlencode(params), headers={"content-type": "application/x-protobuf"})
    return connection.getresponse()


def process_get_request(min_params: List[str], on_parameter_available: Callable[[], AnyResponse]) -> AnyResponse:
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


def do_mixed_request(host: str, port: int, address: str, params: Dict[str, AnyStr], content: bytes) -> HTTPResponse:
    from urllib.parse import urlencode
    from http.client import HTTPConnection
    connection = HTTPConnection(host=host, port=port)
    connection.request("POST", address + "?" + urlencode(params), body=content,
                       headers={"content-type": "application/x-protobuf"})
    return connection.getresponse()


def process_mixed_request(min_params: List[str], on_parameter_available: Callable[[], AnyResponse]) -> AnyResponse:
    from flask import request
    # FIXME Any difference to processing GET requests?
    missing_params = list(filter(lambda p: p not in request.args, min_params))
    if missing_params:
        return Response(response="The request misses one of the parameters [\"" + "\", ".join(missing_params) + "\"]",
                        status=400, mimetype="text/plain")
    else:
        return on_parameter_available()


def extract_sid() -> Tuple[Optional[bytes], Optional[SimulationID]]:
    from flask import request
    serialized_sid_b = request.args.get("sid", default=None)
    if serialized_sid_b:
        serialized_sid = serialized_sid_b.encode()
        sid = SimulationID()
        sid.ParseFromString(serialized_sid)
        return serialized_sid, sid
    else:
        return None, None


def extract_vid() -> Tuple[Optional[bytes], Optional[VehicleID]]:
    from flask import request
    serialized_vid_b = request.args.get("vid", default=None)
    if serialized_vid_b:
        serialized_vid = serialized_vid_b.encode()
        vid = VehicleID()
        vid.ParseFromString(serialized_vid)
        return serialized_vid, vid
    else:
        return None, None


def extract_snid() -> Tuple[Optional[bytes], Optional[SimulationNodeID]]:
    from flask import request
    serialized_snid_b = request.args.get("snid", default=None)
    if serialized_snid_b:
        serialized_snid = serialized_snid_b.encode()
        snid = SimulationNodeID()
        snid.ParseFromString(serialized_snid)
        return serialized_snid, snid
    else:
        return None, None
