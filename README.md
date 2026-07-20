# GraceFinance Signal Engine

A deterministic X acquisition engine for GraceFinance.

Its primary goal is not generic engagement. It is to turn attention into completed financial check-ins, grow the proprietary Financial Confidence dataset, and make the public index more valuable over time.

## What it does

- Pulls the latest GraceFinance Financial Confidence Index snapshot.
- Scores multiple campaign families: check-in, mission, index, curiosity, product, participation, and question.
- Avoids repeating the same campaign category or exact post.
- Adds a unique campaign ID and UTM attribution to every GraceFinance link.
- Publishes to X only.
- Stores campaign decisions, tweet IDs, snapshots, status, and recurring public engagement metrics in SQLite.
- Uses historical engagement rates as one input to future campaign selection.

## Run safely

Dry run is enabled by default:

```bash
python -m app.main --run-once --theme "manual acquisition test"
```

To publish, configure the existing X environment variables and set:

```text
DRY_RUN=false
```

Then run once before enabling the scheduler:

```bash
python -m app.main --run-once --theme "first live acquisition campaign"
```

## Railway persistence

The default database is `data/growth.db`. Attach a Railway persistent volume and mount it so campaign and metrics history survive deploys. The path can later be moved to an environment setting or replaced with GraceFinance Postgres.

## Conversion attribution

Every campaign URL includes:

- `utm_source=x`
- `utm_medium=organic`
- a unique `utm_campaign`
- `utm_content=signal_engine`

The GraceFinance frontend/backend should persist those parameters through visit, signup, guest check-in, and logged-in check-in events. That is the remaining step required for complete visit-to-check-in attribution.
