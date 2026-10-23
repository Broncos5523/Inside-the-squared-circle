# Reviewed facts bridge — v4.30 preview

This is an **opt-in human-reviewed import**, not an automatic weekly match-result service. The production homepage and v4.29 are unchanged.

After a show **finishes broadcasting**, a reviewer checks a dated recap for that exact show and TV airdate. Record only brief original factual paraphrases, never article excerpts, copied recaps, images, or scraped WWE/TNA pages. Obtain sufficient permission to use any source content beyond bare facts.

Create a JSON file with:
- schema_version: 1
- mode: REVIEWED_WEEKLY_EPISODE_FACTS_V1
- reviewed_at_et: ISO 8601 timestamp with timezone offset *after* the broadcast, for example 2026-10-23T00:30:00-04:00
- programs: up to six dated show objects

Each show object needs show_id (raw, smackdown, nxt, aaa, tna or evolve), airdate (YYYY-MM-DD), review_method set to MANUAL_SOURCE_REVIEW, reuse_basis set to FACT_ONLY_PARAPHRASE, source_name, source_url, and arrays results and developments.

A match-result object needs text (a short definite outcome statement), match_type, and status set to REPORTED_UNVERIFIED. A storyline object needs text, type, and the same status. Either may contain a source_url override for fact-level provenance. Retain full URLs **in JSON only**; they never appear as clickable source links on the board.

Import (explicitly, never from the automated schedule collector):

    python -m proof.reviewed_recaps --input path/to/review.json --out web/data/reviewed-recaps.json

Validate without writing:

    python -m proof.reviewed_recaps --verify

Review the resulting JSON and commit it to the repository. GitHub Actions validates it before deployment. The v4.30 preview will show reviewed records only for the exact last completed episode and at most 14 days after that airdate. No record is ever copied to the next episode. AAA event card facts require explicit TV-week mapping. Evolve remains recap-only. If the new feed is empty, the original dated editorial sources are retained as fallback, without pretending to be automatic.

The initial published file is deliberately empty — no invented winners, talent, segments or storylines. Source host allowlist changes require code review. The validator checks structural safeguards and timestamps but **cannot certify the truth** of a human claim.

Source research as of Oct 23: TheSportsDB permits reuse of official API output subject to its September 2026 terms and third-party restrictions, but available weekly result content is incomplete. OWDB and a separately MIT-licensed codebase have not been cleared as reliable and reusable modern weekly results datasets. Do not wire either into a live results feed without documented rights, exact dated coverage, and provenance checks.
