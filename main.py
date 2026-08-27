"""Compatibility entry point for running the Redis server."""

import logging

from src import RedisServer


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s * %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    RedisServer().serve_forever()


if __name__ == "__main__":
    main()
