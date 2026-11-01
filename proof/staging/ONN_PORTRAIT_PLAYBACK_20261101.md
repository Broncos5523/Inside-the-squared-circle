# ONN portrait playback

The playback target changed from Fire TV/Silk to an ONN streaming stick using TV Bro. The owner supplied a photo showing RAW loading successfully, but sideways and letterboxed on a physically upright TV receiving a landscape signal.

In TV playback mode the outer 720 x 1280 surface now rotates 90 degrees counterclockwise when the viewport is wider than it is tall. Its scale is computed from the rotated dimensions, keeping the whole board visible and centered. A 1280 x 720 signal fills the display at scale 1. Portrait phone viewports and the review/library UI retain their existing orientation.

Optional `rotate=none`, `rotate=left`, or `rotate=right` URL settings support different physical mounting directions. The default needs no extra parameter. Resizing changes the outer surface only; it does not rebuild the iframe, reload the source, or restart card playback.

All approved HTML, artwork, ticker design, card timing, source checks, and immutable verified-delivery payloads remain unchanged. ONN/TV Bro is the current device for the remaining physical playback test and production handoff.
