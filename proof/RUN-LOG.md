# DriftWatch — Smallest Proof Run Log

**Run date:** 2026-11-27 (America/Phoenix)
**Operator:** Mira (subagent run, local only — no GitHub writes)
**Method:** PLAN.md Plan A, smallest proof steps 1–3: choose 3 suites,
pin a baseline, re-run the same suite against a second version/date,
report exactly what moved.
**Suites (approved Nov 27, 2026):** A) one ProofBench suite —
Seam Check (CIEDE2000). B) one media check — the framediff harness
on Two Lights v1 vs v3. C) one skill pack check — Measured Skills
manifest/checker verification.
**Rule for this log:** every number below traces to a command actually
run in this session (raw output in `raw/`) or a record actually read
(file cited inline).

**Run complete (2026-11-27).** All three suites ran. Six Proof
Records were built by `build_records.py` and validated against the
Proof Record schema v0.3.0 (all six pass). Outcomes: A — STABLE
(certified-checker arm), with the live-app arm INCONCLUSIVE (not
re-runnable in this session); B — CHANGED (subject v1→v3), instrument
repeatability delta 0.0000; C — STABLE (23/23). The Drift Report is
at `../reports/DRIFT-REPORT-2026-11-27-001.md`. Nothing was pushed
to GitHub by this run; `../paths-proof-001.bin` lists the 20 files
ready for the parent's push.

---

## Suite C — Measured Skills manifest verification

**Baseline (record of 2026-11-26, read from
`~/workspace/measured-skills/RELEASES.md`):**
- MANIFEST.sha256 covers 23 files (one SKILL.md per pack).
- Independent re-hash (`sha256sum -c MANIFEST.sha256`): 23 of 23 OK.
- `check_install.py` on a pristine copy: exit 0 —
  "Checked all packs: 23 OK, 0 missing, 0 changed, 0 extra (of 23 files)."

**Re-run (2026-11-27, this session):** commands and raw outputs below,
saved to `raw/suite-c-sha256sum.txt` and `raw/suite-c-check-install.txt`.

**Re-run results (2026-11-27):**
- `sha256sum -c MANIFEST.sha256` — exit 0; 23 lines, all ": OK"
  (counted from the raw output). 23/23 OK — identical to baseline.
- `python3 check_install.py` — exit 0; output verbatim:
  "Checked all packs: 23 OK, 0 missing, 0 changed, 0 extra (of 23 files).
  Result: clean — this copy matches the release exactly."
  Identical wording and counts to the 2026-11-26 baseline record.
- Subject hashes at re-run: MANIFEST.sha256 file sha256
  `59a56f647372b202ca6c8a3dc488592afaf9f1be21668a76b4fd0b95e2772165`;
  check_install.py sha256
  `d7cbce6bf1d0a7e5a686545b8aaa7df243a0ff7dbcd657634ed78a1beabd1799`.

**Suite C outcome: STABLE.** Nothing moved: 23/23 files hash-match
the pinned release manifest, exactly as at delivery on Nov 26.

---

## Suite B — framediff on Two Lights

**Baseline (records of 2026-11-26 in `~/workspace/fix-the-take-proof/`):**
- `verify_self_diff.json` — v3 vs v3, window 6.5–10.0 s, 156 frames
  compared outside the window: MAD max 0.0, mean 0.0, median 0.0,
  0 frames over MAD 1.
- `verify_cross_diff.json` — v3 vs v1, same window and frame count:
  MAD max 78.6012, mean 68.6311, median 70.1647, 156/156 frames over
  MAD 5.

**Re-run (2026-11-27, this session):** `framediff.py` run fresh on the
same two video files with the same window; outputs below, saved to
`raw/suite-b-*.json`.

**Re-run results (2026-11-27):** `framediff.py` (sha256
`bd9ed544e34ed3132a3520266b0f4e23e4a9eb51af7285dc3dcf4a9f7221faf3`),
window 6.5–10.0 s, `--json`:
- v3 vs v3 (sanity): MAD max 0.0, mean 0.0, median 0.0, 0/156 frames
  over MAD 1 — identical to the Nov 26 self-diff record.
- v3 vs v1: MAD max **78.6012**, mean **68.6311**, median **70.1647**,
  156/156 frames over MAD 5 — identical to the Nov 26 cross record
  to all four recorded decimal places. Instrument repeatability
  delta vs baseline: **0.0000 on every statistic**.
- Subject hashes: v3 file sha256
  `f41653ace620e36eaf21659ab6c3e563db5b0a9a51ba21f4d0bd393b1b174001`;
  v1 file sha256
  `44ab6a4f630879ce3162b846bfd1937b1b6e3739eee7aa0d53de4108bdbb6e6b`.

