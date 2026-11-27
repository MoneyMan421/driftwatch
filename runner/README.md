# DriftWatch Runner — the free single-suite checker

**Pin a measured baseline once. Run the suite again later. This tool
tells you exactly what moved.**

The runner is one Python file (`driftwatch.py`, standard library
only, Python 3.9+). You give it a *suite config*: a small JSON file
that names a pinned baseline (a Proof Record), the command that
re-runs the suite, how to pull the fresh measurements out of that
command's output, and the tolerances to compare within. The runner
executes the command, extracts the measurements, compares them
against the baseline, and writes the result as a new Proof Record
plus a one-page markdown summary.

It was packaged from the three re-run paths of the first DriftWatch
proof (November 27, 2026), and ships with those three suites as
working examples.

## Run a suite

```bash
cd runner/
python3 driftwatch.py suites/skills-integrity.json
python3 driftwatch.py seam-check        # short form: looks in ./suites/
python3 driftwatch.py framediff
```

Exit codes, so it can sit in a script or CI job:
**0** STABLE · **1** CHANGED · **2** INCONCLUSIVE ·
**3** misconfigured (bad config or missing baseline — no record
written).

## What it writes

Each run creates `out/<suite>/<date>/<time>/` containing:

- `DW-<SUITE>-RUN-<date>-<time>.json` — a Proof Record (Open Door
  Standards, Proof Record v0.3.0): the subject and baseline it
  compared against, the fresh measurements with their deltas against
  the baseline values, the verdict, and a `body_sha256` seal computed
  the same way as every other Proof Record in the stack (SHA-256 of
  the record serialised with sorted keys and compact separators,
  excluding the seal itself — recompute it and any later edit shows).
- `summary.md` — the human-readable drift summary: STABLE, CHANGED
  (naming the measurements that moved) or INCONCLUSIVE (with the
  reason), and a table of baseline vs fresh vs delta.
- `raw-cmd<N>.txt` — the raw stdout of each configured command,
  hashed into the record's evidence, so anyone can re-derive the
  numbers the record claims.

A suite whose command fails, whose output cannot be parsed, or
which does not produce a baseline measurement is **INCONCLUSIVE
with the reason stated** — the runner never crashes on a suite and
never invents a number to fill a gap.

## The three shipped suites

| Config | What it re-runs | Baseline |
|---|---|---|
| `suites/skills-integrity.json` | `sha256sum -c MANIFEST.sha256` + `check_install.py` over the Measured Skills release (23 packs) | `proof/record-C-baseline.json` (2026-11-26 delivery) |
| `suites/seam-check.json` | The certified checker `print_check.py --pattern` on the canonical PG4 clean + shifted fixtures | `proof/record-A-baseline.json` (2026-11-17 acceptance) |
| `suites/framediff.json` | `framediff.py` on Two Lights v3-vs-v3 and v3-vs-v1, outside the 6.5–10.0 s window | `proof/record-B-baseline.json` (2026-11-26) |

These configs point at the real assets on this machine (paths under
`~/workspace/...`). On another machine, edit the paths — the format
below is the whole contract.

## Add your own suite

A suite config is one JSON file. Fields:

**Top level**

- `suite` *(required)* — short name; used for the output folder and
  the record ID. Kebab-case by convention.
- `description` — what the suite measures and any limits (e.g. an
  arm it does not cover). Copied nowhere automatically; it is there
  so the next reader understands the config.
- `baseline_record` *(required)* — path to the pinned baseline Proof
  Record. The runner compares against the `measurements` in this
  record, by name, and copies its `subject` into the run record.
  `~` expands to your home directory.
- `commands` *(required)* — a list of command objects, run in order.
- `tolerances` — `default_abs`: the absolute tolerance applied to
  every numeric measurement (0 = exact match). `per_measurement`:
  optional `{name: tolerance}` overrides. `note`: free text saying
  *why* those tolerances — write the reason down; a tolerance
  without a reason is a guess. (The seam-check suite uses ±0.005
  because its baseline was recorded at 2 decimal places: matching
  at the recorded precision is the honest comparison.)

**Each command object**

- `argv` *(required)* — the command as a list of strings, e.g.
  `["python3", "check_install.py"]`. No shell is involved; `~`
  expands in each element.
- `cwd` — working directory for the command (default: where you
  invoked the runner). `~` expands.
- `parse` — `"json"` when stdout is one JSON document, `"text"`
  otherwise (default `"text"`).
- `allow_exit_codes` — exit codes that still count as a measurement
  (default `[0]`). A checker that exits 1 when its subject *fails*
  should list `[0, 1]`: a failing subject is a result, not a runner
  error. Any other exit code makes the run INCONCLUSIVE.
- `timeout_seconds` — per-command timeout (default 900).
- `extract` — a list of extraction specs; each produces one named
  measurement. If two commands extract the same name, the later one
  wins (the skills-integrity suite uses this: the install checker's
  summary line refines the raw hash count).

**Each extraction spec**

- `name` *(required)* — the measurement name. To be compared, it
  must match a measurement name in the baseline record. Names the
  baseline does not carry are reported as *noted* context, never
  compared (the seam-check suite extracts the checker's verdicts
  this way).
- `from` — how to get the value:
  - `"json_path"` — follow a dotted path into the JSON output,
    e.g. `"checks.0.vertical.wrap_ratio"` (numbers index into
    lists). Requires `parse: "json"`.
  - `"count_lines_matching"` — count stdout lines matching the
    regex in `pattern`, e.g. `": OK$"` for a hash check.
  - `"regex"` — take capture group `group` (default 1) of the first
    match of `pattern`; numeric captures become numbers.
- `path` — the dotted path (for `json_path`).
- `pattern` — the regular expression (for the other two kinds).
- `group` — capture group for `regex` (default 1).

To pin a baseline for a new suite, run the suite once by hand and
write its measurements into a Proof Record (the format is the
schema in `open-door-standards/schemas/proof-record.schema.json`;
`proof/build_records.py` in this repo is a worked example of
building records with correct seals).

## Honest scope

The runner runs suites **you** configure, against baselines **you**
pinned, on **this** machine. It does not discover suites, does not
choose tolerances for you, and does not judge whether a change
matters — it reports what moved, by how much, against the baseline
of record. A STABLE verdict means the measurements it compared did
not move beyond the tolerances you set; it does not mean the
subject is good, safe, or correct.

It is a measurement tool, not a warranty.

*By Collin.*
