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
        self.MAX_LEVEL = max_level
        self.P = 0.5
        self.level = 1
        self.HEAD = Node(member="", score=0, height=self.MAX_LEVEL)
        self.member_map: dict[str, Node] = {}
        self.elements: int = 0

    def _level(self) -> int:
        lvl = 1

        while random.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1

        return lvl

    def add(self, member: str, score: float):

        level = self._level()
        self.level = max(self.level, level)
        new_node = Node(member, score, level)
        self.member_map[member] = new_node
        for i in range(level - 1, -1, -1):
            pointer = self.HEAD.levels[i]

            if pointer is None:
                self.HEAD.levels[i] = new_node
                continue

            if pointer.score >= score:
                new_node.levels[i] = pointer
                self.HEAD.levels[i] = new_node
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

            pointer = self.HEAD.levels[i]

            while pointer is not None:
                print(f" -> {pointer}", end="")
                pointer = pointer.levels[i]

            print(" -> nil")

    def search(self, member: str, score: float) -> tuple[Node | None, int]:
        rank = -1
        pointer = self.HEAD

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
