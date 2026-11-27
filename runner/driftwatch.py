#!/usr/bin/env python3
"""DriftWatch runner — the free single-suite drift checker.

Pin a baseline once (a Proof Record). Run a suite again later with
this tool. It re-runs the suite's configured command, extracts the
fresh measurements, compares them against the pinned baseline within
the configured tolerances, and writes two things:

  * a new Proof Record (Open Door Standards, Proof Record v0.3.0), and
  * a short markdown drift summary (STABLE / CHANGED / INCONCLUSIVE).

A suite whose command fails, or whose measurements cannot be
extracted, is INCONCLUSIVE with the reason stated. The runner never
invents a number: every value it reports came out of a command it
actually ran in this session.

Usage:
    python3 driftwatch.py suites/skills-integrity.json
    python3 driftwatch.py seam-check          # looks in ./suites/

Exit codes: 0 = STABLE, 1 = CHANGED, 2 = INCONCLUSIVE,
3 = the run itself was misconfigured (no record written).

Standard library only. Python 3.9+.
"""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STANDARD = {"name": "Proof Record", "version": "0.3.0"}
RUNNER_VERSION = "0.1.0"
DEFAULT_TIMEOUT = 900  # seconds, per command


class ConfigError(Exception):
    """The config or baseline is unusable — no record is written."""


class Inconclusive(Exception):
    """The suite ran (or tried to) but produced nothing comparable."""


def expand(value):
    """Expand a leading ~ in a path string; pass anything else through."""
    if isinstance(value, str) and value.startswith("~"):
        return str(Path(value).expanduser())
    return value


def load_json(path, what):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        raise ConfigError(f"{what} not found: {path}")
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{what} is not valid JSON ({path}): {exc}")


def dig(obj, dotted):
    """Follow a dotted path ('checks.0.vertical.wrap_ratio') into JSON."""
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        elif isinstance(cur, dict):
            cur = cur[part]
        else:
            raise KeyError(dotted)
    return cur


def coerce(text):
    """Turn a captured string into int/float when it plainly is one."""
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


# ---------------------------------------------------------------- commands

def run_command(cmd_cfg):
    """Run one configured command; return (stdout, stderr, returncode)."""
    argv = [expand(a) for a in cmd_cfg["argv"]]
    cwd = expand(cmd_cfg.get("cwd", "."))
    timeout = cmd_cfg.get("timeout_seconds", DEFAULT_TIMEOUT)
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True,
                              text=True, timeout=timeout)
    except FileNotFoundError:
        raise Inconclusive(f"command not found: {argv[0]}")
    except subprocess.TimeoutExpired:
        raise Inconclusive(f"command timed out after {timeout}s: "
                           + " ".join(argv))
    allowed = cmd_cfg.get("allow_exit_codes", [0])
    if proc.returncode not in allowed:
        raise Inconclusive(
            f"command exited {proc.returncode} (allowed: {allowed}): "
            + " ".join(argv) + f" — stderr: {proc.stderr.strip()[:300]}")
    return proc.stdout, proc.stderr, proc.returncode


def extract_measurements(config, outputs):
    """Apply every command's extract specs; later commands may refine
    a value an earlier command produced (same name wins, in order)."""
    fresh = {}
    for cmd_cfg, stdout in outputs:
        parse = cmd_cfg.get("parse", "text")
        parsed = None
        if parse == "json":
            try:
                parsed = json.loads(stdout)
            except json.JSONDecodeError as exc:
                raise Inconclusive(
                    f"command output was not valid JSON: {exc}")
        for spec in cmd_cfg.get("extract", []):
            name = spec["name"]
            kind = spec.get("from", "json_path")
            try:
                if kind == "json_path":
                    value = dig(parsed, spec["path"])
                elif kind == "count_lines_matching":
                    value = sum(1 for line in stdout.splitlines()
                                if re.search(spec["pattern"], line))
                elif kind == "regex":
                    m = re.search(spec["pattern"], stdout)
                    if m is None:
                        raise KeyError(spec["pattern"])
                    value = coerce(m.group(spec.get("group", 1)))
                else:
                    raise ConfigError(f"unknown extract kind: {kind}")
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise Inconclusive(
                    f"could not extract '{name}' "
                    f"({kind}: {spec.get('path', spec.get('pattern'))}): {exc}")
            fresh[name] = value
    return fresh


