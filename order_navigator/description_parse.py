"""
Parse Item description blocks: isotopes, activity tolerance, dimensions, fill
(line-anchored to avoid false matches), then a single *Description remainder* string
with structured bits removed (no more Desc L1… columns).
"""

from __future__ import annotations

import re
from typing import TypedDict

import pandas as pd

_GUNK = re.compile(r"[\uFFFD\u00a0\t]+")

# Co-60, Tc-99m, H-3 — [ \t] only (not \n) so lines don't merge into one fake token
_ISOTOPE_RE = re.compile(
    r"(?<![0-9A-Za-z])"  # allow / before Pb in "w/Pb-210"
    r"([A-Z](?:[a-z])?[ \t]*-[ \t]*\d{1,4}[a-z]?)"
    r"(?![0-9A-Za-z-])",
    re.IGNORECASE,
)

# Activity units in radioactivity export text
_UNIT = re.compile(
    r"(?i)([kK]Bq|Bq|mCi|uCi|nCi|GBq|MBq|mBq|pCi|Ci)\b"
)

# Whole-line labels (multiline) — we extract value then drop the line from remainder
_LINE_ACTIVITY = re.compile(
    r"(?im)^[ \t]*Activity\s*Tolerance\s*:\s*([^\r\n]*?)\s*$", re.IGNORECASE
)
_LINE_OVERALL = re.compile(
    r"(?im)^[ \t]*Overall\s*Dimensions?\s*:\s*([^\r\n]*?)\s*$", re.IGNORECASE
)
_LINE_ACTIVE = re.compile(
    r"(?im)^[ \t]*Active\s*Dimensions?\s*:\s*([^\r\n]*?)\s*$", re.IGNORECASE
)
# After start of string *or* any newline, so a Fill line does not have to be row 1
_LINE_FILL = re.compile(
    r"(?im)(?:^|\n)\s*Fill\s*Volume\s*:\s*([^\r\n]+?)\s*(?=\n|$)", re.IGNORECASE
)
_ACTIVITY_LOOSE = re.compile(
    r"Activity\s*Tolerance\s*:\s*([^\r\n]+)", re.IGNORECASE
)
_OVERALL_LOOSE = re.compile(
    r"Overall\s*Dimensions?\s*:\s*([^\r\n]+)", re.IGNORECASE
)
_ACTIVE_LOOSE = re.compile(
    r"Active\s*Dimensions?\s*:\s*([^\r\n]+)", re.IGNORECASE
)

# Strip these whole lines from remainder (labels only; values already taken)
_LINE_REMOVE = re.compile(
    r"(?im)^[ \t]*"
    r"(?:Activity\s*Tolerance|Overall\s*Dimensions?|Active\s*Dimensions?|Fill\s*Volume)\s*:"
    r"[^\r\n]*$",
    re.IGNORECASE,
)


class DescriptionFields(TypedDict):
    isotopes: str
    activity_tolerance: str
    overall_dimensions: str
    active_dimensions: str
    fill_volume: str
    description_remainder: str


COL_ISOTOPES = "Isotopes"
COL_ACTIVITY_TOLERANCE = "Activity tolerance"
COL_OVERALL_DIMS = "Overall dimensions"
COL_ACTIVE_DIMS = "Active dimensions"
COL_FILL_VOLUME = "Fill Volume"
COL_REMAINDER = "Description remainder"


def _norm_ws(s: str) -> str:
    return re.sub(r"[ \t\n\r]+", " ", s).strip()


def _trim_field(s: str) -> str:
    t = s.strip()
    t = t.rstrip(" \t,;|·")
    for junk in ("\u00a0", "\u200b", "�"):
        t = t.replace(junk, " ")
    return t.strip()


def _normalize_isotope_label(raw: str) -> str:
    t = re.sub(r"[\n\r]+", " ", raw)
    t = re.sub(r"[ \t]*-[ \t]*", "-", t, count=1)
    t = t.strip()
    m = re.match(r"^([A-Z](?:[a-z])?-)(\d{1,4})([a-z])?$", t, re.IGNORECASE)
    if m and m.group(1):
        pre, d, suff = m.group(1), m.group(2), m.group(3) or ""
        pre = (pre[0].upper() + pre[1:].lower()) if pre[0].isalpha() else pre
        return f"{pre}{d}{suff}"
    return t


