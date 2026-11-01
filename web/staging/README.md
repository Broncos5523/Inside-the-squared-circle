# Approved wrestling board library

All 68 source boards have been recovered. The 543 shared artwork files and 1,617 logical asset routes include the exact user-supplied Big Mami, Chantel Monroe, and Zero / Agent Zero portraits. Original HTML and artwork remain unchanged under `originals/`; `delivery/` contains smaller HTML copies referencing the exact decoded original image and font bytes.

The active player uses source-backed current programming. It includes the latest verified weekly results, the nearest weekly preview, verified event previews within 14 days, and verified event results within seven days. All 68 designs remain available for archive review; design approval alone does not make an old example eligible for live TV. Evolve and other boards remain held whenever their current source checks fail.

The main Pages entry opens `staging/?view=tv&mode=active`. `previous-display.html` preserves the previous main entry byte for byte. Explicit `?mode=archive` URLs remain available for design review.

The production workflow first collects schedules and the existing permitted feeds, then calls the approved-board collector with `ISC_LOCAL_FEED_DIR=web/data`. That collector uses the schedules produced by the same run and still verifies official external sources. A missing local reviewed feed cannot silently fall back to the previous deployment. Collection runs on the existing four-hour schedule and manual dispatch. The player checks the published feed every five minutes and rejects feeds older than six hours.

`proof/staging/build-release.mjs` creates `.pages-output/` from the existing web tree. It keeps all 68 delivery boards, verifies all 543 shared artwork hashes and every delivery hash, and omits the large embedded source HTML copies. GitHub Pages serves the artwork locally under the project subpath. The repository retains all original sources for backup and integrity verification.

The staging validation workflows remain push/manual checks and do not independently schedule production writes. The production workflow commits refreshed programming together with the existing feeds and publishes one matching Pages artifact. Its post-deployment check compares the entry page, live feed, playback scripts, and both new portrait files to that artifact.

Public hosting clearance was confirmed by the owner on October 30, 2026. The separate sports-board project is outside this repository and is unchanged. Actual ONN/TV Bro playback remains a device check; desktop browser QA does not substitute for it.
