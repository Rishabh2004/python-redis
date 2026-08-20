# Python Redis

An educational, dependency-free Redis-compatible server written in Python. It
implements a focused subset of RESP commands while keeping protocol parsing,
command execution, and network concerns separate.

## Supported commands

- `PING`
- `ECHO`
- `SET` and `GET`, including the existing `px` and `mx` expiry options
- `RPUSH` and `LRANGE`

## Project structure

```text
redis_server/
├── commands.py   # Command registry and in-memory data store
├── protocol.py   # RESP parsing and response encoding
└── server.py     # Threaded TCP server lifecycle
tests/            # Dependency-free unit tests
client.py         # Minimal example client
main.py           # Server entry point
```

## Run the server

Python 3.13 or newer is required.

```bash
uv run python main.py
```

The server listens on `localhost:6379`. In another terminal, run the example
client:

```bash
uv run python client.py
```

## Run tests

```bash
uv run python -m unittest discover -v
```
