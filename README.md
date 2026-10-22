# Man Cave Sports Book Presents: Inside the Squared Circle

**“When the bell rings, it gets real.”**

## GitHub staging deployment — October 22, 2026

This repository now contains a **limited, source-conscious cloud research display**. It is an independent wrestling project and makes **no changes to the approved 28 sports boards**.

### Files already uploaded

- `web/index.html` — portrait 9:16 test screen, suitable for trying in Amazon Fire TV Silk; rotates RAW, SmackDown, NXT, AAA, TNA, plus a less frequent Evolve recap slot.
- `web/data/snapshot.json` — explicit dated seed placeholder; **not yet live** until GitHub Actions completes the first collection.
- `.github/workflows/refresh-and-publish.yml` — scheduled every four hours, manual trigger and push trigger; fetches six TVmaze show schedules, retains previous schedule info on partial errors, commits the latest JSON, and deploys GitHub Pages.

**This GitHub staging build is smaller than the separately packaged v4.3 local research archive.** The v4.3 source archive and full 13-unit-test suite have not yet been copied into this repository. Do not interpret this as the final approved graphics.

### One-time setup

1. Repository **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Repository **Settings → Actions → General → Workflow permissions**: grant **Read and write permissions** only if the existing workflow-scoped `contents: write` token is insufficient for the scheduled cache commit.
3. Repository **Actions → Refresh schedules and publish display → Run workflow**. Verify each step succeeds, including Pages deployment.
4. Once GitHub Pages is live, check:
   **https://broncos5523.github.io/Inside-the-squared-circle/**
5. Test that published URL in Fire TV Silk at portrait orientation.

A public repository is used for GitHub Free Pages. Never commit passwords or private data. Scheduled workflows are best-effort and GitHub can delay or disable them.

### What's real and what's missing

**Implemented:** Public TVmaze show schedule refresh, five-show/recap rotation, a 9:16 static browser surface, last-known episode fallback, and clear unknown-card labeling.

**Not implemented:** Automatically verified wrestling matches, title changes, appearances, results, PLE content, editorial rights to scrape WWE/TNA, or the approved show-specific master branding. Do not conflate published schedules with verified advertised matches.

### Attribution and rights

Schedule information: [TVmaze API](https://www.tvmaze.com/api), CC BY-SA (check applicable attribution and derivative licensing requirements). There are no copied wrestler headshots, protected event broadcast artworks, or publisher article text in this repository.



## Candidate match-card ingestion (research-only, October 22, 2026)

An additional automatically scheduled **TheSportsDB API** research pipeline is now present:

- `proof/card_intake.py` fetches possible match mentions using the documented API, filtered to the TVmaze **local broadcast date, promotion and show identity**. Because UTC and local dates can differ for TNA, it checks the appropriate additional UTC calendar day.
- RAW, SmackDown, NXT and TNA are searched where they can be safely matched. **AAA multi-week edited broadcasts and Evolve recaps are deliberately excluded** from automatic event-to-show association.
- `tests/test_card_intake.py` checks 12 deterministic cases, including UTC/local discrepancies, rejected wrong leagues and dates, non-promotional text, duplicate events, outages, and no false match verification.
- `web/data/candidates.json` is updated by the existing GitHub Actions schedule **as research lead counts and evidence event links only**. It deliberately contains **zero verified matches and zero verified appearances**.
- `web/evidence-lab.html` is a separately labeled research monitoring page displaying source coverage and candidate mention counts. This is **not** the TV card.
- Existing `web/preview-v4-4.html` and `web/index.html` continue to display only the schedule, with no invented card.

**Evidence-lab URL after successful deployment:** https://broncos5523.github.io/Inside-the-squared-circle/evidence-lab.html

**TheSportsDB rights:** the official terms (2026-09-17) permit API content copying/modification subject to rights and attribution, but prohibit automated scraping of the website. This pipeline calls only the documented API. See https://www.thesportsdb.com/docs_terms_of_use.php

**What remains unresolved:** A qualified and permitted match-card announcement source, claim-level provenance/confirmation and cancellations, advertised talent/segments, show recaps and final approved broadcast assets. Research leads from TheSportsDB are **never described as WWE or TNA-confirmed information**.

### Data reliability

Episode numbers and timing can conflict between providers. The schedule collector relies on TVmaze's IDs and shows times as *provider-local*, not conclusively ET. The JSON timestamp indicates collection time, **not** independent verification of each announced match.

To protect the display, unverified match information is never filled in simply because the title is a weekly program.
