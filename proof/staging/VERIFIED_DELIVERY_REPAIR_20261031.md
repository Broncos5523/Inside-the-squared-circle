# Verified delivery repair

The owner reported an integrity error immediately after the AAA cycle during device testing. Fresh hosted RAW, NXT, TNA, SmackDown and AAA responses match the published delivery hashes. RAW also matches under desktop, iPhone and Silk user agents. The exact device failure has not been reproduced by a fresh server request.

The old player fetched reusable `.html` URLs with the browser's default cache policy. Its lifecycle test harness omitted Web Crypto and therefore never exercised the checksum branch. The repair preserves the integrity requirement and all approved bytes:

- Each of the 67 distinct delivery files has an identical binary payload addressed by its SHA-256 digest. All 68 board records are covered.
- The loader uses that immutable payload URL and `cache: no-store`, verifies the received bytes before decoding, and retries a failed transfer once with an additional cache-busting parameter.
- A second mismatch remains rejected. Playback can continue to the next valid board; no unverified HTML is executed.
- The optimizer creates the payloads after regenerating delivery files. Source verification checks every payload against its approved delivery bytes.
- The lifecycle harness now uses real Web Crypto. Regressions cover AAA-to-RAW recovery after a corrupt first response, persistent tamper rejection, continued rotation, and missing crypto support.

This addresses stale or rewritten HTML transport without asserting that either has been conclusively observed on the owner's device. A device retest remains required before the production handoff.
