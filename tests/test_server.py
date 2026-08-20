import unittest

from redis_server.commands import CommandProcessor
from redis_server.server import handle_connection


class FakeConnection:
    def __init__(self, requests: list[bytes]) -> None:
        self.requests = iter(requests)
        self.responses: list[bytes] = []
        self.closed = False

    def recv(self, _buffer_size: int) -> bytes:
        return next(self.requests, b"")

    def sendall(self, response: bytes) -> None:
        self.responses.append(response)

    def close(self) -> None:
        self.closed = True


class HandleConnectionTests(unittest.TestCase):
    def test_processes_requests_until_disconnect(self) -> None:
        connection = FakeConnection(
            [
                b"*1\r\n$4\r\nPING\r\n",
                b"*3\r\n$3\r\nset\r\n$3\r\nkey\r\n$5\r\nvalue\r\n",
                b"*2\r\n$3\r\nget\r\n$3\r\nkey\r\n",
            ]
        )

        handle_connection(connection, "test-client", CommandProcessor({}))  # type: ignore[arg-type]

        self.assertEqual(
            connection.responses,
            [b"$4\r\npong\r\n", b"+OK\r\n", b"$5\r\nvalue\r\n"],
        )
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
