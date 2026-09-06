class RespProtocol:
    NIL: bytes = b"$-1\r\n"
    EMPTY_ARRAY: bytes = b"*0\r\n"
    OK: bytes = b"+OK\r\n"
    QUEUED: bytes = b"+QUEUED\r\n"
    PONG: bytes = b"+PONG\r\n"

    @staticmethod
    def parse(data: str) -> list[str]:
        """Parse a RESP array containing bulk strings.

        The server currently accepts one complete command per socket read. Stream
        buffering can be added here later without coupling it to command handling.
        """
        lines = data.split("\r\n")
        if not lines[0].startswith("*"):
            raise ValueError("Expected RESP array")

        count = int(lines[0][1:])
        values: list[str] = []
        index = 1
        for _ in range(count):
            length_line = lines[index]
            if not length_line.startswith("$"):
                raise ValueError("Expected bulk string")
            values.append(lines[index + 1])
            index += 2

        return values

    @staticmethod
    def response(values: list[bytes]) -> bytes:
        prefix = b"*" + str(len(values)).encode() + b"\r\n"
        response = b"".join(values)
        return prefix + response

    @staticmethod
    def array(values: list[str]) -> bytes:
        buff = f"*{len(values)}\r\n"

        for value in values:
            buff += f"${len(value)}\r\n{value}\r\n"

        return buff.encode()

    @staticmethod
    def integer(value: int) -> bytes:
        return f":{value}\r\n".encode()

    @staticmethod
    def bulk_string(value: str) -> bytes:
        return f"${len(value)}\r\n{value}\r\n".encode()

    @staticmethod
    def error(msg: str) -> bytes:
        return f"-{msg}\r\n".encode()

    @classmethod
    def encode_value(cls, value: object) -> bytes:
        """Choose the RESP representation for a Python value."""
        if isinstance(value, bool):
            raise TypeError("Boolean values are not supported")
        if isinstance(value, int):
            return cls.integer(value)
        if isinstance(value, str):
            return cls.bulk_string(value)
        if isinstance(value, list):
            return cls.response([cls.encode_value(item) for item in value])
        return cls.NIL
