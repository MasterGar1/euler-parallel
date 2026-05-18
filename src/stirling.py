from os import cpu_count
from math import log
from typing import List, Tuple


def estimate_terms(precision: int) -> int:
    """Оценка на броя членове на реда на Тейлър, необходими за дадена десетична точност."""
    if precision < 1:
        raise ValueError("Precision must be at least 1.")
    if precision == 1:
        return 4  # e = 2.718... so 4 terms gives a good approximation for 1 digit
    n: int = round(precision / log(precision, 10))
    return max(n, 1)


def validate_threads(threads: int, terms: int) -> int:
    """Проверка на броя нишки и ограничаване според CPU ядрата."""
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
    terms: int, threads: int, interval: int | None = None
) -> List[Tuple[int, int]]:
    """
    Разпределя [0, 1, ..., terms-1] в интервали за нишките.
    Ако е зададен интервал, използва части с еднакъв размер.
    В противен случай използва пропорционално разпределение, където cost(k) = k+1.
    """
    if interval is not None:
        # Потребителски зададен интервал: части с еднакъв размер
        inter: List[Tuple[int, int]] = []
        beg: int = 0
        while beg < terms:
            end: int = min(beg + interval, terms)
            inter.append((beg, end))
            beg = end
        return inter

    # Пропорционално разпределение на работата:
    # cost(k) = k+1 (изчисляването на k! отнема ~k+1 умножения на големи цели числа)
    # Искаме да зададем последователни диапазони, така че кумулативната цена на нишка да е балансирана.
    # Обща цена = sum(k+1 for k in range(terms)) = terms*(terms+1)/2
    total_cost: int = terms * (terms + 1) // 2
    target_cost: float = total_cost / threads

    intervals: List[Tuple[int, int]] = []
    start: int = 0
    current_cost: int = 0

    for k in range(terms):
        cost = k + 1
        # Ако добавянето на този член надвиши целта и все още имаме нужда от повече нишки
        if current_cost > 0 \
        and current_cost + cost > target_cost \
        and len(intervals) < threads - 1:
            intervals.append((start, k))
            start = k
            current_cost = cost
        else:
            current_cost += cost

    # Добавяне на последния интервал, покриващ оставащите членове
    if start < terms:
        intervals.append((start, terms))

    # Допълване с празни интервали ако е необходимо (не би трябвало да се случи с разумни входни данни)
    while len(intervals) < threads:
        intervals.append((terms, terms))

    return intervals[:threads]
