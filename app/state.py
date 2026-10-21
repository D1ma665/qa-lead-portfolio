import json, copy, os
from config import SCORES, GOALS, BASES, HISTORY

_STATE_FILE = os.path.join(os.path.dirname(__file__), "state.json")

def _defaults():
    return {
        "scores": copy.deepcopy(SCORES),
        "goals": copy.deepcopy(GOALS),
        "bases": copy.deepcopy(BASES),
        "history": copy.deepcopy(HISTORY),
    }

def load():
    if os.path.exists(_STATE_FILE):
        try:
            with open(_STATE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            base = _defaults()
            base.update({k: data[k] for k in base if k in data})
            return base
        except Exception:
            return _defaults()
    return _defaults()

def save(state):
    with open(_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

STATE = load()