def _line_end(s: str, start: int) -> int:
    e = s.find("\n", start)
    return len(s) if e < 0 else e


def _isotope_base_key(core: str) -> str:
    d = _normalize_isotope_label(re.sub(r"[\n\r\t]+", " ", core))
    return re.sub(r"[^a-z0-9]+", "-", d.lower().strip(" -"))


def _tail_len_after_isotope(s: str, c0: int, c1: int) -> int:
    """
    Length of activity to keep *with* the isotope, same line only, immediately after
    the symbol: ' added at 1.5kBq', or the first/second activity (e.g. 10.26kBq (0.28 uCi)).
    """
    le = _line_end(s, c0)
    rest = s[c1:le]
    t = rest.lstrip()
    if not t or t[0] in ",;:":
        return 0
    i_add = re.search(r"(?i)added at", rest)
    if i_add is not None:
        seg = rest[i_add.start() :]
        u = _UNIT.search(seg)
        if u:
            return i_add.start() + u.end()
        return 0
    u1 = _UNIT.search(rest, 0)
    if u1 is None or u1.start() > 100:
        return 0
    e1 = u1.end()
    u2 = _UNIT.search(rest, e1)
    if u2 is not None and u2.start() - e1 < 3:
        return u2.end()
    p2 = re.match(
        r"^\s*\([^)]*?(?:uCi|nCi|Bq|kBq|mCi|kBq)[^)]*\)\s*",
        rest[e1:],
        re.IGNORECASE,
    )
    if p2:
        return e1 + p2.end()
    return e1


def _w_prefix_len(s: str, core_a: int) -> int:
    if core_a >= 2 and s[core_a - 2 : core_a].lower() == "w/":
        if core_a == 2 or s[core_a - 3] in " \n\t,;+([{\r":
            return 2
    return 0


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not spans:
        return []
    spans = sorted(spans, key=lambda t: t[0])
    out: list[tuple[int, int]] = [spans[0]]
    for a, b in spans[1:]:
        la, lb = out[-1]
        if a <= lb:
            out[-1] = (la, max(lb, b))
        else:
            out.append((a, b))
    return out


def _isotope_displays_and_spans(s: str) -> tuple[list[str], list[tuple[int, int]]]:
    """
    Each isotope may include w/ and adjacent same-line activity.
    One *display* string per base isotope; longest fragment wins. Every physical
    match (e.g. Pb-210 in a list and w/Pb-210 added at …) gets a strip span.
    """
    by_key: dict[str, str] = {}
    spans: list[tuple[int, int]] = []
    order_keys: list[str] = []
    for m in _ISOTOPE_RE.finditer(s):
        core = m.group(1)
        c0, c1 = m.start(1), m.end(1)
        pre = _w_prefix_len(s, c0)
        a0 = c0 - pre
        tl = _tail_len_after_isotope(s, a0, c1)
        a1 = c1 + tl
        k = _isotope_base_key(core)
        if not k:
            continue
        display = re.sub(r"\s+", " ", s[a0:a1]).strip()
        if not display:
            continue
        spans.append((a0, a1))
        if k not in by_key or len(display) > len(by_key[k]):
            by_key[k] = display
        if k not in order_keys:
            order_keys.append(k)
    displays = [by_key[k] for k in order_keys if k in by_key]
    return displays, _merge_spans(spans)


def _isotopes_collect_all(s: str) -> list[str]:
    d, _ = _isotope_displays_and_spans(s)
    return d


def _first_line_field(
    s: str,
    line_re: re.Pattern[str],
    loose_re: re.Pattern[str],
) -> str:
    m = line_re.search(s)
    if m:
        return _trim_field(m.group(1))
    m2 = loose_re.search(s)
    if m2:
        return _trim_field(m2.group(1))
    return ""


