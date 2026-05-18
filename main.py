from sys import stderr, exit as sys_exit
from time import perf_counter_ns
from argparse import ArgumentParser, Namespace
from decimal import Decimal, getcontext
from queue import Queue
from typing import List, Tuple

from src.stirling import distribute_work, estimate_terms, validate_threads
from src.worker import Worker


def parse_args() -> Namespace:
    parser: ArgumentParser = ArgumentParser(
        description="Паралелно (nogil) изчисление на числото на Ойлер (e) чрез ред на Тейлър."
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=1,
        help="Number of threads to use. Defaults to 1.",
    )
    parser.add_argument(
        "-p",
        "--precision",
        type=int,
        required=True,
        help="Number of decimal digits to approximate accurately.",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=None,
        help="Interval size for each partial sum. If omitted, uses work-proportional distribution.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all output to stdout. Only write the result to the file.",
    )
    parser.add_argument(
        "file",
        type=str,
        default="out.txt",
        help="File path to store the final calculated value.",
    )
    return parser.parse_args()


def main() -> None:
    total_start: int = perf_counter_ns()

    args: Namespace = parse_args()

    threads_count: int = args.threads
    precision: int = args.precision
    interval: int = args.interval
    quiet: bool = args.quiet
    output_file: str = args.file

    # Точност и оценка на членовете
    setup_start: int = perf_counter_ns()
    getcontext().prec = precision + 10
    terms: int = estimate_terms(precision)

    try:
        threads_count = validate_threads(threads_count, terms)
    except ValueError as e:
        if not quiet:
            print(f"[ERROR] {e}", file=stderr)
        sys_exit(1)

    # Разделяне на членовете в интервали за нишките
    intervals: List[Tuple[int, int]] = distribute_work(terms, threads_count, interval)
    actual_threads: int = len(intervals)

    if not quiet:
        print(f"[INFO] Calculating e to {precision} decimal places.")
        print(f"[INFO] Taylor series terms: {terms}")
        print(f"[INFO] Using {actual_threads} thread(s) in a linear pipeline.")
        print(f"[INFO] Granularity: {terms // actual_threads}")
        print(
            f"[INFO] Work intervals: {', '.join(str(interval) for interval in intervals[:5]) + f',{' ...,' if len(intervals) > 6 else ''} {intervals[-1]}' if len(intervals) > 5 else ''}"
        )

    # Създаване по една опашка за връзка на нишка
    queues: List[Queue] = [Queue() for _ in range(actual_threads + 1)]

    # Създаване и конфигуриране на работници
    workers: List[Worker] = []
    for idx in range(actual_threads):
        start_k, end_k = intervals[idx]
        w: Worker = Worker(
            worker_id=idx,
            in_queue=queues[idx],
            out_queue=queues[idx + 1] if idx < actual_threads - 1 else None,
            start_k=start_k,
            end_k=end_k,
        )
        workers.append(w)

    setup_end: int = perf_counter_ns()
    setup_time: int = setup_end - setup_start

    # Изпълнение на изчислението
    calc_start: int = perf_counter_ns()

    # Стартиране на всички нишки. Те ще блокират на своята in_queue докато предишната нишка приключи.
    for w in workers:
        w.start()

    # Подаване на начални стойности в първата опашка за стартиране на pipeline-а
    # Сумата започва от 1.0 (членът k=0, 1/0!), а базата на факториела е 1 (0!)
    initial_sum: Decimal = Decimal(1.0)
    initial_fact: int = 1
    queues[0].put((initial_sum, initial_fact))

    # Изчакване на всички работници да завършат
    for w in workers:
        w.join()

    # Събиране на крайния резултат от последния работник
    final_result = workers[-1].result
    if final_result is None:
        final_result = queues[-1].get()

    calc_end: int = perf_counter_ns()
    calc_time: int = calc_end - calc_start

    total_end: int = perf_counter_ns()
    total_time: int = total_end - total_start

    # Записване на резултата във файл
    e_value, _ = final_result
    with open(output_file, "w") as f:
        f.write(str(e_value))

    # Извеждане на информация за времето
    if not quiet:
        print(f"Setup time:        {setup_time}")
        print(f"Calculation time:  {calc_time}")
        print(f"Total time:        {total_time}")
        print(f"Result written to: {output_file}")


if __name__ == "__main__":
    main()
