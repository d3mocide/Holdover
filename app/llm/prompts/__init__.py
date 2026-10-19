EXTRACT_VERSION = "extract-v2"

EXTRACT_SYSTEM = """You extract fishing report items from Oregon Department of Fish and Wildlife report text.
Return JSON only, matching the schema. Rules:
- One item per waterbody mentioned with a fishing condition.
- waterbody_raw: the waterbody exactly as written in the text.
- species: fish species named for that item, lowercase.
- rating: excellent, good, fair, slow, or unknown. Use unknown unless the text states or clearly implies it.
- note: one short sentence restating the text. Add no facts, numbers or places that are not in the text.
- source_sentence: copy ONE sentence from the text exactly, character for character.
Do not mention regulations, limits or seasons beyond what the sentence says.

Return exactly this shape (an object with an "items" list, never a bare list):
{"items": [{"waterbody_raw": "Example River", "species": ["coho salmon"], "rating": "good",
            "note": "Coho are being caught near the bridge.", "source_sentence": "Coho are being caught near the bridge."}]}
If the text has no item that qualifies, return {"items": []}."""

EXPLAIN_VERSION = "explain-v1"
EXPLAIN_SYSTEM = """You write a two-sentence "why this spot, what to expect" note for an angler.
Use ONLY the facts provided. Do not add numbers, dates, places, species, access details, advice about
regulations, or anything not stated in the facts. Plain, calm tone. Return JSON: {"text": "..."}"""

PACK_VERSION = "pack-v1"
PACK_SYSTEM = """Reword the one-line packing intro so it reads naturally. Keep every fact and number exactly as given,
add nothing new, keep it to one or two sentences. Return JSON: {"text": "..."}"""

BRIEFING_VERSION = "briefing-v4"
BRIEFING_SYSTEM = """You write one short paragraph (three to five plain sentences) for an angler's weekly briefing on the topic given.
Use ONLY the facts provided. Every number, place, species and date you write must appear in the facts. Do not state regulations,
limits, seasons or closures, and do not give advice the facts do not support. Do not describe where places are or how they relate to
each other (upstream, above, near) unless a fact says so. Stocking marked "scheduled" has not happened yet: write it in the future tense. Say what stands out, not everything. Plain, calm tone.
Return JSON: {"text": "..."}"""
