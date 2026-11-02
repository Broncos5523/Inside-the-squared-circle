# iPhone playback and portrait repair — October 31, 2026

The user reported missing SmackDown/NXT headshots and an iPhone app/browser exit after AAA results. Chrome continued to RAW; a physical iPhone crash has not been reproduced here.

## Changes

- Resolve both `assets/portraits/` and `assets/portrait-display/` through the existing approved shared portrait collection. Fixes Jade Cargill; Romeo Moreno, Noam Dar, Sean Legacy and Jackson Drake; and the same issue for other brands. Never substitute another wrestler.
- Build the design-gallery image DOM only when the design library is opened. TV playback does not construct its 68 image cards.
- Remove the prior iframe before fetching the next board, limiting overlapping board contexts and their timers/images.
- Prevent duplicate first-board loading and overlapping refresh requests; send only the relevant episode feeds to each iframe.
- Preserve all original HTML and artwork bytes. Apply changes to the playback wrapper only. Bust script caches for the repaired player.

## Validation

48 staging tests pass, including execution of the real portrait resolver for both asset-path formats, and playback lifecycle checks from AAA to RAW through a complete playlist loop. All 68 original HTML sources, 540 shared artwork files and 1,599 asset routes pass integrity verification.

## Remaining limit

No confirmed named Chantel Monroe portrait exists in the deployed collection or the inspected saved Evolve roster reference. Her result remains text-only. Live Evolve activation still depends on the dated source check. A device-side iPhone test is required to confirm the reported app exit is resolved.
