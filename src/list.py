import logging

from src.protocol import RespProtocol
from src.store import Element, Store

logger = logging.getLogger(__name__)


def rpush(store: Store, args: list[str]) -> bytes:
    if len(args) < 2:
        return RespProtocol.error("Invalid command for 'rpush' ")

    key = args[0]
    entry = store.data.setdefault(key, Element([]))

    value = entry.value

    if not isinstance(value, list):
        return RespProtocol.error("Invalid key expected list")

    with store.condition:
        for i in range(1, len(args)):
            if len(value) == 0:
                store.buff.append([key, args[i]])
                store.condition.notify()
            value.append(args[i])
    logger.debug(f"DATA inserted {[args[1::]]}")
    return RespProtocol.integer(len(value))


def lrange(store: Store, args: list[str]) -> bytes:
    if len(args) < 3:
        return RespProtocol.error("Invalid command for 'lrange' ")

    key = args[0]
    start, end = int(args[1]), int(args[2])
    entry = store.data.get(key)

    if not entry:
        return RespProtocol.EMPTY_ARRAY

    if end > 0 and start > end:
        return RespProtocol.EMPTY_ARRAY

    values = entry.value

    if not isinstance(values, list):
        raise TypeError("Stored value is not a list")
    if start > len(values):
        return RespProtocol.EMPTY_ARRAY

    if start < 0:
        start = len(values) + start

    if end < 0:
        end = len(values) + end + 1
    end = min(end, len(values))
    response = f"*{end - start}\r\n".encode()
    for index in range(start, end):
        value = values[index]
        if isinstance(value, str):
            response += RespProtocol.bulk_string(value)
        elif isinstance(value, int):
            response += RespProtocol.integer(value)

    return response


def lpush(store: Store, args: list[str]) -> bytes:
    if len(args) < 2:
        return RespProtocol.NIL

    key = args[0]

    entry = store.data.setdefault(key, Element([]))

    value = entry.value

    if not isinstance(value, list):
        return RespProtocol.error(f"Stored key {key} is not list")

    with store.condition:
        temp_arr = []

        for i in range(len(args) - 1, 0, -1):
            if len(value) == 0 and i == len(args) - 1:
                store.buff.append([key, args[i]])
                store.condition.notify()
            temp_arr.append(args[i])

        value.extend(temp_arr)
        logger.debug(f"DATA APPENED {temp_arr}")
        return RespProtocol.integer(len(value))


def llen(store: Store, args: list[str]) -> bytes:

    if len(args) != 1:
        return RespProtocol.NIL

    key = args[0]

    entry = store.data.get(key, None)

    if entry is None:
        return RespProtocol.integer(0)

    value = entry.value

    if not isinstance(value, list):
        return RespProtocol.error("Stored value is not list")

    return RespProtocol.integer(len(value))


def lpop(store: Store, args: list[str]) -> bytes:
    args_len = len(args)
    if args_len > 2 and args_len < 1:
        return RespProtocol.NIL

    key = args[0]
    entry = store.data.get(key)

    if entry is None:
        return RespProtocol.NIL

    if not isinstance(entry.value, list):
        raise TypeError("Stored value is not a list")
    if len(entry.value) == 0:
        return RespProtocol.NIL

    if args_len == 2 and len(entry.value) >= args_len:
        buff: list[str] = []
        for i in range(args_len):
            buff.append(str(entry.value[0]))
            entry.value.pop(0)
        return RespProtocol.array(buff)

    return RespProtocol.bulk_string(str(entry.value.pop(0)))


def blob(store: Store, args: list[str]) -> bytes:

    args_len = len(args)

    if args_len != 2:
        return RespProtocol.error("Invalid Command for list")

    key = args[0]
    timeout = float(args[1])

    entry = store.data.setdefault(key, Element([]))

    if not isinstance(entry.value, list):
        return RespProtocol.error("Invalid Command for list")

    if len(entry.value) > 0:
        return RespProtocol.bulk_string(str(entry.value.pop(0)))

    with store.condition:
        if timeout == 0:
            while len(entry.value) == 0:
                store.condition.wait()
        else:
            notified = store.condition.wait(timeout)

            if not notified:
                return RespProtocol.NIL

        if len(entry.value) == 0:
            return RespProtocol.NIL
        entry.value.pop(0)

        return RespProtocol.array(store.buff.pop(0))
