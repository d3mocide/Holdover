"""Stand-in for an OpenAI-compatible LLM host, for development and demos without a model.

    uvicorn scripts.fake_llm:app --port 11435
    LLM_BASE_URL=http://localhost:11435/v1 LLM_MODEL=fake python -m app.cli llm

It "extracts" by sentence splitting and keyword rules, so it only exercises the plumbing. It is not
a quality reference. Set FAKE_LLM_MODE=hallucinate to make it invent a sentence (tests the guard).
"""
import json
import os
import re

from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/v1/models")
def models():
    return {"data": [{"id": "fake"}]}


def _extract(text: str) -> dict:
    items = []
    for sent in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")):
        m = re.search(r"\b(?:at|on|in|along|of)\s+((?:the\s+)?(?:[A-Z][\w']+\s?){1,4}(?:River|Lake|Reservoir|Creek|Pond|Bay)s?)", sent)
        if not m:
            m = re.search(r"of the ((?:North|South|East|West|Upper|Lower)\s[A-Z]\w+)", sent)  # e.g. "North Santiam"
        if not m:
            continue
        low = sent.lower()
        rating = "excellent" if "excellent" in low else "good" if "good" in low else "fair" if "fair" in low else \
            "slow" if "slow" in low else "unknown"
        species = [s for s in ["coho", "chinook", "steelhead", "trout", "walleye", "bass", "salmon", "shad", "panfish"] if s in low]
        items.append({"waterbody_raw": m.group(1), "species": species, "rating": rating,
                      "note": sent.strip()[:160], "source_sentence": sent.strip()})
    if os.environ.get("FAKE_LLM_MODE") == "hallucinate":
        items.append({"waterbody_raw": "Imaginary Lake", "species": ["trout"], "rating": "excellent",
                      "note": "Great.", "source_sentence": "Imaginary Lake is full of trout."})
    return {"items": items}


@app.post("/v1/chat/completions")
async def chat(req: Request):
    body = await req.json()
    system, user = body["messages"][0]["content"], body["messages"][1]["content"]
    if "short digest" in system:
        names = re.findall(r"^- (.+?) \(", user, re.M)
        out = {"digest": "Reports mention " + ", ".join(names[:5]) + "." if names else "No items."}
    else:
        out = _extract(user.split("Text:\n", 1)[-1])
    return {"choices": [{"message": {"role": "assistant", "content": json.dumps(out)}}]}
