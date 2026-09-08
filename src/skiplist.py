import random


class Node:
    def __init__(self, member: str, score: float, height: int):
        self.member = member
        self.score = score
        self.levels: list[None | Node] = [None] * height

    def __str__(self):
        return f"{self.member}({self.score})"


class SkipList:
    def __init__(self, max_level: int = 16):
        self._max_level = max_level
        self._p = 0.5
        self.level = 1
        self._head = Node(member="", score=0, height=self._max_level)
        self.member_map: dict[str, Node] = {}
        self.elements: int = 0

    def _level(self) -> int:
        lvl = 1

        while random.random() < self._p and lvl < self._max_level:
            lvl += 1

        return lvl

    def add(self, member: str, score: float):

        level = self._level()
        self.level = max(self.level, level)
        new_node = Node(member, score, level)
        if member in self.member_map:
            self.remove(member)

        self.member_map[member] = new_node
        for i in range(level - 1, -1, -1):
            pointer = self._head.levels[i]

            if pointer is None:
                self._head.levels[i] = new_node
                continue

            if pointer.score >= score:
                new_node.levels[i] = pointer
                self._head.levels[i] = new_node
                continue

            while True:
                next_node = pointer.levels[i]

                if next_node is None:
                    break

                if next_node.score >= score:
                    break

                pointer = next_node

            new_node.levels[i] = pointer.levels[i]
            pointer.levels[i] = new_node
        self.elements += 1

    def print(self):

        for i in range(self.level - 1, -1, -1):
            print(f"level {i}: HEAD", end="")

            pointer = self._head.levels[i]

            while pointer is not None:
                print(f" -> {pointer}", end="")
                pointer = pointer.levels[i]

            print(" -> nil")

    def search(self, member: str, score: float) -> tuple[Node | None, int]:
        rank = -1
        pointer = self._head

        for i in range(self.level - 1, -1, -1):
            next_node = pointer.levels[i]

            while next_node is not None and (
                next_node.score < score or (next_node.score == score and next_node.member < member)
            ):
                rank += 1
                pointer = next_node
                next_node = pointer.levels[i]

        candidate = pointer.levels[0]
        if candidate is not None and candidate.score == score and candidate.member == member:
            return candidate, rank + 1

        return None, -1

    def get_score(self, member: str) -> float | None:
        node = self.member_map.get(member)
        return node.score if node else None

    def remove(self, member: str) -> bool:
        old_node = self.member_map.get(member, None)
        is_deleted = False

        if old_node is not None:
            score = old_node.score

            pointer = self._head
            for i in range(self.level - 1, -1, -1):
                next_node = pointer.levels[i]

                while next_node is not None and (
                    next_node.score < score
                    or (next_node.score == score and next_node.member < member)
                ):
                    pointer = next_node
                    next_node = pointer.levels[i]

                if pointer.levels[i] is old_node:
                    pointer.levels[i] = old_node.levels[i]
                    is_deleted = True

            del self.member_map[member]
            self.elements -= 1
        return is_deleted
