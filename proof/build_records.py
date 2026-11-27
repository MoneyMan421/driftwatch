#!/usr/bin/env python3
"""Build the six Proof Records for the DriftWatch smallest proof.

body_sha256 = SHA-256 of the canonical record body: the record
serialised as JSON with sorted keys and compact separators,
excluding the body_sha256 field itself.
Every measurement value below is transcribed from a record read or a
command run in the 2026-11-27 session (see RUN-LOG.md); raw outputs
are in raw/ and are hashed into each record's evidence.
"""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE / "raw"
ISSUED_AT = subprocess.run(["date", "-Iseconds"], capture_output=True,
                           text=True).stdout.strip().replace("+00:00", "Z")
ISSUED_BY = "Mira — DriftWatch smallest proof run, 2026-11-27"
STD = {"name": "Proof Record", "version": "0.3.0"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ev(path: Path) -> dict:
    return {"kind": "file", "locator": str(path), "sha256": sha(path)}


def finish(rec: dict, fname: str) -> dict:
    body = json.dumps(rec, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    rec["body_sha256"] = hashlib.sha256(body).hexdigest()
    (HERE / fname).write_text(json.dumps(rec, indent=2) + "\n")
    return rec


def meas(name, value, target, result, tol=None, unit=None):
    m = {"name": name, "value": value, "target": target, "result": result}
    if tol:
        m["tolerance"] = tol
    if unit:
        m["unit"] = unit
    return m


CHK = "54d986d9bda2fdb4ce08dea22a4c426af55c088f9968436272daf21b7d2a9d98"
FD = "bd9ed544e34ed3132a3520266b0f4e23e4a9eb51af7285dc3dcf4a9f7221faf3"
CI = "d7cbce6bf1d0a7e5a686545b8aaa7df243a0ff7dbcd657634ed78a1beabd1799"

# ---------------- Suite A — Seam Check ----------------
a_subj = {"kind": "tool",
          "name": "ProofBench Seam Check (T9) on PG4 canonical fixtures — certified checker arm",
          "version": f"print_check.py sha256:{CHK}",
          "content_sha256": "27d717af4bf490c3336f01992529b09cda6b5bc1f1808c9e739b6c7b662cf59e"}
a_bands = "CLEANLY band: wrap ratio <= 1.5 and dE00 excess <= 1.0"

a_base = {
    "record_id": "DW-A-BASELINE-2026-11-17",
    "record_type": "checker_result",
    "standard": STD,
    "subject": a_subj,
    "method": {"tool": "print_check.py --pattern (certified reference checker)",
               "tool_version": f"sha256:{CHK}",
               "procedure": "T9 seam check at native resolution on pg4-clean-tile.png and pg4-shifted-tile.png (256x256), worse axis rules, as recorded 2026-11-17",
               "measured_at": "2026-11-17",
               "environment": "Readings transcribed from ~/workspace/proofbench-acceptance/acceptance-report-2026-11-17.md (primary) and documents/12-SKILL-browser-utility-webapp-v3.md"},
    "measurements": [
        meas("clean_vertical_wrap_ratio", 0.72, a_bands, "pass"),
        meas("clean_vertical_de_excess", -7.14, a_bands, "pass"),
        meas("clean_horizontal_wrap_ratio", 0.60, a_bands, "pass"),
        meas("clean_horizontal_de_excess", -0.45, a_bands, "pass"),
        meas("shifted_vertical_wrap_ratio", 24.36, "FAILS band (by construction: right half rolled 40 px)", "pass"),
        meas("shifted_vertical_de_excess", 21.39, "FAILS band (by construction)", "pass"),
        meas("shifted_horizontal_wrap_ratio", 0.60, a_bands, "pass"),
        meas("shifted_horizontal_de_excess", -0.45, a_bands, "pass"),
    ],
    "verdict": {"outcome": "CLEANLY (clean fixture), FAILS (shifted fixture) — both as constructed"},
    "evidence": [ev(Path.home() / "workspace/proofbench-acceptance/acceptance-report-2026-11-17.md")],
    "limitations": ["Baseline transcribed from the Nov 17 acceptance record, not re-measured on that date by this run.",
                    "The live hosted app arm of the Nov 17 baseline is a separate implementation and is not covered by this record."],
    "context": {"related_record_ids": ["DW-A-RERUN-2026-11-27"]},
    "supersedes": None,
    "issued_by": ISSUED_BY, "issued_at": ISSUED_AT,
}

a_rerun = {
    "record_id": "DW-A-RERUN-2026-11-27",
    "record_type": "checker_result",
    "standard": STD,
    "subject": a_subj,
    "method": {"tool": "print_check.py --pattern (certified reference checker)",
               "tool_version": f"sha256:{CHK}",
               "procedure": "python3 tools/print_check.py <fixture> --print-width-mm 100 --print-height-mm 100 --pattern --json (print dimensions feed only the DPI arm, not the T9 seam check)",
               "measured_at": "2026-11-27",
               "environment": "Local run, fixtures at ~/workspace/proofbench-acceptance/ (clean sha256 27d717af..., shifted sha256 2edc8533...)"},
    "measurements": [
        meas("clean_vertical_wrap_ratio", 0.719, 0.72, "pass", "match at baseline precision (2 dp)"),
        meas("clean_vertical_de_excess", -7.136, -7.14, "pass", "match at baseline precision (2 dp)"),
        meas("clean_horizontal_wrap_ratio", 0.595, 0.60, "pass", "match at baseline precision (2 dp)"),
        meas("clean_horizontal_de_excess", -0.449, -0.45, "pass", "match at baseline precision (2 dp)"),
        meas("shifted_vertical_wrap_ratio", 24.356, 24.36, "pass", "match at baseline precision (2 dp)"),
        meas("shifted_vertical_de_excess", 21.386, 21.39, "pass", "match at baseline precision (2 dp)"),
        meas("shifted_horizontal_wrap_ratio", 0.595, 0.60, "pass", "match at baseline precision (2 dp)"),
        meas("shifted_horizontal_de_excess", -0.449, -0.45, "pass", "match at baseline precision (2 dp)"),
    ],
    "verdict": {"outcome": "STABLE — verdicts CLEANLY / FAILS and all eight readings reproduce the 2026-11-17 baseline at its recorded precision",
                "deficits": ["Live hosted app arm not re-run: no browser operation was available in this session, so the app readings of Nov 17 (clean 0.82/-0.91, 0.72/-0.02; shifted 27.13/+36.86, 0.72/-0.02) are unverified for drift — inconclusive, not assumed stable."]},
    "evidence": [ev(RAW / "suite-a-clean.json"), ev(RAW / "suite-a-shifted.json")],
    "limitations": ["Covers the certified-checker implementation only; the hosted app samples differently and its numbers are not interchangeable with these."],
    "context": {"related_record_ids": ["DW-A-BASELINE-2026-11-17"]},
    "supersedes": None,
    "issued_by": ISSUED_BY, "issued_at": ISSUED_AT,
}

# ---------------- Suite B — framediff ----------------
b_subj = {"kind": "output",
          "name": "Two Lights video v1 vs v3 — outside-window frame difference (window 6.5-10.0 s excluded)",
          "version": "v3 sha256:f41653ace620e36eaf21659ab6c3e563db5b0a9a51ba21f4d0bd393b1b174001; v1 sha256:44ab6a4f630879ce3162b846bfd1937b1b6e3739eee7aa0d53de4108bdbb6e6b",
          "content_sha256": "f41653ace620e36eaf21659ab6c3e563db5b0a9a51ba21f4d0bd393b1b174001"}
b_method_base = {"tool": "framediff.py (Fix the Take proof harness)",
                 "tool_version": f"sha256:{FD}",
                 "procedure": "Per-frame mean absolute pixel difference (MAD, 0-255 RGB) over the 156 frames outside the 6.5-10.0 s window, 1152x768 @ 24 fps",
                 "measured_at": "2026-11-26",
                 "environment": "Values transcribed from ~/workspace/fix-the-take-proof/verify_self_diff.json and verify_cross_diff.json"}
b_meas_base = [
    meas("self_v3v3_mad_max", 0.0, 0.0, "pass", "identical file must read 0"),
    meas("self_v3v3_mad_mean", 0.0, 0.0, "pass"),
    meas("cross_v3v1_mad_max", 78.6012, "recorded baseline statistic", "noted", unit="MAD"),
    meas("cross_v3v1_mad_mean", 68.6311, "recorded baseline statistic", "noted", unit="MAD"),
    meas("cross_v3v1_mad_median", 70.1647, "recorded baseline statistic", "noted", unit="MAD"),
    meas("cross_frames_with_mad_over_5", 156, "of 156 frames compared", "noted"),
]
b_base = {
    "record_id": "DW-B-BASELINE-2026-11-26", "record_type": "checker_result",
    "standard": STD, "subject": b_subj, "method": b_method_base,
    "measurements": b_meas_base,
    "verdict": {"outcome": "Baseline pinned: self-diff 0.0 on every statistic; v3-vs-v1 cross-diff MAD max 78.6012 / mean 68.6311 / median 70.1647, 156 of 156 frames over MAD 5"},
    "evidence": [ev(Path.home() / "workspace/fix-the-take-proof/verify_self_diff.json"),
                 ev(Path.home() / "workspace/fix-the-take-proof/verify_cross_diff.json")],
    "limitations": ["The harness measures only frames outside the 6.5-10.0 s window; the window itself is unmeasured by this suite."],
    "context": {"related_record_ids": ["DW-B-RERUN-2026-11-27"]},
    "supersedes": None, "issued_by": ISSUED_BY, "issued_at": ISSUED_AT,
}
b_rerun = {
    "record_id": "DW-B-RERUN-2026-11-27", "record_type": "checker_result",
    "standard": STD, "subject": b_subj,
    "method": {"tool": "framediff.py (Fix the Take proof harness)",
               "tool_version": f"sha256:{FD}",
               "procedure": "python3 framediff.py <A> <B> --start 6.5 --end 10.0 --json, run for v3-vs-v3 and v3-vs-v1",
               "measured_at": "2026-11-27",
               "environment": "Local run on the same two video files pinned by sha256 in the subject"},
    "measurements": [
        meas("self_v3v3_mad_max", 0.0, 0.0, "pass", "delta vs baseline 0.0000"),
        meas("self_v3v3_mad_mean", 0.0, 0.0, "pass", "delta vs baseline 0.0000"),
        meas("cross_v3v1_mad_max", 78.6012, 78.6012, "pass", "delta vs baseline 0.0000", unit="MAD"),
        meas("cross_v3v1_mad_mean", 68.6311, 68.6311, "pass", "delta vs baseline 0.0000", unit="MAD"),
        meas("cross_v3v1_mad_median", 70.1647, 70.1647, "pass", "delta vs baseline 0.0000", unit="MAD"),
        meas("cross_frames_with_mad_over_5", 156, 156, "pass", "of 156 frames compared"),
    ],
    "verdict": {"outcome": "CHANGED (subject): between Two Lights v1 and v3 all 156 outside-window frames differ substantially (mean MAD 68.6311 of 255). Instrument stable: every pinned statistic reproduced with delta 0.0000"},
    "evidence": [ev(RAW / "suite-b-self-v3v3.json"), ev(RAW / "suite-b-cross-v3v1.json")],
    "limitations": ["Frames inside the 6.5-10.0 s window (84 frames) are excluded by the harness and are not measured here.",
                    "MAD measures pixel difference, not perceptual or narrative equivalence."],
    "context": {"related_record_ids": ["DW-B-BASELINE-2026-11-26"]},
    "supersedes": None, "issued_by": ISSUED_BY, "issued_at": ISSUED_AT,
}

# ---------------- Suite C — Measured Skills ----------------
c_subj = {"kind": "skill",
          "name": "Measured Skills packs — release integrity vs MANIFEST.sha256 (23 packs, v1.0.0 baseline)",
          "version": "MANIFEST.sha256 sha256:59a56f647372b202ca6c8a3dc488592afaf9f1be21668a76b4fd0b95e2772165",
          "content_sha256": "59a56f647372b202ca6c8a3dc488592afaf9f1be21668a76b4fd0b95e2772165"}
c_meas = [
    meas("files_in_manifest", 23, 23, "pass"),
    meas("files_hash_ok", 23, 23, "pass"),
    meas("files_missing", 0, 0, "pass"),
    meas("files_changed", 0, 0, "pass"),
    meas("files_extra", 0, 0, "pass"),
]
c_base = {
    "record_id": "DW-C-BASELINE-2026-11-26", "record_type": "checker_result",
    "standard": STD, "subject": c_subj,
    "method": {"tool": "sha256sum -c MANIFEST.sha256 and check_install.py",
               "tool_version": f"check_install.py sha256:{CI}",
               "procedure": "Independent re-hash of all 23 manifest files plus the install checker on a pristine copy, as recorded at delivery",
               "measured_at": "2026-11-26",
               "environment": "Values transcribed from ~/workspace/measured-skills/RELEASES.md (Baseline verification — v1.0.0)"},
    "measurements": c_meas,
    "verdict": {"outcome": "Baseline pinned: 23 OK, 0 missing, 0 changed, 0 extra; both verifications exit 0"},
    "evidence": [ev(Path.home() / "workspace/measured-skills/RELEASES.md")],
    "limitations": ["Baseline transcribed from the delivery record in RELEASES.md."],
    "context": {"related_record_ids": ["DW-C-RERUN-2026-11-27"]},
    "supersedes": None, "issued_by": ISSUED_BY, "issued_at": ISSUED_AT,
}
c_rerun = {
    "record_id": "DW-C-RERUN-2026-11-27", "record_type": "checker_result",
    "standard": STD, "subject": c_subj,
    "method": {"tool": "sha256sum -c MANIFEST.sha256 and check_install.py",
               "tool_version": f"check_install.py sha256:{CI}",
               "procedure": "cd ~/workspace/measured-skills && sha256sum -c MANIFEST.sha256; python3 check_install.py",
               "measured_at": "2026-11-27",
               "environment": "Local run against the delivery folder itself"},
    "measurements": c_meas,
    "verdict": {"outcome": "STABLE — 23 of 23 files hash-match the pinned release manifest, identical to the 2026-11-26 delivery baseline; both commands exit 0"},
    "evidence": [ev(RAW / "suite-c-sha256sum.txt"), ev(RAW / "suite-c-check-install.txt")],
    "limitations": ["Verifies file integrity against the manifest only; it does not re-measure the content quality of any pack."],
    "context": {"related_record_ids": ["DW-C-BASELINE-2026-11-26"]},
    "supersedes": None, "issued_by": ISSUED_BY, "issued_at": ISSUED_AT,
}

for rec, fn in [(a_base, "record-A-baseline.json"), (a_rerun, "record-A-rerun.json"),
                (b_base, "record-B-baseline.json"), (b_rerun, "record-B-rerun.json"),
                (c_base, "record-C-baseline.json"), (c_rerun, "record-C-rerun.json")]:
    finish(rec, fn)
    print("wrote", fn, rec["record_id"], rec["body_sha256"][:16])
