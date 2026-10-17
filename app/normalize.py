import re

_EXPAND = {
    "R": "RIVER", "RVR": "RIVER", "RES": "RESERVOIR", "LK": "LAKE", "PD": "POND",
    "CR": "CREEK", "FK": "FORK", "ST": "ST", "MT": "MOUNT", "PK": "PARK", "CST": "COAST",
    "N": "NORTH", "S": "SOUTH", "E": "EAST", "W": "WEST", "UPR": "UPPER", "FMR": "FORMER",
}


def normalize_alias(label: str) -> str:
    """Uppercase, strip punctuation and trailing reach suffixes (e.g. '-2'), expand shorthand."""
    s = label.upper().replace("&", " AND ")
    s = re.sub(r"[.,'’]", " ", s)
    s = re.sub(r"[-/()]", " ", s)
    tokens = [t for t in s.split() if t]
    # drop trailing reach number like "N FK-2" -> tokens [... "2"]
    if len(tokens) > 1 and tokens[-1].isdigit():
        tokens.pop()
    return " ".join(_EXPAND.get(t, t) for t in tokens)