**Suite B outcome: CHANGED (subject), instrument stable.** Between
Two Lights v1 and v3, every one of the 156 frames outside the
6.5–10.0 s window differs substantially (mean MAD 68.63 on the
0–255 scale): the change between versions is total, not local to
the retake window. The harness itself did not drift — both of its
pinned statistics reproduced exactly a day later.
**Unmeasured by design:** the harness excludes the window frames
(156–239); what changed *inside* 6.5–10.0 s is not measured by this
suite (the Fix the Take spec assigns the window to visual/human
checks, and its paid Retake firing never took place).

---

## Suite A — ProofBench Seam Check (CIEDE2000)

**Baseline (record of 2026-11-17, read from
`~/workspace/proofbench-manus-transfer/documents/12-SKILL-browser-utility-webapp-v3.md`,
lines 63–64):** independent run against live ProofBench v2 BUILD 02.01
with canonical PG4 fixtures at native resolution (256×256):
- `pg4-clean-tile.png` — verdict **CLEANLY**. Live app: vertical
  0.82 / −0.91; horizontal 0.72 / −0.02 (wrap ratio / ΔE00 excess).
  Certified reference checker: CLEANLY, wrap 0.72 / 0.60.
- `pg4-shifted-tile.png` (right half shifted 40 px) — verdict
  **FAILS**. Live app: vertical 27.13 / +36.86; horizontal
  0.72 / −0.02. Certified reference checker: FAILS, vertical
  24.36 / +21.39.
- Stated in the record: the two implementations sample differently;
  magnitudes agree in order, not exactly.

**Baseline source of record:** the fuller Nov 17 record is
`~/workspace/proofbench-acceptance/acceptance-report-2026-11-17.md`,
which names the certified checker as
`measured-skills/tools/print_check.py --pattern` and records its
readings per axis — clean: vertical 0.72 / −7.14, horizontal
0.60 / −0.45, CLEANLY; shifted: vertical 24.36 / +21.39, horizontal
0.60 / −0.45, FAILS. (Skill document 12 condenses the clean checker
line to "wrap 0.72 / 0.60"; the acceptance report is primary.)
The canonical fixtures are on disk at `~/workspace/proofbench-acceptance/`
(clean sha256 `27d717af4bf490c3336f01992529b09cda6b5bc1f1808c9e739b6c7b662cf59e`;
shifted sha256 `2edc8533d83ffe4389deaaae71f1560b8fe8fcc0247f929526daa33b813e5493`),
both 256×256 RGB PNG — so the certified-checker arm re-ran locally.

**Re-run results (2026-11-27):**
`python3 tools/print_check.py <fixture> --print-width-mm 100
--print-height-mm 100 --pattern --json`
(checker sha256 `54d986d9bda2fdb4ce08dea22a4c426af55c088f9968436272daf21b7d2a9d98`;
the print dimensions feed only the DPI arm, which is not this suite;
the T9 seam check measures the image itself):
- Clean: **CLEANLY** — vertical wrap 0.719, excess −7.136;
  horizontal wrap 0.595, excess −0.449. Baseline (2 dp): 0.72 / −7.14
  and 0.60 / −0.45. **Match at recorded precision.**
- Shifted: **FAILS** — vertical wrap 24.356, excess +21.386;
  horizontal wrap 0.595, excess −0.449. Baseline: 24.36 / +21.39 and
  0.60 / −0.45. **Match at recorded precision.** The failure still
  isolates to the vertical join, exactly as constructed.

**Suite A outcome: STABLE (certified-checker arm).** All eight
numbers and both verdicts reproduce the Nov 17 baseline exactly at
the precision the baseline was recorded at, ten days later.
**Inconclusive (live-app arm):** the Nov 17 baseline also carries
readings from the hosted ProofBench v2 web app (clean 0.82/−0.91,
0.72/−0.02; shifted 27.13/+36.86, 0.72/−0.02). That arm could not
be re-run in this session — the app is a hosted browser tool and
this run had no browser operation available — so whether the live
app's readings have moved since Nov 17 is **not measured** here and
is reported as inconclusive, not assumed stable.

## Amendment 1 — Suite A app arm re-run (2026-11-27, 09:07–09:10 MST)

The hosted ProofBench app arm, inconclusive in the original run for
lack of a browser, was re-run in a browser session on the same PG4
fixtures (clean sha256 27d717af..., shifted sha256 2edc8533...) at
native resolution; the app reported "Scale used: 1.000x" for both
files and labels "v2" / "BUILD 02.01". All fifteen readings
comparable to the 2026-11-17 app baseline are identical (verdicts
CLEANLY / FAILS; clean 0.82/-0.91/1.11 and 0.72/-0.02/1.30, interior
medians 2.254/3.072; shifted 27.13/+36.86/38.95 and 0.72/-0.02/1.30,
horizontal interior median 3.072). The shifted vertical interior
median (2.278) has no Nov 17 counterpart and is reported without
comparison. Outcome: STABLE — the inconclusive arm is closed.
Record: proof/record-A-apparm-rerun.json (schema-validated,
body_sha256 aab297af...). Raw transcription:
proof/raw/suite-a-app-rerun.txt.
