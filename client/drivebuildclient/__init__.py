from collections import defaultdict
from logging import getLogger
from math import floor, log10
from socket import socket
from threading import Lock
from typing import Tuple, List, Callable

name = "DriveBuild client"
CONTENT_LENGTH_LIMIT: int = 10000000  # 10 millions
# The length of the message transferring the content length
CONTENT_LENGTH_MESSAGE_LENGTH: int = floor(log10(CONTENT_LENGTH_LIMIT)) + 1
MAX_RETRY: int = 100
_logger = getLogger("DriveBuild.Client")


def static_vars(**kwargs):
    """
    Decorator hack for introducing local static variables.
    :param kwargs: The declarations of the static variables like "foo=42".
    :return: The decorated function.
    """

    def decorate(func):
        """
        Decorates the given function with local static variables based on kwargs.
        :param func: The function to decorate.
        :return: The decorated function.
        """
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate


def create_server(port: int) -> socket:
    from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(1)  # FIXME Determine appropriate value
    return server_socket


def accept_at_server(server_socket: socket, on_accept: Callable[[socket, Tuple[str, int]], None]) -> None:
    while True:
        conn, addr = server_socket.accept()
        _logger.debug(str(server_socket.getsockname()) + " accepted " + str(addr))
        on_accept(conn, addr)


def create_client(server_host: str, server_port: int) -> socket:
    from socket import AF_INET, SOCK_STREAM
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect((server_host, server_port))
    return client_socket


@static_vars(send_locks=defaultdict(lambda: Lock()))
def _send_message(sock: socket, message: bytes) -> None:
    message_length = len(message)
    _logger.debug(str(sock.getpeername()) + " sending " + str(message_length) + " bytes")
    if message_length > CONTENT_LENGTH_LIMIT:
        _logger.error("Can not send messages longer than " + str(CONTENT_LENGTH_LIMIT) + ".")
    else:
        message_length_message = str(message_length) \
            .ljust(CONTENT_LENGTH_MESSAGE_LENGTH, " ") \
            .encode()
        _send_message.send_locks[sock].acquire()
        sock.sendall(message_length_message)
        sock.sendall(message)
        _send_message.send_locks[sock].release()


# FIXME Introduce method receiving bytes until reaching a certain number
@static_vars(recv_locks=defaultdict(lambda: Lock()))
def _recv_message(sock: socket) -> bytes:
    from time import sleep
    _recv_message.recv_locks[sock].acquire()
    _logger.debug(str(sock.getsockname()) + " waiting for recv message length")
    try:
        tries = 0
        while tries < MAX_RETRY:
            content_length_message = sock.recv(CONTENT_LENGTH_MESSAGE_LENGTH).decode().strip()
            _logger.debug(str(sock.getsockname()) + " got message length message: " + content_length_message)
            if content_length_message:
                content_length = int(content_length_message)
                _logger.debug(
                    str(sock.getsockname()) + " waits for receiving a message of length " + str(content_length))
                break
            else:
                tries = tries + 1
                sleep(1)
        else:
            _logger.warning("Did not receive content length message.")
            return b""
    except ConnectionResetError:
        _logger.info("The socket " + str(sock.getsockname()) + " was closed.")
        content_length = 0
    except Exception as ex:
        _logger.warning("The socket stream of " + str(sock.getsockname())
                        + " got corrupted. It is likely that any further message will also break. Cause: " + str(ex))
        content_length = 0
    received_message = b""
    while len(received_message) < content_length:
        received_message = received_message + sock.recv(content_length - len(received_message))
    _recv_message.recv_locks[sock].release()
    return received_message


@static_vars(process_locks=defaultdict(lambda: Lock()))
def process_request(sock: socket, handle_message: Callable[[bytes, List[bytes]], bytes]) -> None:
    from drivebuildclient.aiExchangeMessages_pb2 import Num
    socket_name = str(sock.getsockname())
    process_request.process_locks[socket_name].acquire()
    action = _recv_message(sock)
    _logger.debug(socket_name + " received action " + action.decode())
    num_data = Num()
    num_data.ParseFromString(_recv_message(sock))
    _logger.debug(socket_name + " received num_data " + str(num_data.num))
    data = []
    for _ in range(num_data.num):
        data.append(_recv_message(sock))
        _logger.debug(socket_name + " received data " + str(data[-1]))
    process_request.process_locks[socket_name].release()
    # FIXME Include the send call to the blocked section?
    result = handle_message(action, data)
    _logger.debug(socket_name + " sends result")
    _send_message(sock, result)



def process_requests(waiting_socket: socket, handle_message: Callable[[bytes, List[bytes]], bytes]) -> None:
    # FIXME How to recover failures?
    try:
        while True:
            process_request(waiting_socket, handle_message)
    except (ConnectionAbortedError, ConnectionResetError):
        _logger.info("The socket " + str(waiting_socket.getsockname()) + " was closed.")


@static_vars(request_locks=defaultdict(lambda: Lock()))
def send_request(sock: socket, action: bytes, data: List[bytes]) -> bytes:
    from drivebuildclient.aiExchangeMessages_pb2 import Num
    send_request.request_locks[sock].acquire()
    _send_message(sock, action)
    num_data = Num()
    num_data.num = len(data)
    if num_data.num == 0:
        num_data.num = -1
    _send_message(sock, num_data.SerializeToString())
    for d in data:
        _send_message(sock, d)
    result = _recv_message(sock)
    send_request.request_locks[sock].release()
    return result
