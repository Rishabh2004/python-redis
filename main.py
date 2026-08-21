"""Compatibility entry point for running the Redis server."""

import logging

from redis_server import RedisServer


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    RedisServer().serve_forever()


if __name__ == "__main__":
    main()
