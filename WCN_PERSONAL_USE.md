# Wrestling Central News: personal-display permission and integration

On October 22, 2026, Wrestling Central News (WCN) gave the project owner
written permission to automatically collect and cache WCN public match-card
information for a **private, noncommercial home display**, free of charge,
subject to: visible source credit **Wrestling Central News
(wrestlingcentralnews.com)**; reasonable checks (~15-minute intervals or
slower); and asking WCN first for public or commercial use.

The approved feed is https://wrestlingcentralnews.com/feed.xml and upcoming
events are listed at https://wrestlingcentralnews.com/upcoming/.

The new collector (proof/wcn_private_cards.py) reads RSS metadata and
the Card & preview section of WCN's **exact dated weekly event pages**.
It extracts only short deterministic pairs ("X vs. Y"), without copying
whole sentences, hallucinating additional matches, importing results,
or mapping AAA's multiday event card to one television week. No other
publishers are scraped. It refreshes no faster than 15 minutes from
a cached file.

## Personal local display

Run from the repository root:

    python -m proof.wcn_private_cards --snapshot web/data/snapshot.json --out web/data/wcn-match-cards-private.json

On your own local server, the V4.32 private-WCN preview will read this
ignored JSON file. It retains the existing approved look and adds WCN's
short, date-matched card entries with the requested small source credit,
no clickable links, and the usual spoiler/date safeguards.

**Not published to public GitHub Pages.** The ordinary hosted V4.32 preview
falls back to existing approved feeds. GitHub Pages is publicly accessible;
the publisher did not grant public redistribution in its email. Before
publicly publishing cached WCN data, obtain express additional permission.

GitHub Actions runs only an ephemeral WCN connectivity/coverage audit to
ensure the collector keeps working. It writes under /tmp and deliberately
excludes the WCN result from repository commits and Pages deployment.
