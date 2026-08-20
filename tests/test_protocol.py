import unittest

from redis_server.protocol import parse_resp


class ParseRespTests(unittest.TestCase):
    def test_parses_bulk_string_array(self) -> None:
        request = "*2\r\n$4\r\necho\r\n$5\r\nhello\r\n"

        self.assertEqual(parse_resp(request), ["echo", "hello"])

    def test_rejects_non_array_input(self) -> None:
        with self.assertRaisesRegex(ValueError, "Expected RESP array"):
            parse_resp("PING\r\n")


if __name__ == "__main__":
    unittest.main()
