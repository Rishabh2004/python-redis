import threading
import time
from dataclasses import dataclass
from enum import StrEnum

from src.radixtree import RadixTree
from src.skiplist import SkipList

type Value = str | list[str] | SkipList | RadixTree


class ValueType(StrEnum):
    STRING = "string"
    INTEGER = "int"
    LIST = "list"
    SORTED_SET = "zset"
    RADIX_TREE = "radix-tree"


@dataclass(slots=True)
class Element:
    value: Value
    expires: int | None = None

    @property
    def type(self) -> ValueType:
        """Infer the Redis type from the stored value."""
        if isinstance(self.value, bool):
            raise TypeError("Boolean values are not supported")

        if isinstance(self.value, str):
            if self.value.isnumeric():
                return ValueType.INTEGER
            return ValueType.STRING
        if isinstance(self.value, list):
            return ValueType.LIST
        if isinstance(self.value, SkipList):
            return ValueType.SORTED_SET
        if isinstance(self.value, RadixTree):
            return ValueType.RADIX_TREE

    def is_type(self, value_type: ValueType) -> bool:
        return self.type is value_type


class Store:
    def __init__(self):
        self._data: dict[str, Element] = {}
        self.condition = threading.Condition()
        self.transaction: bool = False
        self.buff: list[list[str]] = []

    @property
    def data(self) -> dict[str, Element]:
        return self._data

    @property
    def clock_ms(self) -> int:
        return int(time.time() * 1000)

    def set(self, key: str, value: Element) -> None:
        self._data[key] = value

    def get(self, key: str) -> Element | None:

        element = self._data.get(key, None)

        if element is not None and self._is_expired(element):
            self.data.pop(key, None)
            return None

        return element

    def _is_expired(self, element: Element) -> bool:
        return element.expires is not None and element.expires < self.clock_ms