# ---------------------------------------------------------------- compare

def compare(baseline, fresh, tolerances):
    """Compare fresh values against the baseline record's measurements.

    Returns (rows, missing, extras). Each row: name, baseline value,
    fresh value, delta (numeric only), within (True/False/None)."""
    default_tol = tolerances.get("default_abs", 0)
    per_name = tolerances.get("per_measurement", {})
    rows, missing = [], []
    base_names = set()
    for meas in baseline.get("measurements", []):
        name = meas["name"]
        base_names.add(name)
        base_val = meas["value"]
        if name not in fresh:
            missing.append(name)
            continue
        fresh_val = fresh[name]
        row = {"name": name, "baseline": base_val, "fresh": fresh_val,
               "unit": meas.get("unit")}
        if isinstance(base_val, (int, float)) and not isinstance(base_val, bool) \
                and isinstance(fresh_val, (int, float)) \
                and not isinstance(fresh_val, bool):
            tol = per_name.get(name, default_tol)
            row["delta"] = fresh_val - base_val
            row["tolerance"] = tol
            # The 1e-9 epsilon absorbs binary floating-point
            # representation error only (e.g. 0.600 - 0.595 evaluates
            # to 0.0050000000000000044); it is far below the precision
            # any suite here records at, so it cannot mask real drift.
            row["within"] = abs(row["delta"]) <= tol + 1e-9
        else:
            row["delta"] = None
            row["tolerance"] = None
            row["within"] = fresh_val == base_val
        rows.append(row)
    extras = [n for n in fresh if n not in base_names]
    return rows, missing, extras


# ---------------------------------------------------------------- records

