import random


class Node:
    def __init__(self, member: str, score: float, height: int):
        self.member = member
        self.score = score
        self.levels: list[None | Node] = [None] * height

    def __str__(self):
        return f"{self.member}({self.score})"


class SkipList:
    def __init__(self):
        self.MAX_LEVEL = 4
        self.P = 0.5
        self.level = 1
        self.HEAD = Node(member="", score=0, height=self.MAX_LEVEL)

    def _level(self) -> int:
        lvl = 1

        while random.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1

        return lvl

    def add(self, member: str, score: float):

        level = self._level()
        self.level = max(self.level, level)

        new_node = Node(member, score, level)
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

        # Print loop for priting only one element in skip list

    def print(self):

        for i in range(len(self.HEAD.levels) - 1, -1, -1):
            print(f"level {i}: HEAD", end="")

            pointer = self.HEAD.levels[i]

            while pointer is not None:
                print(f" -> {pointer}", end="")
                pointer = pointer.levels[i]

            print(" -> nil")


sk = SkipList()
sk.add("A", 10)
sk.add("B", 5)
sk.add("C", 3)
sk.add("D", 20)


sk.print()
