# Production handoff — October 31, 2026

The approved source is the 68-board library from staging commit `99acbf927ea1a50a13b64a1070b377f9b45ac707`, including the portrait and rotation repairs accepted by the owner. Production preparation starts from main commit `42015d148a8613ebddeb8e4e7cf201ac9294230b` and preserves its current schedule/research feeds.

## Result after approval

- The existing GitHub Pages main URL automatically opens the approved active player.
- The current main entry is retained at `previous-display.html` with identical bytes.
- The existing scheduled job collects fresh schedules, assembles source-backed current boards, verifies all artwork and delivery files, commits the matching feeds, and publishes them together.
- The main display serves its feed and artwork from GitHub Pages; it does not depend on the Sites review host or the staging branch.
- The source gates, exact approved graphics, winner-only portraits, complete result-card dwell time, iframe cleanup, and timer recovery remain intact.

## Release conditions

1. Passing source, playback, packaging, and existing research tests.
2. Successful same-run live collector verification and a fresh nonempty active feed.
3. Owner checks a complete rotation in Fire TV Silk, including a transition beyond AAA, TNA, Crown Jewel, Halloween Havoc, and the supplied portraits when their cards are eligible.
4. Explicit approval before changing main/production, as requested by the owner.

The production Pages workflow performs a further byte-for-byte published-artifact check after the approved merge. A failure before deployment leaves the prior deployment in place. A stale source feed remains gated rather than displaying archived examples as current.

## Rollback

Before merging, record the production main SHA. If the new root entry needs reverting, restore `web/index.html` from `web/previous-display.html` and rerun the Pages workflow. For a full rollback, revert the production handoff merge through a reviewed change. Do not reset or rewrite main history.

This document describes prepared behavior. It is not a claim that main has already been changed or that a physical Fire TV test has been completed.

## Device-test delivery repair

The owner reported an integrity error after AAA during device testing. The revised player fetches immutable SHA-256-named binary payloads with browser caching disabled, verifies the exact approved bytes, and retries a failed transfer once. The package verifier checks every payload. The original delivery HTML, layouts, and artwork remain unchanged. The production switch remains on hold for a device retest of this revision.