def canonical_body_sha256(record):
    """SHA-256 of the record without body_sha256, serialised with
    sorted keys and compact separators — the convention used by
    proof/build_records.py, so runner records verify the same way."""
    body = {k: v for k, v in record.items() if k != "body_sha256"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_record(config, baseline, rows, extras, fresh, outcome, reason,
                 evidence, stamp, date_str):
    suite = config["suite"]
    measurements = []
    for row in rows:
        meas = {"name": row["name"], "value": row["fresh"],
                "target": row["baseline"],
                "result": "pass" if row["within"] else "fail"}
        if row["tolerance"] is not None:
            meas["tolerance"] = (f"±{row['tolerance']} (abs)"
                                 if row["tolerance"] else "exact match")
        if row.get("unit"):
            meas["unit"] = row["unit"]
        measurements.append(meas)
    for name in extras:
        measurements.append({"name": name, "value": fresh[name],
                             "target": "not in baseline", "result": "noted"})
    verdict = {"outcome": outcome}
    deficits = []
    changed = [r["name"] for r in rows if not r["within"]]
    if changed:
        deficits.append("Measurements outside tolerance: "
                        + ", ".join(changed))
    if reason:
        deficits.append(reason)
    if deficits:
        verdict["deficits"] = deficits
    commands = "; ".join(" ".join(expand(a) for a in c["argv"])
                         for c in config["commands"])
    record = {
        "record_id": f"DW-{suite.upper()}-RUN-{date_str}-{stamp}",
        "record_type": "checker_result",
        "standard": STANDARD,
        "subject": baseline["subject"],
        "method": {
            "tool": f"DriftWatch runner (driftwatch.py {RUNNER_VERSION}) — "
                    f"suite '{suite}': {baseline['method']['tool']}",
            "tool_version": f"driftwatch.py {RUNNER_VERSION}",
            "procedure": commands,
            "measured_at": date_str,
            "environment": "Local run via the DriftWatch free runner; "
                           f"baseline {baseline['record_id']}",
        },
        "measurements": measurements,
        "verdict": verdict,
        "evidence": evidence,
        "limitations": [
            "Automated re-run by the DriftWatch free runner; compares "
            "only the measurements named in the baseline record."],
        "context": {"related_record_ids": [baseline["record_id"]]},
        "supersedes": None,
        "issued_by": f"DriftWatch runner (driftwatch.py {RUNNER_VERSION})",
        "issued_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    record["body_sha256"] = canonical_body_sha256(record)
    return record


def write_summary(path, config, baseline, rows, missing, extras,
                  outcome, reason, record_id):
    lines = [f"# Drift summary — {config['suite']}",
             "",
             f"**Baseline:** {baseline['record_id']} · "
             f"**Run record:** {record_id}",
             f"**Outcome:** {outcome}",
             ""]
    if reason:
        lines += [f"**Note:** {reason}", ""]
    if rows:
        lines += ["| Measurement | Baseline | Fresh | Delta | Within tolerance |",
                  "|---|---|---|---|---|"]
        for r in rows:
            delta = "—" if r["delta"] is None else f"{r['delta']:+g}"
            lines.append(f"| {r['name']} | {r['baseline']} | {r['fresh']} "
                         f"| {delta} | {'yes' if r['within'] else 'NO'} |")
        lines.append("")
    if missing:
        lines += ["Baseline measurements not produced by this run: "
                  + ", ".join(missing), ""]
    if extras:
        lines += ["Fresh measurements not in the baseline (noted, "
                  "not compared): " + ", ".join(extras), ""]
    lines += ["A measurement record, not a warranty.", ""]
    path.write_text("\n".join(lines))


# ---------------------------------------------------------------- main

def resolve_config(arg):
    p = Path(arg)
    if p.is_file():
        return p
    here = Path(__file__).parent
    for cand in (here / "suites" / arg, here / "suites" / f"{arg}.json"):
        if cand.is_file():
            return cand
    raise ConfigError(f"suite config not found: {arg}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="DriftWatch single-suite runner")
    ap.add_argument("config", help="suite config path, or a name in ./suites/")
    ap.add_argument("--out", default=None,
                    help="output root (default: ./out next to this script)")
    args = ap.parse_args(argv)

    try:
        config_path = resolve_config(args.config)
        config = load_json(config_path, "suite config")
        for field in ("suite", "baseline_record", "commands"):
            if field not in config:
                raise ConfigError(f"config missing field: {field}")
        baseline_path = expand(config["baseline_record"])
        baseline = load_json(baseline_path, "baseline record")
    except ConfigError as exc:
        print(f"driftwatch: {exc}", file=sys.stderr)
        return 3

    suite = config["suite"]
    now = datetime.now(timezone.utc)
    date_str, stamp = now.strftime("%Y-%m-%d"), now.strftime("%H%M%S")
    out_root = Path(args.out) if args.out else Path(__file__).parent / "out"
    out_dir = out_root / suite / date_str / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    outcome, reason, rows, missing, extras = None, None, [], [], []
    fresh, evidence = {}, []
    try:
        outputs = []
        for i, cmd_cfg in enumerate(config["commands"], 1):
            stdout, stderr, _rc = run_command(cmd_cfg)
            raw_path = out_dir / f"raw-cmd{i}.txt"
            raw_path.write_text(stdout)
            evidence.append({
                "kind": "file", "locator": str(raw_path),
                "sha256": hashlib.sha256(stdout.encode()).hexdigest()})
            outputs.append((cmd_cfg, stdout))
        fresh = extract_measurements(config, outputs)
        tolerances = config.get("tolerances", {})
        rows, missing, extras = compare(baseline, fresh, tolerances)
        if missing:
            outcome = "INCONCLUSIVE"
            reason = ("baseline measurements not produced by this run: "
                      + ", ".join(missing))
        elif any(not r["within"] for r in rows):
            changed = [r["name"] for r in rows if not r["within"]]
            outcome = ("CHANGED — " + ", ".join(changed)
                       + " outside tolerance vs baseline "
                       + baseline["record_id"])
        else:
            outcome = (f"STABLE — all {len(rows)} compared measurements "
                       f"within tolerance of baseline "
                       f"{baseline['record_id']}")
    except Inconclusive as exc:
        outcome, reason = "INCONCLUSIVE", str(exc)

    record = build_record(config, baseline, rows, extras, fresh, outcome,
                          reason, evidence, stamp, date_str)
    record_path = out_dir / f"{record['record_id']}.json"
    record_path.write_text(json.dumps(record, indent=2) + "\n")
    summary_path = out_dir / "summary.md"
    write_summary(summary_path, config, baseline, rows, missing, extras,
                  outcome, reason, record["record_id"])

    print(f"{suite}: {outcome}")
    print(f"record:  {record_path}")
    print(f"summary: {summary_path}")
    if outcome.startswith("STABLE"):
        return 0
    if outcome.startswith("CHANGED"):
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
