from sys import stderr, exit as sys_exit
from time import perf_counter_ns
from argparse import ArgumentParser, Namespace
from decimal import Decimal, getcontext
from queue import Queue
from typing import List, Tuple

from src.helper import distribute_work, estimate_terms, validate_threads
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


def main() -> None:
    total_start: int = perf_counter_ns()

    args: Namespace = parse_args()

    threads_count: int = args.threads
    precision: int = args.precision
    interval: int = args.interval
    quiet: bool = args.quiet
    output_file: str = args.file

    setup_start: int = perf_counter_ns()
    getcontext().prec = precision + 10
    terms: int = estimate_terms(precision)

    try:
        threads_count = validate_threads(threads_count, terms)
    except ValueError as e:
        if not quiet:
            print(f"[ERROR] {e}", file=stderr)
        sys_exit(1)

    intervals: List[Tuple[int, int]] = distribute_work(terms, threads_count, interval)

    num_chunks: int = len(intervals)
    if not quiet:
        print(f"[INFO] Calculating e to {precision} decimal places.")
        print(f"[INFO] Taylor series terms: {terms}")
        print(f"[INFO] Using {threads_count} worker(s) in a linear pipeline.")
        avg_granularity: float = terms / num_chunks
        print(f"[INFO] Intervals per thread: {interval} ({num_chunks} stages total, ~{avg_granularity:.1f} terms/stage)")
        intervals_str = ", ".join(str(iv) for iv in intervals[:5])
        if len(intervals) > 5:
            intervals_str += f", ... {intervals[-1]}"
        print(f"[INFO] Work intervals: {intervals_str}")

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

    setup_end: int = perf_counter_ns()
    setup_time: int = setup_end - setup_start

    calc_start: int = perf_counter_ns()

    for w in workers:
        w.start()

    initial_sum: Decimal = Decimal(1.0)
    initial_term: Decimal = Decimal(1.0)
    queues[0].put((initial_sum, initial_term))

    for w in workers:
        w.join()

    final_result = queues[-1].get()

    calc_end: int = perf_counter_ns()
    calc_time: int = calc_end - calc_start

    total_end: int = perf_counter_ns()
    total_time: int = total_end - total_start

    e_value, _ = final_result
    with open(output_file, "w") as f:
        f.write(str(e_value))

    if not quiet:
        print(f"Setup time:        {setup_time / 1e9}")
        print(f"Calculation time:  {calc_time / 1e9}")
        print(f"Total time:        {total_time / 1e9}")
        print(f"Result written to: {output_file}")


if __name__ == "__main__":
    main()