def _fill_value(s: str) -> str:
    """Line-anchored only so 'volume' in other text is not captured."""
    m = _LINE_FILL.search(s)
    return _trim_field(m.group(1)) if m else ""


def _strip_matched_isotope_spans(working: str, spans: list[tuple[int, int]]) -> str:
    w = working
    for a, b in sorted(spans, key=lambda t: t[0], reverse=True):
        w = w[:a] + " " + w[b:]
    w = re.sub(r"[ \t]+", " ", w)
    return w


def _strip_dangling_separators(s: str) -> str:
    s = re.sub(r"^\s*[,;]+", "", s)
    s = re.sub(r"[,;]+\s*$", "", s)
    return re.sub(r"\n\s*[,;]+\s*\n", "\n", s)


def parse_item_description_text(text: object) -> DescriptionFields:
    """
    Build structured fields + a single *description_remainder* string. Structured
    line content and isotope tokens are removed from the remainder so they are not
    repeated elsewhere.
    """
    empty: DescriptionFields = {
        "isotopes": "",
        "activity_tolerance": "",
        "overall_dimensions": "",
        "active_dimensions": "",
        "fill_volume": "",
        "description_remainder": "",
    }
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return empty

    s = str(text)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = _GUNK.sub(" ", s)

    isotopes, iso_spans = _isotope_displays_and_spans(s)
    isos_joined = ", ".join(isotopes) if isotopes else ""

    act = _first_line_field(s, _LINE_ACTIVITY, _ACTIVITY_LOOSE)
    oa = _first_line_field(s, _LINE_OVERALL, _OVERALL_LOOSE)
    ad = _first_line_field(s, _LINE_ACTIVE, _ACTIVE_LOOSE)
    fv = _fill_value(s)

    work = _strip_matched_isotope_spans(s, iso_spans)
    work = _LINE_REMOVE.sub("", work)
    work = re.sub(r"\n{3,}", "\n\n", work)
    work = _strip_dangling_separators(work)
    work = re.sub(r"^\s*[,;|·]+\s*", "", work, flags=re.M)
    work = re.sub(r"^\s*[,;|·]+\s*$", "", work, flags=re.M)
    work = re.sub(r"(?m)^[ \t,;|·]+$", "\n", work)
    work = re.sub(r"\n{3,}", "\n", work)
    rem = " ".join(
        part.strip()
        for part in re.split(r"[\n]+", work)
        if part and part.strip(" ,;|·\t")
    )
    rem = re.sub(r"\s+[,;|]\s+([,;|])", r" \1", rem)
    rem = _norm_ws(rem)
    # Any leftover text that still contains a full isotope+activity display (substring match)
    for display in isotopes:
        pat = re.escape(_norm_ws(display))
        rem = re.sub(pat, " ", rem, flags=re.IGNORECASE)
    rem = _norm_ws(rem)
    rem = rem.strip(" ,;|·")

    return {
        "isotopes": isos_joined,
        "activity_tolerance": act,
        "overall_dimensions": oa,
        "active_dimensions": ad,
        "fill_volume": fv,
        "description_remainder": rem,
    }


def add_parsed_description_columns(
    df: pd.DataFrame,
    source_col: str = "Item description",
) -> pd.DataFrame:
    """Add Isotopes, tolerance, dimensions, Fill Volume, and Description remainder."""
    if source_col not in df.columns:
        return df
    out = df.copy()
    keys: list[tuple[str, str]] = [
        (COL_ISOTOPES, "isotopes"),
        (COL_ACTIVITY_TOLERANCE, "activity_tolerance"),
        (COL_OVERALL_DIMS, "overall_dimensions"),
        (COL_ACTIVE_DIMS, "active_dimensions"),
        (COL_FILL_VOLUME, "fill_volume"),
        (COL_REMAINDER, "description_remainder"),
    ]
    bucket: dict[str, list[str]] = {c: [] for c, _ in keys}
    for val in out[source_col]:
        f = parse_item_description_text(val)
        for col_name, fkey in keys:
            bucket[col_name].append(f[fkey])  # type: ignore[literal-required]
    for col_name, _ in keys:
        out[col_name] = bucket[col_name]
    return out
