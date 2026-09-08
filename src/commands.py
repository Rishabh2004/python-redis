from collections.abc import Callable

from src import list as rlist
from src import string, zset
from src.protocol import RespProtocol
from src.store import Store

type Commandhandler = Callable[[Store, list[str]], bytes]


class CommandProcessor:
    def __init__(self):
        self.database = Store()
        self._handler: dict[str, Commandhandler] = {
            "ping": string.ping,
            "echo": string.echo,
            "get": string.get_value,
            "set": string.set_value,
            "type": string.type,
            "rpush": rlist.rpush,
            "lrange": rlist.lrange,
            "lpush": rlist.lpush,
            "llen": rlist.llen,
            "lpop": rlist.lpop,
            "blpop": rlist.blob,
            "zadd": zset.zadd,
            "zrank": zset.zrank,
            "zrange": zset.zrange,
            "zcard": zset.zcard,
            "zscore": zset.zscore,
            "zrem": zset.zrem,
        }

    def execute(self, cmd: list[str]) -> bytes:
        command = cmd[0].lower()
        handler = self._handler.get(command)

        if handler is None:
            return RespProtocol.error("Invalid Command")

        return handler(self.database, cmd[1:])
