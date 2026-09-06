import logging

from src.protocol import RespProtocol
from src.store import Element, Store

logger = logging.getLogger(__name__)


def ping(_store: Store, _args: list[str]) -> bytes:
    return RespProtocol.PONG


def echo(_store: Store, args: list[str]) -> bytes:
    return RespProtocol.array(args)


def get_value(store: Store, args: list[str]) -> bytes:
    key = args[0]
    element = store.get(key)

    if element is None:
        return RespProtocol.NIL
    return RespProtocol.encode_value(element.value)


def set_value(store: Store, args: list[str]) -> bytes:
    logger.debug("ARGS %s", args)

    if len(args) not in (2, 4):
        logger.debug("Condition true")
        return RespProtocol.error("INVALID COMMAND")

    key, raw_value = args[0], args[1]

    expires = None
    if len(args) == 4:
        option, duration = args[2], int(args[3])
        if option == "px":
            expires = store.clock_ms + duration
        elif option == "mx":
            expires = store.clock_ms + (duration * 1000)
        else:
            return RespProtocol.error("INVALID COMMAND")

    store.set(
        key,
        Element(raw_value, expires=expires),
    )
    return RespProtocol.OK


def incr(store: Store, args: list[str]) -> bytes:
    if len(args) != 1:
        return RespProtocol.error("ERR wrong number if arguements for 'incr' command")

    entry = store.get(args[0])

    if entry is None:
        store.set(args[0], Element("1"))
        return RespProtocol.integer(1)
    value = entry.value
    if not isinstance(value, int):
        return RespProtocol.error("ERR value is not an integer or out of range")

    value += 1
    return RespProtocol.integer(value)


def type(store: Store, args: list[str]) -> bytes:

    if len(args) != 1:
        return RespProtocol.error("ERR wrong number if arguemnts for 'type' command")

    entry = store.get(args[0])

    if entry is None:
        return RespProtocol.bulk_string("none")
    else:
        return RespProtocol.bulk_string(entry.type)
