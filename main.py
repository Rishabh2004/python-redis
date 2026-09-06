"""Compatibility entry point for running the Redis server."""

import logging
from argparse import ArgumentParser, Namespace

from src.server import RedisServer


class RedisApplication:
    def __init__(self):
        self.parser = self._build_parser()

    def run(self) -> None:
        args = self.parser.parse_args()
        self._configure_logging(args)

        RedisServer(host=args.host, port=args.port).serve_forever()

    @staticmethod
    def _build_parser() -> ArgumentParser:
        parser = ArgumentParser(description="Redis implemented in python")
        parser.add_argument("--port", type=int, default=6379, help="Port to bind")
        parser.add_argument("--host", type=str, default="localhost", help="Host interface to bind")
        parser.add_argument("--debug", action="store_true", help="Enable debug logging")
        return parser

    @staticmethod
    def _configure_logging(arguements: Namespace):
        logging.basicConfig(
            level=logging.DEBUG if arguements.debug else logging.INFO,
            format="[%(levelname)s] %(asctime)s * %(message)s",
            datefmt="%d-%m-%y %H:%M:%S",
        )


if __name__ == "__main__":
    RedisApplication().run()
