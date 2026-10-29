"""Read-only WWE SmackDown historical-results compatibility parser.

STAGING ONLY: produces unapproved drafts, never publishes feeds, graphics, or
approved boards. Supports older WWE pages with no "Published on" heading.
"""
from __future__ import annotations

from datetime import date, datetime
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
from zoneinfo import ZoneInfo


class SourceIntegrityError(ValueError):
    pass


def clean(s):
    return " ".join(s.replace("\xa0", " ").split())


MONTHS = dict(zip(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), range(1, 13)
))
DATE_RE = re.compile(r"\b([a-z]{3,9})\.?\s+(\d{1,2}),?\s+(20\d\d)\b", re.I)
MATCH_RE = re.compile(r"^(.+?)\s+def(?:\.|eated)?\s+(.+)$", re.I)
URL_RE = re.compile(r"^https://www\.wwe\.com/shows/smackdown/(20\d\d-\d\d-\d\d)/results$")


def parse_date(text):
    match = DATE_RE.search(text)
    if not match:
        return None
    month = MONTHS.get(match[1][:3].lower())
    try:
        return date(int(match[3]), month, int(match[2])) if month else None
    except ValueError:
        return None


class Article(HTMLParser):
    """Read direct child <p> elements of WWE's field--name-body, not videos."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.published = ""
        self.h3 = []
        self.depth = 0
        self.body_depth = None
        self.p = None
        self.strong = 0
        self.in_title = False
        self.in_h3 = False
        self.script = 0
        self.paragraphs = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style"):
            self.script += 1
        if tag == "title":
            self.in_title = True
        if tag == "h3":
            self.in_h3, self.h3 = True, []
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "div":
            self.depth += 1
            if self.body_depth is None and "field--name-body" in (
                attrs.get("class") or ""
            ).split():
                self.body_depth = self.depth
        if tag == "p" and self.body_depth == self.depth:
            self.p = []
        if tag == "strong" and self.p is not None:
            self.strong += 1
        if tag == "br" and self.p is not None:
            self._append(" ")

    def _append(self, text):
        kind = "heading" if self.strong else "text"
        if self.p and self.p[-1][0] == kind:
            old_kind, old_text = self.p.pop()
            self.p.append((old_kind, old_text + text))
        else:
            self.p.append((kind, text))

    def handle_data(self, text):
        if self.script:
            return
        if self.in_title:
            self.title += text
        if self.in_h3:
            self.h3.append(text)
        if self.p is not None:
            self._append(text)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "h3":
            self.in_h3 = False
            value = clean("".join(self.h3))
            if "Published on" in value:
                self.published = value
        if tag == "strong":
            self.strong = max(0, self.strong - 1)
        if tag == "p" and self.p is not None:
            chunks = [(kind, clean(text)) for kind, text in self.p if clean(text)]
            if chunks:
                self.paragraphs.append(chunks)
            self.p = None
            self.strong = 0
        if tag == "div":
            if self.depth == self.body_depth:
                self.body_depth = None
            self.depth = max(0, self.depth - 1)
        if tag in ("script", "style"):
            self.script = max(0, self.script - 1)


def discover(archive_html, as_of=None):
    reader = Article()
    reader.feed(archive_html)
    if "archive" not in reader.title.casefold():
        raise SourceIntegrityError("WWE archive title not found")
    as_of = as_of or datetime.now(ZoneInfo("America/New_York")).date()
    dates = set()
    for url in reader.links:
        match = re.fullmatch(
            r"/shows/smackdown/(20\d\d-\d\d-\d\d)(?:/results)?/?", url
        )
        if match:
            try:
                dates.add(date.fromisoformat(match[1]))
            except ValueError:
                pass
    if not dates:
        raise SourceIntegrityError("No dated official SmackDown archive entries")
    past = sorted((d for d in dates if d <= as_of), reverse=True)
    future = sorted((d for d in dates if d > as_of), reverse=True)
    return {
        "latest_eligible": past[0].isoformat() if past else None,
        "eligible": [d.isoformat() for d in past[:12]],
        "future_previews": [d.isoformat() for d in future],
    }


def extract(html, expected_date, source_url):
    """Return source-ordered draft only; never mark it verified or on-air."""
    match = URL_RE.fullmatch(source_url)
    if not match or match[1] != expected_date:
        raise SourceIntegrityError("Wrong official source or date")
    try:
        date_expected = date.fromisoformat(expected_date)
    except ValueError as exc:
        raise SourceIntegrityError("Invalid episode date") from exc
    if len(html) < 250 or len(html) > 2_000_000:
        raise SourceIntegrityError("Invalid source document size")
    article = Article()
    article.feed(html)
    title = clean(article.title)
    if not re.search(r"SmackDown results\s*[:,]?", title, re.I):
        raise SourceIntegrityError("Final results article not found")
    title_date = parse_date(title)
    stamped_date = parse_date(article.published)
    # The current results page has a publication <h3>, but older results
    # commonly have only "SmackDown results: Oct. 16, 2026" in the title.
    if title_date != date_expected or (
        stamped_date is not None and stamped_date != date_expected
    ):
        raise SourceIntegrityError("Official results date mismatch")
    if len(article.paragraphs) < 2:
        raise SourceIntegrityError("No source article body")
    events = []
    for paragraph in article.paragraphs:
        for kind, value in paragraph:
            if kind == "heading":
                match = MATCH_RE.match(value)
                winners, losers, finish, changed = [], [], None, False
                if match:
                    winners = [
                        clean(name) for name in re.split(r"\s*(?:,|&)\s*", match[1])
                        if clean(name)
                    ]
                    rhs = match[2]
                    finish = "disqualification" if re.search(
                        r"\bby disqualification\b", rhs, re.I
                    ) else None
                    changed = bool(re.search(r"\bto capture\b", rhs, re.I))
                    rhs = re.split(
                        r"\s+(?:by disqualification|in a |in an |to capture|to win)\b",
                        rhs, maxsplit=1, flags=re.I
                    )[0]
                    losers = [
                        clean(name) for name in re.split(r"\s*(?:,|&)\s*", rhs)
                        if clean(name)
                    ]
                events.append({
                    "order": len(events) + 1,
                    "kind": "match" if winners and losers else "storyline",
                    "source_headline": value[:250],
                    "winners": winners, "losers": losers,
                    "finish": finish, "title_change": changed,
                    "details": [], "portrait_rule": "winners_only" if winners else "review",
                    "requires_editorial_review": True,
                })
            elif events and value:
                if re.match(r"(?:Seconds after the bell|After the match)\b", value, re.I):
                    if events[-1]["kind"] == "match":
                        previous_id = events[-1]["order"]
                        events.append({
                            "order": len(events) + 1,
                            "kind": "storyline", "source_headline": "POST-MATCH FALLOUT",
                            "winners": [], "losers": [], "finish": None,
                            "title_change": False, "details": [],
                            "portrait_rule": "review", "requires_editorial_review": True,
                            "follows": previous_id,
                        })
                if len(events[-1]["details"]) < 6:
                    events[-1]["details"].append(value[:420])
    # Keep officially announced next-week title stakes after their causal
    # final match, without misclassifying them as a second finished match.
    if events and events[-1]["kind"] == "match":
        final = events[-1]
        evidence = next((
            line for line in final["details"]
            if re.search(r"\bnext week\b", line, re.I)
            and re.search(r"\b(?:title|championship) match\b", line, re.I)
        ), None)
        if evidence:
            final["causes_next"] = True
            events.append({
                "order": len(events) + 1,
                "kind": "storyline",
                "source_headline": "WHAT COMES NEXT: TITLE MATCH ANNOUNCEMENT",
                "winners": [], "losers": [], "finish": None,
                "title_change": False, "details": [evidence],
                "portrait_rule": "review", "requires_editorial_review": True,
                "follows": final["order"],
            })
    if not events or sum(e["kind"] == "match" for e in events) < 1:
        raise SourceIntegrityError("No official completed match headings")
    summary = "\n".join(
        e["source_headline"] + "|" + "|".join(e["details"]) for e in events
    )
    return {
        "schema_version": 1, "show": "smackdown", "episode_date": expected_date,
        "source_url": source_url,
        "date_evidence": "publication_and_title" if stamped_date else "title_only",
        "events": events, "match_count": sum(e["kind"] == "match" for e in events),
        "review_status": "draft", "safe_for_live_board": False,
        "automatic_editorial_approval": False,
        "digest_sha256": sha256(summary.encode("utf-8")).hexdigest(),
    }
