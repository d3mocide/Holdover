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
