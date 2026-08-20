"""Command dispatch and the in-memory data store."""

import time
from collections.abc import Callable
from typing import TypeAlias

from .protocol import (
    EMPTY_ARRAY,
    NIL,
    encode_array,
    encode_bulk_string,
    encode_integer,
)

StoredValue: TypeAlias = dict[str, object]
Database: TypeAlias = dict[str, StoredValue]
CommandHandler: TypeAlias = Callable[[list[str]], bytes]

DATABASE: Database = {}
OK = b"+OK\r\n"


def _current_time_ms() -> int:
    return int(time.time() * 1000)


class CommandProcessor:
    """Dispatch parsed commands against an in-memory database."""

    def __init__(
        self,
        database: Database | None = None,
        clock_ms: Callable[[], int] = _current_time_ms,
    ) -> None:
        self.database = DATABASE if database is None else database
        self._clock_ms = clock_ms
        self._handlers: dict[str, CommandHandler] = {
            "ping": self._ping,
            "echo": self._echo,
            "set": self._set,
            "get": self._get,
            "rpush": self._rpush,
            "lrange": self._lrange,
        }

    def execute(self, parts: list[str]) -> bytes:
        """Execute a parsed command and return its RESP response."""
        command = parts[0].lower()
        handler = self._handlers.get(command)
        if handler is None:
            return OK
        return handler(parts[1:])

    def _ping(self, _arguments: list[str]) -> bytes:
        return encode_bulk_string("pong")

    def _echo(self, arguments: list[str]) -> bytes:
        return encode_array(arguments)

    def _set(self, arguments: list[str]) -> bytes:
        key, value = arguments[0], arguments[1]

        if len(arguments) == 4:
            option, duration = arguments[2], arguments[3]
            if option == "px":
                self.database[key] = {
                    "value": value,
                    "px": int(duration),
                    "inserted": self._clock_ms(),
                }
            elif option == "mx":
                self.database[key] = {
                    "value": value,
                    "mx": int(duration) * 1000,
                    "inserted": self._clock_ms(),
                }
        else:
            self.database[key] = {"value": value}

        return OK

    def _get(self, arguments: list[str]) -> bytes:
        key = arguments[0]
        entry = self.database.get(key)
        if entry is None:
            return NIL

        if self._is_expired(entry):
            self.database.pop(key, None)
            return NIL

        value = entry["value"]
        # Preserve the current wire behavior for both string and list values.
        return f"${len(value)}\r\n{value}\r\n".encode()  # type: ignore[arg-type]

    def _is_expired(self, entry: StoredValue) -> bool:
        current_time = self._clock_ms()
        inserted = entry.get("inserted")

        mx = entry.get("mx")
        if mx and int(mx) + int(inserted) < current_time:
            return True

        px = entry.get("px")
        return bool(px and int(px) + int(inserted) < current_time)

    def _rpush(self, arguments: list[str]) -> bytes:
        if len(arguments) < 2:
            return NIL

        key = arguments[0]
        entry = self.database.setdefault(key, {"value": []})
        values = entry["value"]
        if not isinstance(values, list):
            raise AttributeError("Stored value does not support append")

        for argument in arguments[1:]:
            values.append(int(argument) if argument.isnumeric() else argument)

        return encode_integer(len(values))

    def _lrange(self, arguments: list[str]) -> bytes:
        if len(arguments) < 3:
            return NIL

        key = arguments[0]
        start, end = int(arguments[1]), int(arguments[2])
        entry = self.database.get(key)
        if not entry or start > end:
            return EMPTY_ARRAY

        values = entry["value"]
        if not isinstance(values, list):
            raise TypeError("Stored value is not a list")
        if start > len(values):
            return EMPTY_ARRAY

        end = min(end, len(values))
        response = f"*{end - start}\r\n".encode()
        for index in range(start, end):
            value = values[index]
            if isinstance(value, str):
                response += encode_bulk_string(value)
            elif isinstance(value, int):
                response += encode_integer(value)

        return response
