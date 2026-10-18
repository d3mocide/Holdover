"""A cheap guard for generated text: it must not contain numbers or capitalised words that are not in the facts it was given."""
import re


def ungrounded_terms(text: str, source: str) -> list[str]:
    """Numbers and capitalised words (other than sentence starts) in `text` that don't occur in `source`.
    A guard, not a proof: a hit means the text is discarded and the template is used instead."""
    src = source.lower()
    bad = [n for n in re.findall(r"\d[\d,.\-]*", text) if n.rstrip(".,-").lower() not in src]
    for sent in re.split(r"(?<=[.!?])\s+", text):
        for w in re.findall(r"(?<!^)(?<![.!?] )\b[A-Z][a-z]{2,}\b", sent):
            if w.lower() not in src:
                bad.append(w)
    return bad
