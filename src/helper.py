from os import cpu_count
from math import log
from typing import List, Tuple


def estimate_terms(precision: int) -> int:
    if precision < 1:
        raise ValueError("Precision must be at least 1.")
    if precision == 1:
        return 4
    n: int = round(precision / log(precision, 10))
    return max(n, 1)


def validate_threads(threads: int, terms: int) -> int:
    max_threads: int = cpu_count() or 1
    if threads < 1:
        raise ValueError("Thread count must be at least 1.")
    if threads > terms:
        raise ValueError(
            f"Thread count ({threads}) exceeds number of terms ({terms}). Reduce thread count."
        )
    if threads > max_threads:
        print(
            f"[WARN] Requested threads ({threads}) > CPU cores ({max_threads}). Continuing anyway."
        )
    return threads


def distribute_work(
    terms: int, threads: int, interval: int = 1
) -> List[Tuple[int, int]]:
    """
    Разпределя [0, 1, ..., terms-1] в (threads * interval) части
    с приблизително еднаква изчислителна цена (по-големите получават
    по-малко членове, защото са по-скъпи).
    """
    if interval < 1:
        raise ValueError("Interval must be at least 1.")

    total_chunks: int = threads * interval
    if total_chunks > terms:
        total_chunks = terms

    intervals: List[Tuple[int, int]] = []
    for i in range(total_chunks):
        start: int = int(terms * i / total_chunks)
        end: int = int(terms * (i + 1) / total_chunks)
        if end > start:
            intervals.append((start, end))

    return intervals
