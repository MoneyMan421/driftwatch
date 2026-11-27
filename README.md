# DriftWatch

**Pin a measured baseline for a model, tool, skill or workflow.
Re-run the same suite after a change. Report exactly what moved.**

## The problem

A model, tool, skill or prompt can change underneath a working
system. Yesterday's pass becomes today's wrong output — and nobody
notices, because nothing visibly "broke." The output still arrives,
still fluent, still confident. It is just different from what you
verified.

This is the stability work the model race deprioritises: every
release is a race to new capability, and the behaviour you already
depended on is nobody's headline. DriftWatch is built for the
people who depend on it.

## The method

1. **Pin a baseline.** Record the versions (model, tool, skill),
   the inputs, the targets and the tolerances — before anything
   changes.
2. **Re-run the same suite.** After a version change, or on a
   schedule. Same inputs, same targets, same tolerances. The suite
   does not move; the subject does.
3. **Report exactly what moved.** Pass → fail flips, numeric deltas
   against the pinned targets, changed outputs, and the first
   version where the change appeared. Stable results are reported
   as stable. Inconclusive results are reported as inconclusive.
   Nothing is trimmed to make the report look better.

The output is a **Drift Report**: a record that can be attached to
a release or a client delivery, and read by someone who did not run
it — a buyer, a team lead, a client. Reports follow the Proof
Record format from
[Open Door Standards](https://github.com/MoneyMan421/open-door-standards):
a measurement record, not a warranty.

## First domain

DriftWatch starts where the fixtures and measured targets already
exist: our own checker and media suites — the ProofBench family and
the measured guide checkers. Not a generic observability platform.
A bench that begins with suites whose targets were measured before
the bench existed.

The smallest proof, in order:

1. Choose 3 existing suites.
2. Run each suite against two versions or two dates.
3. Publish one honest report showing one real change, one stable
   result and one inconclusive result.
4. Put the runner in outside hands and record whether it gets run
   a second time without help.

**Pass line:** at least 3 of 5 outside users run it twice, and at
least one says the report changed a release, purchase or rollback
decision.

## Status — stated plainly

**First proof run: complete — steps 1–3 of the smallest proof.**
On 2026-11-27, three existing suites were pinned to their recorded
baselines and re-run unchanged: the ProofBench Seam Check (T9,
CIEDE2000), the framediff media check on Two Lights v1 vs v3, and
the Measured Skills release-integrity check. The first Drift Report
— `reports/DRIFT-REPORT-2026-11-27-001.md` — records what the runs
showed: one real change and three stable results. (One arm, the
hosted-app check, could not be re-measured in the first session
and was reported inconclusive; it was measured later the same day
and closed STABLE by Amendment 1, appended to the report — the
original text stands as issued.) Proof Records and the full run
log are under `proof/`. The runner is packaged at `runner/` and
self-tested: all three suites reproduce their pinned baselines
through it. Step 4 of the proof — the runner in five outside
hands, run twice — has not happened yet. Anything this page says
DriftWatch *does* is the method above; anything it *will do* is
labelled as such. That distinction is the product.

## Testers wanted

Five outside testers, to complete the smallest proof: run the
runner twice — once now, once after anything changes — and answer
five short questions about the experience. The pass line is at
least three of five running it twice, and at least one saying a
report changed a decision. If you build or run agents and want
in, open an issue on this repo. Short and blunt feedback is
perfect; a failure I can read is worth more than praise.

## The house rules

- Measure the deliverable, never the record of it.
- Spec in numbers, with tolerances, before measuring.
- Two sources before a number ships as ours.
- Failures and inconclusive results are published, not hidden.
- A Drift Report is a measurement record, not a warranty.

## Where it sits

DriftWatch is the PROVE layer's flagship in the Open Door Stack —
Know → Govern → Run → **Prove** → Reuse — and the first public
wedge of the portfolio behind it.

*By Collin.*
