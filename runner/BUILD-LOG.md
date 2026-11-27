# DriftWatch Runner — Build Log

**Build date:** 2026-11-27 (America/Phoenix)
**Builder:** Mira (subagent run, local only — no GitHub writes)
**Task:** package the three re-run paths from the first DriftWatch
proof (`../proof/RUN-LOG.md`) into a free single-suite runner an
outside user can pick up and run twice.

## Checkpoint 1 — sources read (16:08 UTC)

- `../proof/RUN-LOG.md` — the three suite procedures, commands and
  outcomes (A STABLE / app arm inconclusive, B CHANGED, C STABLE).
- `../proof/build_records.py` — the body_sha256 convention to match:
  SHA-256 of the record serialised as JSON with sorted keys, compact
  separators, `ensure_ascii=False`, excluding the `body_sha256`
  field itself.
- `~/workspace/open-door-standards/schemas/proof-record.schema.json`
  — Proof Record schema v0.3.0 (required: record_id, record_type,
  standard, subject, method, verdict, issued_by, issued_at,
  body_sha256).
- The three baseline records (`../proof/record-{A,B,C}-baseline.json`)
  and the raw outputs in `../proof/raw/` — these fix the measurement
  names and the extraction formats:
  - A: `print_check.py --pattern --json` → `checks[0].{vertical,
    horizontal}.{wrap_ratio,de_excess}` per fixture, 8 measurements,
    baseline recorded at 2 dp.
  - B: `framediff.py A B --start 6.5 --end 10.0 --json` →
    `mad_max / mad_mean / mad_median / frames_with_mad_over_5`,
    two runs (v3-vs-v3 self, v3-vs-v1 cross), 6 measurements.
  - C: `sha256sum -c MANIFEST.sha256` (count `: OK` lines) +
    `python3 check_install.py` (parse the "Checked all packs: N OK,
    N missing, N changed, N extra (of N files)" line), 5 measurements.
- Tool CLIs verified: `print_check.py --help` (image positional,
  `--print-width-mm/--print-height-mm` required, `--pattern`,
  `--json`); `framediff.py` (video_a, video_b, `--start`, `--end`,
  `--json`). `jsonschema` 4.10.3 is available in this environment
  for validating emitted records during the self-test (the runner
  itself is stdlib-only and does not depend on it).

Next: write `driftwatch.py`.

## Checkpoint 2 — runner and configs written

- `driftwatch.py` — single-file, stdlib only. Loads a suite config,
  loads the pinned baseline Proof Record, runs the configured
  commands, extracts fresh measurements (`json_path`,
  `count_lines_matching`, `regex`), compares against the baseline
  within tolerances, and writes a Proof Record + `summary.md` under
  `out/<suite>/<date>/<time>/`. Command failure, unparseable output
  or a missing baseline measurement → INCONCLUSIVE with the reason,
  never a crash and never an invented number. Exit codes: 0 STABLE,
  1 CHANGED, 2 INCONCLUSIVE, 3 misconfigured (no record written).
  `body_sha256` computed exactly as `build_records.py` does (sorted
  keys, compact separators, field excluded, then verified by
  recomputation in the self-test below).
- `suites/skills-integrity.json` — sha256sum + check_install.py in
  `~/workspace/measured-skills`, exact-match tolerances, baseline
  `record-C-baseline.json`.
- `suites/seam-check.json` — print_check.py on both PG4 fixtures,
  tolerance ±0.005 (the baseline's recorded 2 dp precision), baseline
  `record-A-baseline.json`; the checker's verdicts are extracted as
  noted context (they are not measurements in the baseline record).
- `suites/framediff.json` — framediff.py v3-vs-v3 and v3-vs-v1,
  exact-statistic tolerances, baseline `record-B-baseline.json`.

Next: self-test — skills-integrity end-to-end (must reproduce
STABLE), schema-validate the emitted record, then seam-check.

## Checkpoint 3 — self-tests: skills-integrity and seam-check

**skills-integrity (required self-test):**
`python3 driftwatch.py suites/skills-integrity.json` →
**STABLE — all 5 compared measurements within tolerance of baseline
DW-C-BASELINE-2026-11-26**, exit 0. The emitted record
(`out/skills-integrity/2026-11-27/160941/DW-SKILLS-INTEGRITY-RUN-2026-11-27-160941.json`)
was validated against the Proof Record schema v0.3.0 with
jsonschema 4.10.3: **PASS**. Its `body_sha256` was recomputed by an
independent snippet using the build_records.py convention:
**matches**. All five measurements (23/23/0/0/0) read "exact match".

**seam-check — first runner run flagged a tolerance edge, fixed:**
the first run (16:09:46) reported CHANGED on the two horizontal wrap
ratios: fresh 0.595 vs baseline 0.60 is a decimal delta of exactly
0.005 (the tolerance), but in binary floating point
0.600 − 0.595 = 0.0050000000000000044, a hair over. That contradicts
the proof's human-verified verdict ("match at recorded precision").
Fix, in `compare()`: the comparison now allows a 1e-9 epsilon that
absorbs representation error only — orders of magnitude below the
precision any of these suites records at, so it cannot mask real
drift. The first run's outputs are left on disk under
`out/seam-check/2026-11-27/160946/` as build history.
Re-run (16:10:03) → **STABLE — all 8 compared measurements within
tolerance of baseline DW-A-BASELINE-2026-11-17**, exit 0; record
schema-validated PASS, body_sha256 verified; the checker's own
verdicts came through as noted context (clean CLEANLY, shifted
FAILS — the failure still isolates to the vertical join).

Next: framediff through the runner (the third suite; the proof's
subject outcome was CHANGED v1-vs-v3 with the instrument stable, so
against the pinned baseline the runner should read STABLE — every
pinned statistic reproduced).

## Checkpoint 4 — framediff self-test; build complete

**framediff:** `python3 driftwatch.py framediff` (22 s wall) →
**STABLE — all 6 compared measurements within tolerance of baseline
DW-B-BASELINE-2026-11-26**, exit 0. Every pinned statistic reproduced
exactly: self-diff 0.0 / 0.0; cross-diff MAD max 78.6012, mean
68.6311, median 70.1647; 156 frames over MAD 5. (Read against the
proof: the subject change v1→v3 is what the baseline itself records;
STABLE here means the harness still reproduces those statistics —
the instrument has not drifted.) Record schema-validated PASS,
body_sha256 verified.

**README.md** written: what the runner is, how to run a suite, what
it writes, the config format field by field, and the honest scope.

## Final state

All three proof suites now run end-to-end through the single runner,
each reproducing its proof outcome against its pinned baseline:

| Suite | Runner verdict | Record schema | body_sha256 |
|---|---|---|---|
| skills-integrity | STABLE (5/5 exact) | PASS | verified |
| seam-check | STABLE (8/8 within ±0.005) | PASS | verified |
| framediff | STABLE (6/6 exact) | PASS | verified |

Nothing was pushed to GitHub in this build. The one leftover from
the tolerance fix: the superseded first seam-check run's outputs
remain in `out/seam-check/2026-11-27/160946/` (a CHANGED verdict
produced by the float-representation edge, before the fix) — kept
as build history and explained in Checkpoint 3; the parent may
delete that folder before pushing if a clean `out/` is preferred.
