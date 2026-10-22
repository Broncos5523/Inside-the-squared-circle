# Inside the Squared Circle — v4.3 Connected-Pipeline Proof

**Status: proof of concept only; NOT PUBLISHED and NOT a complete wrestling card system.**

This extends the research after v4.0/v4.2 and answers the next question: **can a data collection job safely turn documented TV episode API results into static JSON that a Fire TV browser can continuously display, without putting an unverified wrestling match on the screen?**

## What you get

- `proof/collector.py`: real internet-capable TVmaze collector (6 programs) using Python standard library, retry/backoff, source/time validation, per-show last-good, atomic cache update.
- **Research-only preview paragraph extraction:** TVmaze episode summaries, when supplied, are separated into candidate evidence excerpts marked `UNVERIFIED_DESCRIPTION` and never displayed as confirmed matches. This is not yet a model-based extractor.
- `web/index.html`, `web/assets/*`: real portrait-format HTML/CSS/JS display, rotates five primary shows every 14 seconds with a secondary Evolve recap once per two primary cycles, polls cached JSON every 2 minutes, fits a 9:16 viewport without cropping. Each primary show has a distinct color accent; this **is a testing UI, NOT the approved finished wrestling designs**.
- `web/data/snapshot.json`: clearly marked **October 22 fixture based on previously observed TVmaze metadata**, not a live/current feed. It cannot populate a verified match card.
- `tests/test_collector.py`: deterministic software behavior tests with synthetic source fixtures; includes failure, stale, spoiler/risk protections.
- `.github/workflows/refresh-and-publish.yml`: optional GitHub Actions scheduled job (every 4 hours), tests, collector, persistent last-good JSON commit, and GitHub Pages deployment. **Requires user-owned GitHub account/repository and Pages enabled**; not deployed from this conversation.
- `docs/PROVIDER_GATE.md`: contract for attaching an expressly licensed match-card source. No news RSS publisher crawler is enabled.

## Run locally (without internet)

At the project root:

```bash
python -m unittest discover -s tests -v
python -m http.server 8000 -d web
```

Open `http://localhost:8000`. The packaged schedule is a dated research example. The live data-collection command below must be run on a machine with internet:

```bash
python proof/collector.py --out web/data/snapshot.json
```

If all providers fail, the collector exits nonzero **without overwriting previously saved data**. The display uses the retained JSON and reports age/staleness.

## Optional free hosting, but not guaranteed forever

1. Create a **public** GitHub repo and upload this package at repo root. Public repos are necessary for GitHub Pages on GitHub Free; published information is public.
2. In GitHub repository Settings → Pages, set source to **GitHub Actions**.
3. Ensure repository Actions have permission to write content (the workflow needs `contents: write` to persist the JSON cache); configure branch protection accordingly.
4. Open Actions → “Refresh schedules and publish research display” → **Run workflow**.
5. Watch the tests/collector and then the resulting Pages link. Only share/use it as a **research demo**.
6. GitHub Actions scheduled jobs **can be delayed/dropped** and may be disabled in an inactive public repo after **60 days**. Consequently, this is not a proven set-and-forget 24/7 service; no deployments have been attempted.

No account credentials are needed for TVmaze. None should be hardcoded in a public repo. Do not add unauthorized WWE, TNA or publisher scraping.

## Data and licensing

TVmaze documents its free API under **CC BY-SA**, including attribution and ShareAlike obligations. The display retains a TVmaze attribution link. Before a public deployment, review whether additional notices and ShareAlike requirements apply to your adapted data. This package contains **no wrestler photographs, logos, actual broadcast artwork, scraped articles, or copyrighted matching of approved graphics**.

**Critical limit:** The collector connects only the *schedule*. Actual wrestling match cards, confirmed appearances, titles and results remain empty until an independently tested and authorized provider is added. This is deliberate to prevent hallucinations. On-screen fallback means *no authorized card feed is connected*, **not** *no matches announced*.

## Cache persistence caveat

The scheduled workflow commits **only `web/data/snapshot.json`** back to the public repository after collection, before deploying Pages. This is deliberate: fresh GitHub Actions runners otherwise restart with the original dated sample snapshot and cannot retain last-good schedules across runs. Repository branch rules may prevent the bot push; in that case the workflow fails rather than pretending that the cache is durable. API collection, a full scheduled workflow, and the published website still need user-owned GitHub deployment validation.