from src.protocol import RespProtocol
from src.skiplist import SkipList
from src.store import Element, Store


def zadd(store: Store, args: list[str]) -> bytes:
    args_len = len(args)

    if args_len != 3:
        return RespProtocol.NIL

    key = args[0]
    score = float(args[1])
    member = args[2]

    sset = store.data.setdefault(key, Element(SkipList()))
    if not isinstance(sset.value, SkipList):
        return RespProtocol.NIL

    found_member = sset.value.get_score(member)

    if found_member is None:
        sset.value.add(member, score)
        return RespProtocol.integer(1)

    return RespProtocol.integer(0)


def zrank(store: Store, args: list[str]) -> bytes:
    if len(args) != 2:
        return RespProtocol.NIL

    key = args[0]
    member = args[1]

    sset = store.data.setdefault(key, Element(SkipList()))
    if not isinstance(sset.value, SkipList):
        return RespProtocol.NIL

    found_member = sset.value.get_score(member)

    if found_member is None:
        return RespProtocol.NIL
    else:
        _, rank = sset.value.search(member, found_member)
        return RespProtocol.integer(rank)


def zrange(store: Store, args: list[str]) -> bytes:
    if len(args) < 3:
        return RespProtocol.NIL

    key = args[0]
    start, end = int(args[1]), int(args[2])

    sset = store.data.get(key, None)
    if sset is None:
        return RespProtocol.EMPTY_ARRAY

    if not isinstance(sset.value, SkipList):
        return RespProtocol.NIL

    if start > sset.value.elements:
        return RespProtocol.NIL

    if start > end > 0:
        return RespProtocol.EMPTY_ARRAY

    if start < 0:
        start = sset.value.elements + start

    if end < 0:
        end = sset.value.elements + end

    end = min(end, sset.value.elements)

    result = []
    idx = 0
    pointer = sset.value._head.levels[0]
    while pointer is not None and idx <= end:
        if idx >= start:
            result.append(pointer.member)

        pointer = pointer.levels[0]
        idx += 1

    return RespProtocol.array(result)


def zcard(store: Store, args: list[str]) -> bytes:
    if len(args) != 1:
        return RespProtocol.NIL
    key = args[0]

    sset = store.data.get(key, None)
    if sset is None:
        return RespProtocol.integer(0)

    if not isinstance(sset.value, SkipList):
        return RespProtocol.integer(0)

    return RespProtocol.integer(sset.value.elements)


def zscore(store: Store, args: list[str]) -> bytes:
    if len(args) != 2:
        return RespProtocol.NIL
    key = args[0]
    member = args[1]
    sset = store.data.get(key, None)
    if sset is None:
        return RespProtocol.NIL

    if not isinstance(sset.value, SkipList):
        return RespProtocol.NIL

    member_score = sset.value.get_score(member)

    if member_score is None:
        return RespProtocol.NIL

    return RespProtocol.bulk_string(str(member_score))


def zrem(store: Store, args: list[str]) -> bytes:
    if len(args) != 2:
        return RespProtocol.NIL

    key = args[0]
    member = args[1]
    sset = store.data.get(key, None)
    if sset is None:
        return RespProtocol.NIL

    if not isinstance(sset.value, SkipList):
        return RespProtocol.NIL

    if sset.value.remove(member):
        return RespProtocol.integer(1)
    else:
        return RespProtocol.integer(0)
