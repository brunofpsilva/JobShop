"""Valida um horário job shop produzido por JobshopSequencial/JobshopParalelo.

Uso:  jobshop.exe input.txt > out.txt
      python tools/validate.py input.txt out.txt
      python tools/validate.py --selftest

Lê a secção "Solution" do stdout (linhas "Job k | i: <início>  e: <fim> |...")
e verifica duração, ordem das operações de cada job e sobreposição por máquina.
Sai com código 1 se o horário for inválido.
"""
import re
import sys


def read_instance(text):
    nums = list(map(int, text.split()))
    n_jobs, n_machines = nums[0], nums[1]
    pairs = nums[2:]
    if len(pairs) != n_jobs * n_machines * 2:
        raise ValueError("input: esperados %d números após o cabeçalho, lidos %d"
                         % (n_jobs * n_machines * 2, len(pairs)))
    # jobs[j] = [(máquina, duração), ...] pela ordem do job
    return [[(pairs[2 * (j * n_machines + k)], pairs[2 * (j * n_machines + k) + 1])
             for k in range(n_machines)] for j in range(n_jobs)]


def read_schedule(text):
    rows = {}
    for m in re.finditer(r"^Job (\d+) \|(.*)$", text, re.M):
        rows[int(m.group(1))] = [(int(a), int(b)) for a, b in re.findall(r"i: (-?\d+)\s+e: (-?\d+)", m.group(2))]
    return [rows[j] for j in sorted(rows)]


def validate(jobs, schedule):
    """Devolve (makespan, lista de erros)."""
    errors = []
    if len(schedule) != len(jobs) or any(len(s) != len(j) for s, j in zip(schedule, jobs)):
        return None, ["horário com dimensões diferentes do input"]
    by_machine = {}
    for j, (ops, times) in enumerate(zip(jobs, schedule)):
        prev_end = 0
        for k, ((machine, dur), (start, end)) in enumerate(zip(ops, times)):
            if start < 0 or end - start != dur:
                errors.append("J%d op%d: [%d,%d) não tem duração %d" % (j, k, start, end, dur))
            if start < prev_end:
                errors.append("J%d op%d começa em %d antes da op anterior acabar (%d)" % (j, k, start, prev_end))
            prev_end = end
            by_machine.setdefault(machine, []).append((start, end, j, k))
    for machine, ivs in sorted(by_machine.items()):
        ivs.sort()
        for (s1, e1, j1, k1), (s2, e2, j2, k2) in zip(ivs, ivs[1:]):
            if s2 < e1:
                errors.append("M%d: J%d op%d [%d,%d) sobrepõe J%d op%d [%d,%d)" % (machine, j1, k1, s1, e1, j2, k2, s2, e2))
    makespan = max(end for times in schedule for _, end in times)
    return makespan, errors


def selftest():
    jobs = read_instance("2 2  0 3 1 2  0 2 1 1")
    ok = [[(0, 3), (3, 5)], [(3, 5), (5, 6)]]
    assert validate(jobs, ok) == (6, [])
    assert any("sobrepõe" in e for e in validate(jobs, [[(0, 3), (3, 5)], [(2, 4), (5, 6)]])[1])
    assert any("antes da op anterior" in e for e in validate(jobs, [[(0, 3), (2, 4)], [(3, 5), (5, 6)]])[1])
    assert any("duração" in e for e in validate(jobs, [[(0, 4), (4, 6)], [(4, 6), (6, 7)]])[1])
    assert read_schedule("Job 0 | i: 0  e: 3 |i: 3  e: 5 |\nJob 1 | i: 3  e: 5 |i: 5  e: 6 |\n") == ok
    print("selftest OK")


def main(argv):
    if argv[1:] == ["--selftest"]:
        return selftest()
    if len(argv) != 3:
        sys.exit(__doc__)
    with open(argv[1]) as f:
        jobs = read_instance(f.read())
    with open(argv[2], errors="replace") as f:
        schedule = read_schedule(f.read())
    makespan, errors = validate(jobs, schedule)
    for e in errors:
        print("ERRO:", e)
    print("%s  makespan=%s  %s" % (argv[1], makespan, "INVÁLIDO" if errors else "válido"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main(sys.argv)
