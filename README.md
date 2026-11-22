# JobShop

Sequential and OpenMP-parallel versions of a simple heuristic for the job shop scheduling problem.

In a job shop, several jobs run on several machines. Each job is a sequence of operations that must run in order, and each operation needs one specific machine for a given time. The goal is to minimise the makespan, the time until every job is finished. Constraints:

- An operation can't start until the previous operation of its job is finished.
- A machine runs one operation at a time.
- An operation, once started, runs to completion.

Reference: https://developers.google.com/optimization/scheduling/job_shop

## Compile

From the repository root:

```
gcc sequential/JobshopSequencial.c -o jobshop_seq.exe
gcc -fopenmp parallel/JobshopParalelo.c -o jobshop_par.exe
```

## Run

```
./jobshop_seq.exe parallel/jobshop.txt
./jobshop_par.exe parallel/jobshop.txt
```

The schedule is printed to stdout (`i:` start, `e:` end for each operation), and start times are written to `output.txt`.

Input format: first line `<jobs> <machines>`, then one line per job with `<machine> <duration>` pairs in the order the job runs them. `sequential/` and `parallel/` hold identical copies of the inputs.

## How it works

The heuristic schedules the operations column by column, where column `k` is the k-th operation of every job:

1. Every operation in column `k` starts at `maxEndTime`, the latest end time of any operation in columns `0..k-1`. That keeps each job's operations in order.
2. If two operations in the same column need the same machine, the second one starts when the first one ends.
3. After the column, `maxEndTime` is updated and every machine is marked free again.

Columns are separated by a barrier, so machines are never shared across columns. This means every schedule is valid, but machines sit idle while a column waits for its slowest operation, so the makespan is far from optimal.

**Parallel version:** one OpenMP thread per job (`num_threads(nrJobs)`). For each column, each thread places its own job's operation inside `#pragma omp critical`, then waits at `#pragma omp barrier`. A single thread (`#pragma omp single`) updates `maxEndTime` and resets the machines. The implicit barrier at the end of `single` keeps the other threads from starting the next column until that reset is done. The order in which threads enter the critical section changes which job goes first on a shared machine, but not the makespan.

## Validation

`tools/validate.py` checks a schedule printed by either program. It confirms that each operation's `end - start` equals its duration, that every job runs its operations in order, and that no two operations overlap on the same machine. It exits with code 1 if the schedule is invalid.

```
./jobshop_par.exe parallel/jobshop3.txt > out.txt
python tools/validate.py parallel/jobshop3.txt out.txt
python tools/validate.py --selftest
```

Both versions produce valid schedules with identical makespans on all three inputs. The parallel version was validated on 200 runs per input.

| Input | Instance | Size (jobs × machines) | Makespan (this heuristic) | Best known (optimal) |
|---|---|---|---|---|
| `jobshop.txt` | OR-Tools example | 3 × 3 | 13 | 11 |
| `jobshop2.txt` | FT06 | 6 × 6 | 86 | 55 |
| `jobshop3.txt` | FT10 | 10 × 10 | 1838 | 930 |

## Measured time

These are the times each program reports itself: the median of 50 runs on a 16-thread Windows 11 machine, built with MinGW-w64 GCC 13.2 and no optimisation flags.

| Input | Sequential | Parallel |
|---|---|---|
| `jobshop.txt` | < 1 ms | 0 ms (max 1 ms) |
| `jobshop2.txt` | < 1 ms | 1 ms |
| `jobshop3.txt` | < 1 ms | 2 ms (max 12 ms) |

On Windows, both clocks only tick in 1 ms steps, so the sequential runs show 0. On these input sizes the parallel version is slower than the sequential one, because creating the threads and synchronising them at the barrier costs more than the scheduling work itself.

Project from Master Degree in Informatics Engineering 2022.
