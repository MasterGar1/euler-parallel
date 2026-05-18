# Parallel Calculation of Euler's Number (e) — Free-Threaded Python 3.14

Computes Euler's number `e` to an arbitrary number of decimal places using the Taylor series, parallelized across multiple threads in Python 3.14's free-threaded (no-GIL) mode.

## How It Works

### Taylor Series

Euler's number is defined as:

```
e = 1/0! + 1/1! + 1/2! + 1/3! + ... + 1/n! + ...
```

Each term requires computing `k!` — an increasingly expensive arbitrary-precision integer operation. The number of terms needed for a given decimal precision `p` is estimated via Stirling's approximation:

```python
n ≈ round(p / log(p, 10))
```

### Parallelization Strategy

Three techniques work together:

#### 1. Cost-Proportional Work Distribution

Terms are **not** split into equal-sized chunks. Since computing term `k` costs `k+1` big-integer multiplications, the distribution algorithm scans forward and groups terms so each thread has approximately the same **total computational cost** (not the same number of terms). A fixed interval size can also be provided via `-i`.

#### 2. Factored Local Computation (Mathematical Trick)

Each thread computes its partial sum **independently** of all others before synchronising:

For a thread handling terms `[start, end)`:
- `local_mult = (start+1) × (start+2) × ... × end`
- `local_sum = 1/(start+1)! + 1/(start+2)! + ... + 1/end!`

This works because:

```
1/k! = (1/start!) × (1 / ((start+1) × (start+2) × ... × k))
```

Once the previous thread's `base_fact` arrives, a single O(1) combination merges the results:

```python
true_sum = previous_sum + (local_sum / Decimal(base_fact))
true_fact = base_fact * local_mult
```

This avoids serialising on factorial computation — the expensive big-integer work runs fully in parallel.

#### 3. Linear Pipeline Topology

Threads are arranged as a **pipeline** connected by thread-safe `queue.Queue` objects:

```
Queue[0] → Worker[0] → Queue[1] → Worker[1] → ... → Queue[N] → Worker[N-1]
```

- All workers start simultaneously and immediately begin their local sums.
- After finishing local work, each worker blocks on `in_queue.get()` waiting for the upstream partial result.
- The combination step is instantaneous (one division, one multiplication, one addition).
- The first queue is seeded with `(sum=1.0, fact=1)` representing term 0.
- The final worker stores the complete result.

### Why Python 3.14 Free-Threaded Matters

Before the free-threaded (no-GIL) build of Python 3.13+, the Global Interpreter Lock would serialise CPU-bound Python threads, making this approach pointless. With the GIL disabled (`PYTHON_GIL=0`), `threading.Thread` workers can run true parallel computation on multiple cores, making this pipeline effective.

## Usage

### Prerequisites

- Python 3.14 (free-threaded build) or Python ≥3.13 with `PYTHON_GIL=0`
- Install dependencies: `pip install -r requirements.txt`

### Basic Computation

```bash
python main.py -p 10000
```

Calculates `e` to 10,000 decimal places and writes the result to `out.txt`.

### Options

| Argument | Description |
|---|---|
| `-p, --precision` | Decimal digits of accuracy (required) |
| `-t, --threads` | Number of worker threads (default: 1) |
| `-i, --interval` | Fixed interval size per thread; omitting uses automatic cost-proportional distribution |
| `-q, --quiet` | Suppress stdout output |
| `file` | Output file path (default: `out.txt`) |

### Disable the GIL (Python 3.13+)

On a free-threaded build, the GIL is off by default. For earlier interpreters:

```bash
PYTHON_GIL=0 python main.py -p 10000 -t 8
```

### Examples

```bash
# 10,000 digits with 8 threads, auto-balanced workload
python main.py -p 10000 -t 8

# 50,000 digits with fixed intervals of 500 terms per chunk
python main.py -p 50000 -t 16 -i 500

# Quiet mode, custom output file
python main.py -p 100000 -t 32 -q e_100k.txt
```

## Benchmarking

A built-in benchmark runner measures speedup and efficiency across thread counts:

```bash
python benchmark.py -p 10000
```

Runs `main.py` at 1, 2, 4, 6, ... up to `cpu_count()` threads (3 runs each), then:

- Writes a CSV table to `results/benchmark_p-{precision}_i-{interval}.csv`
- Saves a **speedup** plot to `results/speedup_p-{precision}_i-{interval}.png`
- Saves an **efficiency** plot to `results/efficiency_p-{precision}_i-{interval}.png`

Columns in the CSV:

| Column | Meaning |
|--------|---------|
| `p` | Number of threads |
| `Tp(1)`, `Tp(2)`, `Tp(3)` | Measured runtime for each of 3 runs |
| `Tp` | Best (minimum) runtime |
| `Sp` | Speedup = T(1) / T(p) |
| `Ep` | Efficiency = Sp / p |

### Example Benchmark

```bash
python benchmark.py -p 10000
```

## Project Layout

```
.
├── main.py              # Entry point: argument parsing, pipeline setup, timing
├── benchmark.py         # Automated benchmark: runs, CSV tables, PNG plots
├── src/
│   ├── stirling.py      # Term estimation, thread validation, work distribution
│   └── worker.py        # Worker thread implementing factored local computation
├── results/             # Output CSV tables and speedup/efficiency graphs
├── out.txt              # Default result file
├── requirements.txt     # Python dependencies (matplotlib for benchmarking)
└── README.md
```

## Dependencies

- **Python 3.13+** — stdlib only for the computation (`decimal`, `threading`, `queue`)
- **matplotlib** — required only for `benchmark.py` to generate plots (see `requirements.txt`)

```bash
pip install -r requirements.txt
```

## Notes

- `Decimal` precision is set to `precision + 10` guard digits to absorb rounding errors.
- Thread count is automatically capped at `cpu_count()`. A warning is issued if the requested count exceeds available cores, but execution continues.
- If the requested thread count exceeds the number of Taylor terms, a hard error is raised.
