"""TCP server lifecycle and connection handling."""

import logging
import socket
import threading

from .commands import CommandProcessor
from .protocol import parse_resp

LOGGER = logging.getLogger(__name__)
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6379
BUFFER_SIZE = 1024

DEFAULT_PROCESSOR = CommandProcessor()


def handle_connection(
    client_connection: socket.socket,
    client_address: object,
    processor: CommandProcessor | None = None,
) -> None:
    """Read and process commands until a client disconnects."""
    command_processor = processor or DEFAULT_PROCESSOR

    try:
        LOGGER.info("Client connected: %s", client_address)
        while True:
            request = client_connection.recv(BUFFER_SIZE)
            if not request:
                break

            LOGGER.debug("Received data: %r", request)
            try:
                parts = parse_resp(request.decode())
            except (ValueError, IndexError):
                continue

            if parts:
                client_connection.sendall(command_processor.execute(parts))
    except ConnectionResetError:
        LOGGER.warning("Connection abruptly lost: %s", client_address)
    finally:
        client_connection.close()
        LOGGER.info("Client disconnected: %s", client_address)


class RedisServer:
    """A threaded TCP server for the supported Redis commands."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        processor: CommandProcessor | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.processor = processor or DEFAULT_PROCESSOR

    def serve_forever(self) -> None:
        """Accept clients until the process receives a keyboard interrupt."""
        server = socket.create_server((self.host, self.port), reuse_port=True)
        try:
            while True:
                connection, address = server.accept()
                threading.Thread(
                    target=handle_connection,
                    args=(connection, address, self.processor),
                ).start()
        except KeyboardInterrupt:
            LOGGER.info("Server is stopping")
        finally:
            server.close()
