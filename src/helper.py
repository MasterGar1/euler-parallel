from os import cpu_count
from math import log
from typing import List, Tuple


def estimate_terms(precision: int) -> int:
    """Оценява броя членове на ред на Тейлър, необходими за постигане на дадена точност."""
    if precision < 1:
        raise ValueError("Precision must be at least 1.")
    if precision == 1:
        return 4
    n: int = round(precision / log(precision, 10))
    return max(n, 1)


def validate_threads(threads: int, terms: int) -> int:
    """Проверява дали броят нишки е валиден и в рамките на позволения максимум."""
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


def distribute_work(terms: int, threads: int, interval: int = 1) -> List[Tuple[int, int]]:
    """
    Разпределя [0, 1, ..., terms-1] в (threads * interval) части,
    така че по-големите индекси (по-скъпи заради растящите факториели)
    да имат по-малка тежест.
    """
    if interval < 1:
        raise ValueError("Interval must be at least 1.")

    total_chunks: int = threads * interval
    if total_chunks > terms:
        total_chunks = terms

    weights: List[int] = [total_chunks - i for i in range(total_chunks)]
    total_weight: int = sum(weights)

    intervals: List[Tuple[int, int]] = []
    current: int = 0
    for i in range(total_chunks):
        size: int = max(1, int((weights[i] / total_weight) * terms))
        if current + size > terms:
            size = terms - current
        if size > 0:
            intervals.append((current, current + size))
            current += size
        if current >= terms:
            break

    if current < terms:
        if intervals:
            last_start, _ = intervals[-1]
            intervals[-1] = (last_start, terms)
        else:
            intervals.append((0, terms))

    return intervals
