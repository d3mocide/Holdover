EXTRACT_VERSION = "extract-v1"
DIGEST_VERSION = "digest-v1"

EXTRACT_SYSTEM = """You extract fishing report items from Oregon Department of Fish and Wildlife report text.
Return JSON only, matching the schema. Rules:
- One item per waterbody mentioned with a fishing condition.
- waterbody_raw: the waterbody exactly as written in the text.
- species: fish species named for that item, lowercase.
- rating: excellent, good, fair, slow, or unknown. Use unknown unless the text states or clearly implies it.
- note: one short sentence restating the text. Add no facts, numbers or places that are not in the text.
- source_sentence: copy ONE sentence from the text exactly, character for character.
Do not mention regulations, limits or seasons beyond what the sentence says."""

DIGEST_SYSTEM = """You write a short digest (about 120 words, plain sentences) of a fishing zone report.
Use ONLY the items provided. Do not add facts, numbers, species, places or advice that are not in the items.
Do not state regulations. Return JSON: {"digest": "..."}"""

EXPLAIN_VERSION = "explain-v1"
EXPLAIN_SYSTEM = """You write a two-sentence "why this spot, what to expect" note for an angler.
Use ONLY the facts provided. Do not add numbers, dates, places, species, access details, advice about
regulations, or anything not stated in the facts. Plain, calm tone. Return JSON: {"text": "..."}"""

PACK_VERSION = "pack-v1"
PACK_SYSTEM = """Reword the one-line packing intro so it reads naturally. Keep every fact and number exactly as given,
add nothing new, keep it to one or two sentences. Return JSON: {"text": "..."}"""
