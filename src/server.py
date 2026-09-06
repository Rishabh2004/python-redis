import logging
import os
import socket
import threading

from src.commands import CommandProcessor
from src.config import RedisConf
from src.protocol import RespProtocol

logger = logging.getLogger(__name__)


class RedisServer:
    HOST = "locahost"
    PORT = 6379
    BUFFER_SIZE = 4096

    def __init__(self, host: str = HOST, port: int = PORT, buffer_size: int = BUFFER_SIZE):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.protocol = RespProtocol()
        self.processor = CommandProcessor()
        self.conf = RedisConf()

    def handle_connection(self, client: socket.socket, address):

        try:
            logger.info(f"CLIENT CONNECTED: {address}")

            while request := client.recv(self.buffer_size):
                logger.debug("REQUEST RECIEVED: %s", request)

                try:
                    parts = self.protocol.parse(request.decode().lower())

                except (UnicodeDecodeError, ValueError, IndexError):
                    logger.info("FAILED TO PARSE REQUEST: %s", request)
                    client.sendall(self.protocol.error("ERR Invalid Request"))
                    continue

                if parts:
                    resp = self.processor.execute(parts)
                    logger.debug("SERVER RESPONDED %s", resp)
                    client.sendall(resp)
        except ConnectionResetError:
            logger.warning("Connection abruptly lost: %s", address)
        finally:
            client.close()
            logger.info("Client disconnected: %s", address)

    def serve_forever(self) -> None:
        logger.info("SERVER STARTED RUNNING")
        logger.info("SERVER IS READY TO ACCEPT CONNECTION")
        logger.info("RUNNING AT PORT %s", self.port)
        logger.info("PID %s", os.getpid())
        server = socket.create_server((self.host, self.port), reuse_port=True)

        try:
            while True:
                try:
                    conn, addr = server.accept()

                    threading.Thread(
                        target=self.handle_connection,
                        args=(conn, addr),
                        daemon=True,
                        name=f"redis-client-{addr}",
                    ).start()
                except TimeoutError:
                    continue
        except KeyboardInterrupt:
            logger.info("SERVER IS STOPPING")
        finally:
            server.close()
            logger.info("SERVER STOPPED RUNNING")
