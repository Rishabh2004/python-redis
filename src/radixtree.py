from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RadixNode:
    label: str = ""
    is_end: bool = False
    children: dict[str, RadixNode] = field(default_factory=dict)


class RadixTree:
    def __init__(self):
        self.root = RadixNode("")

    # ------------------------------------------------------------------
    # INSERT
    # ------------------------------------------------------------------
    def insert(self, word: str) -> None:
        node = self.root
        remaining = word

        while True:
            first_char = remaining[0]

            # No child starts with our first character -> just add a new edge
            if first_char not in node.children:
                new_node = RadixNode(remaining)
                new_node.is_end = True
                node.children[first_char] = new_node
                return

            child = node.children[first_char]
            common_len = self._common_prefix_len(remaining, child.label)

            if common_len == len(child.label):
                # Full edge matched, move down and continue with the rest
                remaining = remaining[common_len:]
                if remaining == "":
                    child.is_end = True
                    return
                node = child
                continue

            # Partial match -> split the edge
            self._split_edge(node, child, common_len)
            remaining = remaining[common_len:]
            if remaining == "":
                node.children[first_char].is_end = True
                return
            node = node.children[first_char]

    def _split_edge(self, parent: RadixNode, child: RadixNode, split_at: int) -> None:
        # child.label gets cut into two parts: [0:split_at] and [split_at:]
        common_part = child.label[:split_at]
        remaining_part = child.label[split_at:]

        # New intermediate node takes the common part
        mid_node = RadixNode(common_part)
        parent.children[common_part[0]] = mid_node

        # Old child keeps the leftover suffix, now hangs under mid_node
        child.label = remaining_part
        mid_node.children[remaining_part[0]] = child

    # ------------------------------------------------------------------
    # SEARCH
    # ------------------------------------------------------------------
    def search(self, word: str) -> bool:
        node = self._find_node(word)
        return node is not None and node.is_end

    def _find_node(self, word: str) -> RadixNode | None:
        node = self.root
        remaining = word
        while remaining:
            first_char = remaining[0]
            if first_char not in node.children:
                return None
            child = node.children[first_char]
            common_len = self._common_prefix_len(remaining, child.label)
            if common_len != len(child.label):
                return None
            remaining = remaining[common_len:]
            node = child
        return node

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def delete(self, word: str) -> bool:
        if not self.search(word):
            return False
        self._delete_recursive(self.root, word)
        return True

    def _delete_recursive(self, node: RadixNode, remaining: str) -> bool:
        """
        Returns True if the caller should remove `child` from
        `node.children` entirely (dead leaf with nothing left).
        """
        first_char = remaining[0]
        child = node.children[first_char]
        common_len = self._common_prefix_len(remaining, child.label)
        remaining_after = remaining[common_len:]

        if remaining_after == "":
            # child is the target word's terminal node
            child.is_end = False
        else:
            drop_grandchild = self._delete_recursive(child, remaining_after)
            if drop_grandchild:
                del child.children[remaining_after[0]]

        # Dead leaf: no children, not a word terminus -> tell parent to drop it
        if not child.is_end and len(child.children) == 0:
            return True

        # Single surviving child and not a terminus -> merge labels back
        # together so we don't leave a wasteful pass-through node
        if not child.is_end and len(child.children) == 1:
            (only_grandchild,) = child.children.values()
            only_grandchild.label = child.label + only_grandchild.label
            node.children[first_char] = only_grandchild
            return False

        return False

    # ------------------------------------------------------------------
    # PREFIX SEARCH
    # ------------------------------------------------------------------
    def starts_with(self, prefix: str) -> list[str]:
        node = self.root
        remaining = prefix
        matched = ""

        while remaining:
            first_char = remaining[0]
            if first_char not in node.children:
                return []
            child = node.children[first_char]
            common_len = self._common_prefix_len(remaining, child.label)
            if common_len < len(remaining) and common_len < len(child.label):
                return []
            matched += child.label[:common_len]
            remaining = remaining[common_len:]
            node = child

        results: list[str] = []
        self._collect(node, matched, results)
        return results

    def _collect(self, node: RadixNode, path: str, out: list[str]) -> None:
        if node.is_end:
            out.append(path)
        for first_char in sorted(node.children):
            child = node.children[first_char]
            self._collect(child, path + child.label, out)

    def keys(self) -> list[str]:
        out: list[str] = []
        self._collect(self.root, "", out)
        return out

    @staticmethod
    def _common_prefix_len(a: str, b: str) -> int:
        i = 0
        while i < len(a) and i < len(b) and a[i] == b[i]:
            i += 1
        return i
