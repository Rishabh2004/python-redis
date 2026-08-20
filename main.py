"""Compatibility entry point for running the Redis server."""

import logging

from redis_server import DATABASE, RedisServer, handle_connection, parse_resp
from redis_server.protocol import EMPTY_ARRAY, NIL

# Keep the original public names available for existing imports.
db = DATABASE
EMPTY_ARR = EMPTY_ARRAY


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    RedisServer().serve_forever()


if __name__ == "__main__":
    main()
