# Why the Skip List Print Loop Gets Stuck

The current implementation stores one shared pointer, `Node.next`, on each node. A skip list needs a separate forward pointer for every level.

This deterministic example forces `_level()` to return these values:

| Node | Score | Assigned level |
|---|---:|---:|
| A | 10 | 1 |
| B | 5 | 2 |
| C | 3 | 2 |
| D | 20 | 2 |

## Empty Skip List

```text
levels[0] = None
levels[1] = None
levels[2] = None
levels[3] = None
```

## Insert A, Level 1

```text
levels[0] -> A -> None
```

`A.next` is `None`, so printing finishes.

## Insert B, Level 2

`B` is added to levels 1 and 0:

```text
levels[1] -> B -> None
levels[0] -> A -> B -> None
```

The shared pointers are:

```text
A.next = B
B.next = None
```

Printing still finishes.

## Insert C, Level 2

`C` is appended to both lanes:

```text
levels[1] -> B -> C -> None
levels[0] -> A -> B -> C -> None
```

The shared pointers are:

```text
A.next = B
B.next = C
C.next = None
```

Printing still finishes.

## Insert D, Level 2

Before inserting `D`, the relevant lanes are:

```text
levels[1] -> B -> C -> None
levels[0] -> A -> B -> C -> None
```

The loop processes `i = 1` first. It walks to `C` and executes line 147:

```python
temp.next = node
```

Because `node` is `D`, the pointers become:

```text
C.next = D
D.next = None
```

The level-1 lane temporarily looks correct:

```text
levels[1] -> B -> C -> D -> None
```

Next, the loop processes `i = 0`. It follows the shared `next` pointers:

```text
temp = A
temp = B
temp = C
temp = D
```

At this point `temp` is already the node being inserted. The same line runs again:

```python
temp.next = node
```

This is equivalent to:

```python
D.next = D
```

The node now points to itself:

```text
D -> D -> D -> D -> ...
```

## Why Two Nodes Do Not Hang

With only `A` and `B`, the final append is simply:

```python
A.next = B
```

`temp` is `A`, while `node` is `B`, so no self-cycle is created. The bug requires a node already reached through one level to be reused as the tail of another level. Three or four insertions can expose it, depending on the randomly assigned levels.

## Why Printing Hangs

The printer uses:

```python
while temp.next is not None:
    temp = temp.next
```

After `D.next = D`, `temp` remains `D` forever. `temp.next` is always non-`None`, so the loop never terminates.

## Root Cause: The Lists Are Not Independent

Although `self.levels` contains four head pointers, the nodes do not contain four independent links. Every level follows the same field:

```python
self.next: Node | None = None
```

Therefore changing a node's link on level 1 also changes the link seen on level 0.

For independent skip-list lanes, each node needs one forward pointer per level, for example:

```python
self.levels: list[Node | None] = [None] * level
```

Then traversal and insertion at level `i` must use `temp.levels[i]`, not `temp.next`. Four head pointers alone are not enough; the links between the nodes must also be independent.
