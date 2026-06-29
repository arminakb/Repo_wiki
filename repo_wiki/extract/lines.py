from __future__ import annotations


def line_offsets(text: str) -> list[int]:
    offsets = [0]
    for index, char in enumerate(text):
        if char == "\n":
            offsets.append(index + 1)
    return offsets


def line_for_offset(offsets: list[int], offset: int) -> int:
    line = 1
    for idx, start in enumerate(offsets, start=1):
        if start > offset:
            break
        line = idx
    return line
