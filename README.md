# Python Redis

An educational, dependency-free Redis-compatible server written in Python. It
implements a focused subset of the Redis Serialization Protocol (RESP), with
separate protocol parsing, command handling, storage, and TCP server layers.

## Features

- Threaded TCP server, listening on `localhost:6379` by default
- RESP command parsing and response encoding
- In-memory strings with `px` (milliseconds) and `mx` (seconds) expiry options
- Lists, including blocking pops
- Sorted sets backed by a skip list

## Supported commands

| Type | Commands |
| --- | --- |
| Connection | `PING`, `ECHO` |
| Strings | `SET`, `GET`, `TYPE` |
| Lists | `RPUSH`, `LPUSH`, `LRANGE`, `LLEN`, `LPOP`, `BLPOP` |
| Sorted sets | `ZADD`, `ZRANK`, `ZRANGE`, `ZCARD`, `ZSCORE`, `ZREM` |

## Requirements

- Python 3.13 or newer
- [uv](https://docs.astral.sh/uv/) (optional, used in the commands below)

## Run the server

```bash
uv run python main.py
```

The server accepts optional host and port settings:

```bash
uv run python main.py --host 127.0.0.1 --port 6380 --debug
```

## Try it with redis-cli

With the server running in one terminal:

```bash
redis-cli PING
redis-cli SET greeting hello
redis-cli GET greeting
redis-cli ZADD scores 10 alice
redis-cli ZRANGE scores 0 -1
```

You can also run the included example client:

```bash
uv run python client.py
```

## Run tests

```bash
uv run python -m unittest discover -v
```

## Project structure

```text
src/
├── commands.py   # Command registry and dispatcher
├── protocol.py   # RESP parsing and response encoding
├── server.py     # Threaded TCP server lifecycle
├── store.py      # In-memory storage and expiry state
├── string.py     # String command handlers
├── list.py       # List command handlers
└── zset.py       # Sorted-set command handlers and skip-list integration
tests/            # Unit tests
client.py         # Minimal example client
main.py           # Server entry point
```
