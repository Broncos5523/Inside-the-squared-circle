# V4.42 — real screenshot-driven QA repairs

Source: user's October 23 iPhone screenshot of V4.41.

**Observed defects:**
- LIVE footer displayed version 4.40 instead of the actual 4.41.
- Man Cave master tagline was clipped at the bottom of the masthead.
- A glowing ring rope crossed the nameplates of the real photographed wrestlers.
- Three-wrestler hero showed female match participants because source-matched
  participants overrode the editorial reference-cover trio. The user wants
  the SmackDown cover structure (LA Knight, Roman Reigns, Cody Rhodes) as
  a reference style, with actual upcoming match facts below it.

**Corrections:** Independent V4.42 QA preview restores an editorial visual
cover using three individually license-reviewed 2025 photos, while **clearly
marking them archival editorial photos, not advertised appearances**. The
card, championship watch, other matches, optional segment rows, schedule
and ticker remain entirely data-driven; no example-card facts are copied.
After-the-Bell still uses only the dated, human-reviewed recap facts, with
the actual names from that recap, and never uses the archival trio as
false past-show participants.

CSS extends the gold/silver masthead vertical area to prevent tagline clipping,
reduces giant letter heights slightly, moves the ring ropes behind people
rather than over their names, moves the nameplates above the rope, feathers
the photo edges and retains a visible attributed credit.

The long-standing hardcoded footer version bug is repaired in markup AND
runtime to V4.42. Earlier previews untouched.

Preview:
https://broncos5523.github.io/Inside-the-squared-circle/preview-v4-42-smackdown-reference-qa.html?show=smackdown&view=broadcast

Recap:
https://broncos5523.github.io/Inside-the-squared-circle/preview-v4-42-smackdown-reference-qa.html?show=smackdown&view=afterbell

No generated images, no new Google photos, no fake champions or standings.
The existing Real Man Cave official master-emblem asset is still unresolved;
the rejected checkerboard emblem remains excluded. This is a review,
not a user-approved gold master.

**Additional fix:** The lower right panel in the screenshot duplicated upcoming
matches from the left panel. V4.42 now uses previous week's date-gated,
reviewed storyline developments under LAST WEEK'S FALLOUT when available.
Without reviewed notes or advertised appearances, it shows one short neutral
program note instead of duplicated bouts. No raw article links are exposed.
