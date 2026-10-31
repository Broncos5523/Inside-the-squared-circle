# Source-backed staging library

This is a continuation of the recovered Inside the Squared Circle project. The 68-slot registry contains 67 source-backed slots and a held final Evolve board. All original HTML and mapped artwork remain byte-for-byte preserved beneath `originals/`.

`index.html` provides a phone review of all source-backed designs. The separate active playlist admits sourced current programming only; archive examples never become current results or champions. `?view=tv&mode=archive&id=SLOT_ID&play=1` is an explicitly labeled design-review rotator, not the production playlist. `?view=tv&mode=active` runs only eligible current programming.

`board-adapter.js` changes URL delivery in the in-memory iframe response. It does not edit original HTML, artwork, layout, fonts, portraits, animations or colors. Assets remain deduplicated; materializing all 1,585 routes would exceed the intended static hosting size. Original URL paths are resolved to the original 530 content-hashed assets.

`proof/staging/optimize_assets.py` creates cached delivery copies by referring to the exact image/font bytes already present in the recovered shared artwork. It reduces 292 MB of embedded source HTML to about 1.36 MB of delivery HTML without adding or re-encoding artwork. Original HTML remains intact under `originals/`; `delivery-assets.json` records every byte hash. Run the optimizer after regenerating the source library.

Public hosting clearance was confirmed by the user on October 30, 2026. Source credits are retained. Live facts remain independently gated by source/date and approval, regardless of public-hosting permission.

The integration branch does not automatically create a GitHub Pages preview. The separate public staging review at `https://isc-original-board-review.bigaz5523.chatgpt.site` serves the review UI and retrieves the exact original artwork and current-content feed from this integration branch. Delivery HTML hashes are checked in the browser, and all original HTML/artwork hashes are checked in CI. This does not deploy or change the production Pages site. The existing `refresh-and-publish.yml` remains unchanged. Scheduled Actions execute from the default branch; the new staging workflow runs on pushes/manual dispatch, but its cron is not active until an approved merge. Continuous unattended collection is still a release gate.

Browser QA passed for all 67 recovered slots at a 720 × 1280 internal board size with no broken visible images. SummerSlam preview Night One and Night Two select separately; Night Two remained selected for over three minutes, and review rotation advanced automatically. The wrapper corrects duplicated recovered SummerSlam Results labels; original source HTML remains unchanged.

Release holds: final corrected Evolve source; version-specific PLE Results approval; current champion/belt verification; missing SummerSlam preview and Survivor Series results JSON; complete automatic current results/event ingestion; actual iPhone Safari and Fire TV Silk device validation. No production launch is authorized by the staging build.
