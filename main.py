from sys import stderr, exit as sys_exit
from time import perf_counter_ns
from argparse import ArgumentParser, Namespace
from decimal import Decimal, getcontext
from queue import Queue
from typing import List, Tuple

from src.helper import distribute_work, estimate_terms, validate_threads
from src.worker import Worker


def parse_args() -> Namespace:
    """Анализира аргументите от командния ред за паралелното изчисление на e."""
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
        default=1,
        help="Number of intervals per thread. Higher = finer granularity. Defaults to 1.",
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


def setup(threads_count: int, precision: int, interval: int):
    """Подготвя работниците, опашките и интервалите за паралелното изчисление."""
    getcontext().prec = precision + 10
    terms: int = estimate_terms(precision)

    try:
        threads_count = validate_threads(threads_count, terms)
    except ValueError as e:
        print(f"[ERROR] {e}", file=stderr)
        sys_exit(1)

    intervals: List[Tuple[int, int]] = distribute_work(terms, threads_count, interval)

    num_chunks: int = len(intervals)

    queues: List[Queue] = [Queue() for _ in range(num_chunks + 1)]

    workers: List[Worker] = []
    for idx in range(threads_count):
        w: Worker = Worker(
            worker_id=idx,
            threads_count=threads_count,
            intervals=intervals,
            queues=queues,
            precision=precision,
        )
        workers.append(w)

    return workers, queues, intervals, terms, num_chunks, threads_count


def run(workers: List[Worker], queues: List[Queue]):
    """Стартира работниците, предава началната стойност и чака резултат в последната опашка."""
    initial_sum: Decimal = Decimal(1.0)
    initial_term: Decimal = Decimal(1.0)

    for w in workers:
        w.start()

    queues[0].put((initial_sum, initial_term))

    for w in workers:
        w.join()

    final_result = queues[-1].get()

    return final_result


def calculate_e(
    threads_count: int, precision: int, interval: int, quiet: bool = False
) -> dict:
    """Изчислява числото на Ойлер (e) с дадена точност и брой нишки, връща речник с резултат и времена."""
    total_start: int = perf_counter_ns()

    setup_start: int = perf_counter_ns()
    workers, queues, intervals, terms, num_chunks, threads_count = setup(
        threads_count, precision, interval
    )
    setup_end: int = perf_counter_ns()

    if not quiet:
        print(f"[INFO] Calculating e to {precision} decimal places.")
        print(f"[INFO] Taylor series terms: {terms}")
        print(f"[INFO] Using {threads_count} worker(s) in a linear pipeline.")
        avg_granularity: float = terms / num_chunks
        print(
            f"[INFO] Intervals per thread: {interval} ({num_chunks} stages total, ~{avg_granularity:.1f} terms/stage)"
        )
        intervals_str = ", ".join(str(iv) for iv in intervals[:5])
        if len(intervals) > 5:
            intervals_str += f", ... {intervals[-1]}"
        print(f"[INFO] Work intervals: {intervals_str}")

    calc_start: int = perf_counter_ns()
    final_result = run(workers, queues)
    calc_end: int = perf_counter_ns()

    e_value, _ = final_result

    total_end: int = perf_counter_ns()

    return {
        "e_value": e_value,
        "setup_time": setup_end - setup_start,
        "calc_time": calc_end - calc_start,
        "total_time": total_end - total_start,
    }


def main() -> None:
    """Основна функция, която управлява потока от аргументи до резултат."""
    args: Namespace = parse_args()

    threads_count: int = args.threads
    precision: int = args.precision
    interval: int = args.interval
    quiet: bool = args.quiet
    output_file: str = args.file

    result: dict = calculate_e(threads_count, precision, interval, quiet=quiet)

    with open(output_file, "w") as f:
        f.write(str(result["e_value"]))

    if not quiet:
        print(f"Setup time:        {result['setup_time']}")
        print(f"Calculation time:  {result['calc_time']}")
        print(f"Total time:        {result['total_time']}")
        print(f"Result written to: {output_file}")


def entry_point() -> None:
    """Точка на вход за изпълнение на програмата."""
    main()


if __name__ == "__main__":
    entry_point()
