# Automatic champion changes — November 3, 2026

Previously, the collector compared current holders to the original design catalog and withheld an entire show on a change. It now treats the catalog as title, belt, and layout configuration. Current WWE holders come from the dedicated current-holder field; TNA holders are paired with their title in Meet Our Champions; AAA changes require matching current-title sections from both sources.

New holders resolve exact names against approved portrait inventory, preferring the show's approved results image. Runtime route aliases inject those assets into unchanged championship HTML. No original source, image, belt, or route inventory is modified. Unsupported identities and unavailable titles are withheld independently, leaving other verified titles rotating. No previous holder's reign date is assigned to a replacement; unknown dates display the native dash. Evolve remains deferred.

Validation: 89 staging/production Node checks pass. Immutable verification confirms 68 boards, 544 shared assets, and 1,618 routes. Live official WWE extraction confirms Ethan Page with November 2 reign start and the approved RAW results portrait. Live TNA markup yields seven title-specific slots. Regression coverage includes automatic singles and team changes, partial source failure, changed holders without artwork, missing reign dates, two-source AAA disagreement, and runtime asset aliasing without inventory mutation.

Uses existing four-hour production refresh and five-minute browser feed checks. Existing clients need one reload to load adapter version 20261103-auto-champions-13.
