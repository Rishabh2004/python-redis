"""Helpers for decoding requests and encoding RESP responses."""

NIL: bytes = b"$-1\r\n"
EMPTY_ARRAY: bytes = b"*0\r\n"
OK: bytes = b"+OK\r\n"


def parse_resp(data: str) -> list[str]:
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


def encode_array(values: list[str]) -> bytes:
    """Encode strings as a RESP array of bulk strings."""
    response = f"*{len(values)}\r\n"
    for value in values:
        response += f"${len(value)}\r\n{value}\r\n"
    return response.encode()


def encode_bulk_string(value: str) -> bytes:
    """Encode a string as a RESP bulk string."""
    return f"${len(value)}\r\n{value}\r\n".encode()


def encode_integer(value: int) -> bytes:
    """Encode an integer as a RESP integer."""
    return f":{value}\r\n".encode()
