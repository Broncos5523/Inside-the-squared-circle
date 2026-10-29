# SmackDown historical episode collector — isolated staging checkpoint

Date: October 29, 2026. This work is on branch `work/smackdown-history-collector` ONLY.

## Verified findings

- The official October 23, 2026 SmackDown results page has a `Published on October 23, 2026` heading and an exact-dated results title.
- Older official results pages dated October 16, October 9, and October 2 **lack the same publication heading** but expose an exact results date in the HTML title (example: `SmackDown results: Oct. 16, 2026 | WWE`).
- Initial Floot parser rejected those older pages because it required the missing heading. The staging parser handles both official formats and fails closed for date disagreements, non-results pages, missing source bodies, and wrong-source URLs.
- GitHub Actions branch CI completed successfully: 6 offline safety tests plus read-only fetching of four official WWE pages. Source counts on the successful first pass: October 23 had 5 match results; October 16 had 5; October 9 had 3; October 2 had 4. Counts may change if WWE revises pages.
- The staged parser preserves official segment order, separates results from storylines, supports a post-match fallout beat, retains a winner-only portrait rule, and appends an officially mentioned future title match as a consequence rather than a completed result.
- Results remain `review_status=draft`, `safe_for_live_board=false`; publication and editorial approval are intentionally blocked.

## Locked visual checkpoint

User approved original SmackDown Results & Fallout rendering and the 11-item October 23 chronological test on Floot:

- Project ID: `c998c503-76b6-4384-8f58-af463aee10c8`.
- SHA256-verified original 34 artwork items and approved source HTML in Floot.
- Original ticker fix and episode archive approved.
- **No board redesign, no graphics regeneration, no production GitHub Pages modification**.

## Floot integration when free-plan daily quota allows

1. In `helpers/ParseWweSmackDown.tsx`, replace the overly strict `Published on` requirement with a fallback to an **exact match against the source's results-title date**. Still reject any present but contradictory publication date. Do not accept a 200 response without the correct SmackDown results title.
2. Add tests equivalent to `tests/test_wwe_historical_source_compat.py`, particularly title-only historical dates, embedded-video exclusion, and winner-only portraits.
3. Validate official page segment order and `following` relationships. October 23 tested 5 completed matches and 11 on-air cards.
4. Extract candidate records into `wrestling_episode_archive` with `draft` status; do not automatically advance `reviewed` or replace the current approved TV episode.
5. For true hands-off 24/7 use, Floot Free does not run its paid scheduled jobs. An independent low-cost/free source-check scheduler plus secure authenticated private archive ingestion needs separate engineering. Existing preview-window timers do not operate while the window is closed.

## Tests and workflow

`python -m unittest discover -s tests -p 'test_wwe_historical_source_compat.py' -v`

Workflow: `.github/workflows/validate-smackdown-history-staging.yml` (read-only `contents` permission, staging branch only; no artifacts uploaded, no site deployment).

Do not merge staging to `main` or publish content without separate testing and authorization.
