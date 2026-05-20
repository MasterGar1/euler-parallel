import matplotlib.pyplot as plt

from sys import exit as sys_exit
from os import cpu_count, path, remove
from argparse import ArgumentParser, Namespace
from csv import DictWriter
from re import Match, search
from subprocess import CompletedProcess, run as subprocess_run

from src.helper import estimate_terms


def parse_args() -> Namespace:
    parser: ArgumentParser = ArgumentParser(
        description="Benchmark parallel calculation of e."
    )
    parser.add_argument(
        "-p", "--precision", type=int, required=True, help="Number of decimal digits."
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=1, help="Optional fixed interval size."
    )
    return parser.parse_args()


def run_benchmark(threads: int, precision: int, interval: int) -> float:
    from sys import executable
    cmd: list[str] = [executable, "main.py", "-t", str(threads), "-p", str(precision), "-i", str(interval)]

    dummy_file: str = "dummy_e.txt"
    cmd.append(dummy_file)

    result: CompletedProcess = subprocess_run(
        cmd, capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"Error running benchmark for {threads} threads:")
        print(result.stderr)
        sys_exit(1)

    # Извличане на времето за изчисление от stdout
    match: Match | None = search(
        r"Calculation time:\s+([0-9.]+)", result.stdout
    )
    if not match:
        print("Could not parse calculation time from output.")
        print("Output was:\n", result.stdout)
        sys_exit(1)

    if path.exists(dummy_file):
        remove(dummy_file)

    return float(match.group(1))


def main():
    args: Namespace = parse_args()
    max_threads: int = cpu_count() or 1

    print("Starting benchmark (3 runs per configuration)...")
    print(f"Precision: {args.precision}")
    interval_str: str = str(args.interval) if args.interval else "Auto"
    print(f"Interval size: {interval_str}")
    print(f"Taylor series terms: {estimate_terms(args.precision)}")
    print(f"Max system threads: {max_threads}")
    print("-" * 105)

    results: list[dict] = []

    def bench_runs(t: int):
        times = []
        for run in range(3):
            times.append(run_benchmark(t, args.precision, args.interval))
        return times

    # Пускане с 1 нишка за получаване на базова линия за ускорението
    print("Running baseline (1 thread)...")
    base_times: list[int] = bench_runs(1)
    best_base_time: int = min(base_times)

    results.append(
        {
            "threads": 1,
            "times": base_times,
            "best_time": best_base_time,
            "speedup": 1.0,
            "efficiency": 1.0,
        }
    )

    # Увеличаване на нишките до max_threads
    current_threads = 2
    while current_threads <= max_threads:
        print(f"Running with {current_threads} threads...")
        calc_times: list[int] = bench_runs(current_threads)
        best_time: int = min(calc_times)
        speedup: float = best_base_time / best_time
        efficiency: float = speedup / current_threads

        results.append(
            {
                "threads": current_threads,
                "times": calc_times,
                "best_time": best_time,
                "speedup": speedup,
                "efficiency": efficiency,
            }
        )

        current_threads += 2

    # Записване в CSV
    csv_filename: str = f"results/benchmark_p-{args.precision}_i-{interval_str}.csv"
    with open(csv_filename, "w", newline="") as csvfile:
        fieldnames = [
            "p",
            "Tp(1)",
            "Tp(2)",
            "Tp(3)",
            "Tp",
            "Sp",
            "Ep",
        ]
        writer: DictWriter = DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "p": r["threads"],
                    "Tp(1)": r["times"][0],
                    "Tp(2)": r["times"][1],
                    "Tp(3)": r["times"][2],
                    "Tp": r["best_time"],
                    "Sp": r["speedup"],
                    "Ep": r["efficiency"],
                }
            )
    print(f"\nSaved benchmark table to {csv_filename}")

    # Генериране на графики
    threads_list = [r["threads"] for r in results]
    speedups = [r["speedup"] for r in results]
    efficiencies = [r["efficiency"] for r in results]

    # Графика на ускорението
    plt.figure(figsize=(10, 6))
    plt.plot(
        threads_list,
        speedups,
        marker="",
        linestyle="-",
        color="b",
        label="Ускорение",
    )

    plt.title(f"Точност: {args.precision}")
    plt.xlabel("Нишки")
    plt.ylabel("Ускорение")
    plt.xticks(threads_list)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    speedup_filename = f"results/speedup_p-{args.precision}_i-{interval_str}.png"
    plt.savefig(speedup_filename)
    plt.close()
    print(f"Saved speedup graph to {speedup_filename}")

    # Графика на ефективността
    plt.figure(figsize=(10, 6))
    plt.plot(
        threads_list,
        efficiencies,
        marker="",
        linestyle="-",
        color="g",
        label="Ефективност",
    )
    plt.title(f"Точност: {args.precision}")
    plt.xlabel("Нишки")
    plt.ylabel("Ефективност")
    plt.xticks(threads_list)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    efficiency_filename = f"results/efficiency_p-{args.precision}_i-{interval_str}.png"
    plt.savefig(efficiency_filename)
    plt.close()
    print(f"Saved efficiency graph to {efficiency_filename}")


if __name__ == "__main__":
    main()
