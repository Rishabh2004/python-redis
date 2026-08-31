import json
import unittest

from src.commands import CommandProcessor
from src.protocol import EMPTY_ARRAY, NIL
from src.skiplist import SkipList


class CommandProcessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 1_000
        self.database: dict[str, dict[str, object]] = {}
        self.processor = CommandProcessor(self.database, lambda: self.now)

    def test_ping_and_echo(self) -> None:
        self.assertEqual(self.processor.execute(["PING"]), b"$4\r\npong\r\n")
        self.assertEqual(
            self.processor.execute(["echo", "hello", "world"]),
            b"*2\r\n$5\r\nhello\r\n$5\r\nworld\r\n",
        )

    def test_set_and_get(self) -> None:
        self.assertEqual(self.processor.execute(["set", "name", "redis"]), b"+OK\r\n")
        self.assertEqual(self.processor.execute(["get", "name"]), b"$5\r\nredis\r\n")
        self.assertEqual(self.processor.execute(["get", "missing"]), NIL)

    def test_expiring_value(self) -> None:
        self.processor.execute(["set", "key", "value", "px", "50"])
        self.now = 1_051

        self.assertEqual(self.processor.execute(["get", "key"]), NIL)
        self.assertNotIn("key", self.database)

    def test_list_commands(self) -> None:
        self.assertEqual(
            self.processor.execute(["rpush", "numbers", "1", "two", "3"]),
            b":3\r\n",
        )
        self.assertEqual(
            self.processor.execute(["lrange", "numbers", "0", "3"]),
            b"*3\r\n:1\r\n$3\r\ntwo\r\n:3\r\n",
        )
        self.assertEqual(self.processor.execute(["lrange", "missing", "0", "1"]), EMPTY_ARRAY)

    def test_get_preserves_existing_list_response(self) -> None:
        self.processor.execute(["rpush", "numbers", "1", "2"])

        self.assertEqual(self.processor.execute(["get", "numbers"]), b"$2\r\n[1, 2]\r\n")

    def test_skiplist_string_is_json_safe_and_readable(self) -> None:
        skiplist = SkipList()
        for member, score in [("b", 2.0), ("a", 1.0), ("c", 3.0)]:
            skiplist.add(member, score)

        rendered = str(skiplist)

        self.assertIn("HEAD", rendered)
        self.assertIn("a", rendered)
        self.assertIn("b", rendered)
        self.assertIn("c", rendered)
        self.assertEqual(json.loads(json.dumps({"value": rendered}))["value"], rendered)


if __name__ == "__main__":
    unittest.main()
