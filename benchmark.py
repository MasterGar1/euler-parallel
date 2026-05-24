import matplotlib.pyplot as plt
from os import cpu_count
from argparse import ArgumentParser, Namespace
from csv import DictWriter

from main import calculate_e
from src.helper import estimate_terms


def parse_args() -> Namespace:
    """Анализира аргументите от командния ред за бenchmark-а."""
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
    """Изпълнява паралелното изчисление на e с дадения брой нишки и измерва времето."""
    result = calculate_e(threads, precision, interval, quiet=True)
    return float(result["calc_time"])


def main():
    """Основна функция за изпълнение на benchmark-а, включително запис в CSV и генериране на графики."""
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
    print("Running baseline...")
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
    threads_list: list[int] = [r["threads"] for r in results]
    speedups: list[float] = [r["speedup"] for r in results]
    efficiencies: list[float] = [r["efficiency"] for r in results]

    # --- Графика на изчислителното време (Compute Time) ---
    plt.figure(figsize=(12, 7))

    best_times: list[float] = [r["best_time"] / 1e9 for r in results]
    plt.plot(
        threads_list,
        best_times,
        marker="",
        linestyle="-",
        color="red",
        linewidth=2,
        label="Tp",
    )

    for run_idx in range(3):
        run_times: list[float] = [r["times"][run_idx] / 1e9 for r in results]
        plt.plot(
            threads_list,
            run_times,
            marker="",
            linestyle="--",
            label=f"Tp({run_idx + 1})",
            linewidth=1,
            alpha=0.6,
        )

    plt.title(f"Изчислително време при n = {args.precision}")
    plt.xlabel("Брой нишки")
    plt.ylabel("Време (s)")
    plt.xticks(threads_list)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    compute_filename: str = f"results/compute_p-{args.precision}_i-{interval_str}.png"
    plt.savefig(compute_filename)
    plt.close()
    print(f"Saved compute time graph to {compute_filename}")

    # --- Графика на ускорението (Speedup) ---
    plt.figure(figsize=(12, 7))
    plt.plot(
        threads_list,
        speedups,
        marker="",
        linestyle="-",
        color="r",
        linewidth=2,
        label="Sp",
    )

    plt.title(f"Ускорение при n = {args.precision}")
    plt.xlabel("Брой нишки")
    plt.ylabel("Ускорение")
    plt.xticks(threads_list)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    speedup_filename: str = f"results/speedup_p-{args.precision}_i-{interval_str}.png"
    plt.savefig(speedup_filename)
    plt.close()
    print(f"Saved speedup graph to {speedup_filename}")

    # --- Графика на ефективността (Efficiency) ---
    plt.figure(figsize=(12, 7))
    plt.plot(
        threads_list,
        efficiencies,
        marker="",
        linestyle="-",
        color="r",
        linewidth=2,
        label="Ep",
    )

    plt.title(f"Ефективност при n = {args.precision}")
    plt.xlabel("Брой нишки")
    plt.ylabel("Ефективност")
    plt.xticks(threads_list)
    plt.grid(True, linestyle=":", alpha=0.6)
    plt.legend()
    efficiency_filename: str = f"results/efficiency_p-{args.precision}_i-{interval_str}.png"
    plt.savefig(efficiency_filename)
    plt.close()
    print(f"Saved efficiency graph to {efficiency_filename}")


if __name__ == "__main__":
    main()
