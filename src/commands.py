"""Command dispatch and the in-memory data store."""

import threading
import time
from collections.abc import Callable

from src.skiplist import SkipList

from .protocol import (
    EMPTY_ARRAY,
    NIL,
    OK,
    QUEUED,
    encode_array,
    encode_bulk_string,
    encode_integer,
    error,
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
        self.in_transcation: bool = False
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
            "zrank": self._zrank,
            "zrange": self._zrange,
            "zcard": self._zcard,
            "zscore": self._zscore,
            "zrem": self._zrem,
            "incr": self._incr,
            "multi": self._multi,
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

        try:
            value = int(value)
            v_type = "int"
        except ValueError:
            v_type = "string"

        if len(arguments) == 4:
            option, duration = arguments[2], arguments[3]
            if option == "px":
                self.database[key] = {
                    "value": value,
                    "px": int(duration),
                    "inserted": self._clock_ms(),
                    "type": v_type,
                }
            elif option == "mx":
                self.database[key] = {
                    "value": value,
                    "mx": int(duration) * 1000,
                    "inserted": self._clock_ms(),
                    "type": v_type,
                }
        else:
            self.database[key] = {"value": value, "type": v_type}

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
            return encode_bulk_string(value)
        if isinstance(value, list):
            return encode_array(value)
        if isinstance(value, int):
            return encode_bulk_string(str(value))
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

        if end < 0:
            end = len(values) + end + 1
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

    def _lpop(self, args: list[str]) -> bytes:
        args_len = len(args)
        if args_len > 2 and args_len < 1:
            return NIL

        key = args[0]
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

    def _blpop(self, args: list[str]) -> bytes:
        args_len = len(args)
        if args_len != 2:
            return NIL

        key = args[0]
        timeout = float(args[1])
        entry = self.database.setdefault(key, {"value": []})

        if not isinstance(entry["value"], list):
            return NIL

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

    def _print(self, _: list[str]):
        print(self.database)
        return OK

    def _zadd(self, args: list[str]) -> bytes:
        args_len = len(args)

        if args_len != 3:
            return NIL

        key = args[0]
        score = float(args[1])
        member = args[2]

        sset: StoredValue = self.database.setdefault(key, {"value": SkipList(), "type": "sset"})
        if not isinstance(sset["value"], SkipList):
            return NIL

        found_member = sset["value"].get_score(member)

        if found_member is None:
            sset["value"].add(member, score)
            return encode_integer(1)

        return encode_integer(0)

    def _zrank(self, args: list[str]) -> bytes:
        if len(args) != 2:
            return NIL

        key = args[0]
        member = args[1]

        sset = self.database.setdefault(key, {"value": SkipList(), "type": "sset"})
        if not isinstance(sset["value"], SkipList):
            raise TypeError("Stored value is not a SortedSet")

        member_node_score = sset["value"].get_score(member)

        if member_node_score is None:
            return NIL
        else:
            _, rank = sset["value"].search(member, member_node_score)
            return encode_integer(rank)

    def _zrange(self, args: list[str]) -> bytes:
        if len(args) < 3:
            return NIL

        key = args[0]
        start, end = int(args[1]), int(args[2])

        sset = self.database.get(key, None)
        if sset is None:
            return EMPTY_ARRAY

        if not isinstance(sset["value"], SkipList):
            return NIL

        if start > sset["value"].elements:
            return NIL

        if start > end > 0:
            return EMPTY_ARRAY

        if start < 0:
            start = sset["value"].elements + start

        if end < 0:
            end = sset["value"].elements + end

        end = min(end, sset["value"].elements)

        result = []
        idx = 0
        pointer = sset["value"].HEAD.levels[0]
        while pointer is not None and idx <= end:
            if idx >= start:
                result.append(pointer.member)

            pointer = pointer.levels[0]
            idx += 1

        return encode_array(result)

    def _zcard(self, args: list[str]) -> bytes:
        if len(args) != 1:
            return NIL
        key = args[0]

        sset = self.database.get(key, None)
        if sset is None:
            return encode_integer(0)

        if not isinstance(sset["value"], SkipList):
            return encode_integer(0)

        return encode_integer(sset["value"].elements)

    def _zscore(self, args: list[str]) -> bytes:
        if len(args) != 2:
            return NIL
        key = args[0]
        member = args[1]
        sset = self.database.get(key, None)
        if sset is None:
            return NIL

        if not isinstance(sset["value"], SkipList):
            return NIL

        member_score = sset["value"].get_score(member)

        if member_score is None:
            return NIL

        return encode_bulk_string(str(member_score))

    def _zrem(self, args: list[str]) -> bytes:
        if len(args) != 2:
            return NIL

        key = args[0]
        member = args[1]
        sset = self.database.get(key, None)
        if sset is None:
            return NIL

        if not isinstance(sset["value"], SkipList):
            return NIL

        if sset["value"].remove(member):
            return encode_integer(1)
        else:
            return encode_integer(0)

    def _incr(self, args: list[str]) -> bytes:
        if len(args) != 1:
            return NIL

        key = args[0]

        if key not in self.database:
            self.database[key] = {"value": 1, "type": "int"}
            return encode_integer(1)
        else:
            data = self.database[key]

            if data["type"] == "string" and isinstance(data["type"], str):
                return error("ERR value is not an integer or out of range")
            else:
                if isinstance(data["value"], int):
                    val = data["value"]
                    val = val + 1
                    data["value"] = val
                    return encode_integer(val)
                else:
                    return error("ERR value is not an integer or out of range")

    def _multi(self, _: list[str]) -> bytes:
        self.in_transcation = True
        if self.in_transcation is True:
            self.commmand_queue = []
        return QUEUED
