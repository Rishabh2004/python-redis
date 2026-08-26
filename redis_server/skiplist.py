import random


class Node:
    def __init__(self, member: str, score: float):
        self.member = member
        self.score = score
        self.next: Node | None = None
        self.levels = []

    def __str__(self):
        return f"{self.member}({self.score})"


class SkipList:
    def __init__(self):
        # self.head: Node | None = None
        self.MAX_LEVEL = 4
        self.P = 0.5
        self.levels: list[Node | None] = [None] * self.MAX_LEVEL
        self.level = 1

    def _level(self) -> int:
        lvl = 1

        while random.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1

        return lvl

    def add(self, member: str, score: float):

        level = self._level()
        self.level = max(self.level, level)
        for i in range(level - 1, -1, -1):
            node = Node(member, score)
            curr_ll = self.levels[i]
            if curr_ll is None:
                self.levels[i] = node
            else:
                temp = curr_ll

                while temp.next is not None:
                    temp = temp.next

                temp.next = node
                self.levels[i] = curr_ll

    def print(self):

        count = 3
        for lvl in range(len(self.levels)):
            buff = f"level :{count - lvl} header --> "
            node = self.levels[count - lvl]
            if node is None:
                buff += "nil"
                print(buff)
                continue

            temp = node
            while temp.next is not None:
                buff += f"{temp.member}({temp.score}) --> "
                temp = temp.next
            buff += f"{temp.member}({temp.score}) --> "
            buff += "nil"
            print(buff)


sk = SkipList()
sk.add("A", 10)
sk.add("B", 5)
sk.add("C", 3)
sk.add("D", 20)


sk.print()
