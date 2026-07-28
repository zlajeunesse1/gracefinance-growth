# GraceFinance Research Signal Engine

A deterministic X acquisition engine for GraceFinance Research.

Its primary goal is not generic engagement or account signup. It recruits voluntary anonymous participants, increases completed research signals, grows the longitudinal panel, and improves the usefulness of the GraceFinance Participant Confidence Index.

## What it does

- Pulls the latest experimental research summary.
- Reads the current participant index, participant count, returning-participant count, and data-quality totals.
- Scores campaign families covering baseline, mission, index, curiosity, privacy, longitudinal participation, panel growth, methodology, and research questions.
- Avoids repeating the same campaign category or exact post.
- Adds a unique campaign ID and UTM attribution to every GraceFinance link.
- Publishes to X only.
- Stores campaign decisions, tweet IDs, snapshots, status, and recurring public engagement metrics in SQLite.
- Uses historical engagement rates as one input to future campaign selection.

## Product promise

Campaign language must match the public research product:

- No account or public profile is required.
- No name, password, bank connection, or exact address is required.
- Participants answer five financial-confidence questions and provide a state-level location or decline to answer.
- A signed anonymous browser identity allows returning measurement.
- The index is experimental voluntary-participant research, not a nationally representative statistic.
- State-level findings remain hidden below the published privacy threshold.

## Run safely

Dry run is enabled by default:

```bash
python -m app.main --run-once --theme "manual research acquisition test"
```

To publish, configure the existing X environment variables and set:

```text
DRY_RUN=false
```

Then run once before enabling the scheduler:

```bash
python -m app.main --run-once --theme "first live research participant campaign"
```

## Railway persistence

The default database is `data/growth.db`. Attach a Railway persistent volume so campaign and metrics history survive deploys.

## Research metrics source

The engine first requests:

```text
/research/summary
```

If the new research endpoint is not yet deployed, it falls back to the legacy raw index endpoint so the scheduler does not crash during rollout.

## Attribution

Every campaign URL includes:

- `utm_source=x`
- `utm_medium=organic`
- a unique `utm_campaign`
- `utm_content=research_signal_engine`

The public research API stores these fields with each submission. Campaign performance should ultimately be ranked by eligible completed research signals and returning-participant growth, not impressions alone.
