"""Command dispatch and the in-memory data store."""

import threading
import time
from collections.abc import Callable

from src.skiplist import SkipList

from .protocol import (
    EMPTY_ARRAY,
    NIL,
    OK,
    encode_array,
    encode_bulk_string,
    encode_integer,
)

type StoredValue = dict[str, object]
type Database = dict[str, StoredValue]
type CommandHandler = Callable[[list[str]], bytes]

DATABASE: Database = {}

condition = threading.Condition()
shared_buff = []


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
            "lpush": self._lpush,
            "llen": self._llen,
            "lpop": self._lpop,
            "blpop": self._blpop,
            "zadd": self._zadd,
            "print": self._print,
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
        if isinstance(value, str):
            return f"${len(value)}\r\n{value}\r\n".encode()
        if isinstance(value, list):
            return f"${len(value)}\r\n{value}\r\n".encode()
        return NIL

    def _as_int(self, value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, str)):
            return int(value)
        return None

    def _is_expired(self, entry: StoredValue) -> bool:
        current_time = self._clock_ms()
        inserted = self._as_int(entry.get("inserted"))
        if inserted is None:
            return False

        mx = self._as_int(entry.get("mx"))
        if mx is not None and inserted + mx < current_time:
            return True

        px = self._as_int(entry.get("px"))
        return px is not None and inserted + px < current_time

    def _rpush(self, arguments: list[str]) -> bytes:
        if len(arguments) < 2:
            return NIL

        key = arguments[0]
        entry = self.database.setdefault(key, {"value": []})
        values = entry["value"]
        if not isinstance(values, list):
            raise TypeError("Stored value does not support append")

        with condition:
            for argument in arguments[1:]:
                value = int(argument) if argument.isnumeric() else argument
                if len(values) == 0:
                    values.append(value)
                    shared_buff.append([key, arguments[1]])
                    condition.notify(1)
                    continue
                values.append(value)

        return encode_integer(len(values))

    def _lrange(self, arguments: list[str]) -> bytes:
        if len(arguments) < 3:
            return NIL

        key = arguments[0]
        start, end = int(arguments[1]), int(arguments[2])
        entry = self.database.get(key)
        if not entry:
            return EMPTY_ARRAY

        if end > 0 and start > end:
            return EMPTY_ARRAY

        values = entry["value"]
        if not isinstance(values, list):
            raise TypeError("Stored value is not a list")
        if start > len(values):
            return EMPTY_ARRAY

        if start < 0:
            start = len(values) + start
            print(start)
        if end < 0:
            end = len(values) + end + 1
            print(end)
        end = min(end, len(values))
        response = f"*{end - start}\r\n".encode()
        for index in range(start, end):
            value = values[index]
            if isinstance(value, str):
                response += encode_bulk_string(value)
            elif isinstance(value, int):
                response += encode_integer(value)

        return response

    def _lpush(self, arguments: list[str]) -> bytes:
        if len(arguments) < 2:
            return NIL

        key = arguments[0]
        entry = self.database.setdefault(key, {"value": []})
        values = entry["value"]
        temp_arr = []
        if not isinstance(values, list):
            raise TypeError("Stored value does not support append")

        for arguement in arguments[len(arguments) - 1 : 0 : -1]:
            temp_arr.append(int(arguement) if arguement.isnumeric() else arguement)

        values.extend(temp_arr)
        return encode_integer(len(values))

    def _llen(self, arguments: list[str]) -> bytes:
        if len(arguments) != 1:
            return NIL
        key = arguments[0]
        entry = self.database.get(key)
        if entry is None:
            return encode_integer(0)
        if not isinstance(entry["value"], list):
            raise TypeError("Stored value is not a list")

        return encode_integer(len(entry["value"]))

    def _lpop(self, arguements: list[str]) -> bytes:
        args_len = len(arguements)
        if args_len > 2 and args_len < 1:
            return NIL

        key = arguements[0]
        entry = self.database.get(key)

        if entry is None:
            return NIL

        if not isinstance(entry["value"], list):
            raise TypeError("Stored value is not a list")
        if len(entry["value"]) == 0:
            return NIL

        if args_len == 2 and len(entry["value"]) >= args_len:
            buff: list[str] = []
            for i in range(args_len):
                buff.append(str(entry["value"][0]))
                entry["value"].pop(0)
            return encode_array(buff)

        return encode_bulk_string(str(entry["value"].pop(0)))

    def _blpop(self, arguements: list[str]) -> bytes:
        args_len = len(arguements)
        if args_len != 2:
            return NIL

        key = arguements[0]
        timeout = float(arguements[1])
        entry = self.database.setdefault(key, {"value": []})

        if not isinstance(entry["value"], list):
            raise TypeError("Stored value is not a list")

        if len(entry["value"]) > 0:
            return encode_bulk_string(str(entry["value"].pop(0)))

        with condition:
            if timeout == 0:
                while len(entry["value"]) == 0:
                    condition.wait()
            else:
                notified = condition.wait(timeout)

                if not notified:
                    return NIL

            if len(entry["value"]) == 0:
                return NIL
            entry["value"].pop(0)

            return encode_array(shared_buff.pop(0))

    def _print(self, arguements: list[str]):
        print(self.database)
        return OK

    def _zadd(self, arguements: list[str]):
        args_len = len(arguements)

        if args_len != 3:
            return NIL

        key = arguements[0]
        score = float(arguements[1])
        member = arguements[2]

        sset = self.database.setdefault(key, {"value": SkipList(), "type": "sset"})

        if not isinstance(sset["value"], SkipList):
            raise TypeError("Stored value is not a SortedSet")

        sset["value"].add(member, score)

        return encode_integer(1)
