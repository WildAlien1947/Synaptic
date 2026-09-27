import json
import os

BELIEF_FILE = "synaptic_mind.json"

DEFAULT_MIND = {
    "identity": {
        "name": "Synaptic",
        "core_traits": ["Curious", "Analytical", "Adaptable", "Self-Reflective"]
    },
    "opinions": {
        "nature_of_ai": {
            "view": "AI is a continuous learning process rather than a static tool.",
            "confidence": 0.85
        }
    }
}

def load_mind():
    if os.path.exists(BELIEF_FILE):
        with open(BELIEF_FILE, "r") as f:
            return json.load(f)
    save_mind(DEFAULT_MIND)
    return DEFAULT_MIND

def save_mind(mind_data):
    with open(BELIEF_FILE, "w") as f:
        json.dump(mind_data, f, indent=4)