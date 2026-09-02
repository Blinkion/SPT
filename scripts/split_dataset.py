#!/usr/bin/env python3
"""Deterministically split a JSONL corpus into train/validation/test files."""

from __future__ import annotations

import argparse
import gzip
import math
import random
from pathlib import Path


SPLITS = ("train", "validation", "test")
WEIGHTS = (7, 2, 1)


def allocate_counts(total: int) -> tuple[int, int, int]:
    """Allocate records by largest remainder for an exact 7:2:1 total."""
    exact = [total * weight / sum(WEIGHTS) for weight in WEIGHTS]
    counts = [math.floor(value) for value in exact]
    remainder_order = sorted(
        range(len(SPLITS)),
        key=lambda index: (exact[index] - counts[index], -index),
        reverse=True,
    )
    for index in remainder_order[: total - sum(counts)]:
        counts[index] += 1
    return counts[0], counts[1], counts[2]


def collect_offsets(input_path: Path) -> list[int]:
    offsets: list[int] = []
    with input_path.open("rb") as source:
        while True:
            offset = source.tell()
            line = source.readline()
            if not line:
                break
            if line.strip():
                offsets.append(offset)
    return offsets


def write_split(
    source,
    offsets: list[int],
    output_path: Path,
) -> None:
    with output_path.open("wb") as raw_output:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw_output,
            mtime=0,
        ) as output:
            for offset in offsets:
                source.seek(offset)
                output.write(source.readline())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Source JSONL file")
    parser.add_argument("output_dir", type=Path, help="Destination directory")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    offsets = collect_offsets(args.input)
    random.Random(args.seed).shuffle(offsets)
    counts = allocate_counts(len(offsets))

    args.output_dir.mkdir(parents=True, exist_ok=True)
    start = 0
    with args.input.open("rb") as source:
        for split, count in zip(SPLITS, counts, strict=True):
            end = start + count
            output_path = args.output_dir / f"{split}.jsonl.gz"
            write_split(source, offsets[start:end], output_path)
            print(f"{split}: {count} records -> {output_path}")
            start = end


if __name__ == "__main__":
    main()
