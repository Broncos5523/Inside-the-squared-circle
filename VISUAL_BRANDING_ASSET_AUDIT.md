# Actual branding & wrestler image research — V4.36

**Authoritative design reference:** the user-supplied full-format wrestling
broadcast showboards (SmackDown, RAW, NXT, TNA, Evolve, etc). Their layout,
metallic Man Cave brand identity, show-specific logos, hero players, match
cards and arena mood are inspiration, NOT verified factual wrestling cards.

**Explicitly rejected:** the previously shown checkerboard standalone logo
is NOT an approved master logo. Never substitute it or claim approval.

The current GitHub code uses a styled typography-only Man Cave title; it
does NOT yet contain a user-approved final transparent master wordmark. The
V4.36 SmackDown masthead moves toward the steel/gold treatment without
claiming to be the approved final custom logo.

## First real show logo: SmackDown

Wikimedia file: https://commons.wikimedia.org/wiki/File:WWE_SmackDown_(2024)_Logo.svg

Described on Wikimedia Commons as the 2024+ SmackDown logo; listed public
domain as a simple text logo and trademarked. We use it as a program
identifier, never to imply WWE endorsement. The GitHub build downloads
and caches a Wikimedia-rendered PNG thumbnail. If licensing metadata or
file integrity differs, it fails closed to the existing text treatment.

## Real wrestler photo starters: 2025 event photographs

Every image below was independently reviewed on its Commons file page and
the build checks live metadata for **CC BY 2.0**. All four were photographed
by **Diego Serrano** at the 2025 Royal Rumble. This is NOT a claim that
the photographed attire, storyline or title is current in 2026.

- Chelsea Green: https://commons.wikimedia.org/wiki/File:Chelsea_Green_RR25_(2).jpg
- Roxanne Perez: https://commons.wikimedia.org/wiki/File:Roxanne_Perez_RR25.jpg
- Giulia: https://commons.wikimedia.org/wiki/File:Giulia_RR25.jpg
- Alexa Bliss: https://commons.wikimedia.org/wiki/File:Alexa_Bliss_RR25_(1).jpg

Attribution: **Diego Serrano**, licensed **CC BY 2.0**:
https://creativecommons.org/licenses/by/2.0/

Images are shown **only when a live, source-reviewed match participant name
is an exact identity match**. Tag groups, ringside names, unverified
appearances and unmatched wrestler names all fall back to the existing
typographic VS panels. Wrestler cutouts are a later step. Images are
unaltered source photographs visually fitted inside the board with CSS.

Build: python -m proof.approved_graphics

Result: web/assets/vetted/ and a JSON attribution manifest.

The actual SmackDown logo and photos are fetched from Commons, validated,
cached within the build, then committed and served from GitHub Pages. This
avoids direct remote requests from the Fire TV browser.

Other show logos are tracked in web/data/visual-source-registry.json; these
are NOT yet integrated or user-approved. No guessed AAA/TNA/Evolve
branding, fake belts, opponent imagery or rankings.

## Existing project protection

Preview: web/preview-v4-36-authentic-smackdown.html
Default/production web/index.html, V4.35, other-show identities and the
separate 28-board sports package are not modified. The WCN cache remains
private. New image attribution is text-only, without article links.

**Pending:** real portrait TV screen review; final approved Man Cave lockup.
