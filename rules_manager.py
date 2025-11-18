# rules_manager.py
import json
import re
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional

class Rule:
    def __init__(self, name: str, pattern: str, replacement: str,
                 match_type: str = "exact", notes: str = "", id: Optional[str]=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.pattern = pattern
        self.replacement = replacement
        self.match_type = match_type
        self.notes = notes

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "pattern": self.pattern,
            "replacement": self.replacement,
            "match_type": self.match_type,
            "notes": self.notes
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'Rule':
        return Rule(
            name=d["name"],
            pattern=d["pattern"],
            replacement=d["replacement"],
            match_type=d.get("match_type", "exact"),
            notes=d.get("notes", ""),
            id=d.get("id")
        )

class RulesManager:
    def __init__(self, path: str = "rules.json"):
        self.path = Path(path)
        self.rules: List[Rule] = []
        self.load()

    def load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.rules = [Rule.from_dict(r) for r in data]
            except Exception:
                self.rules = []
        else:
            self.rules = []

    def save(self):
        data = [r.to_dict() for r in self.rules]
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_rules(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.rules]

    def add_rule(self, name: str, pattern: str, replacement: str, match_type: str = "exact", notes: str = "") -> Dict[str, Any]:
        r = Rule(name=name, pattern=pattern, replacement=replacement, match_type=match_type, notes=notes)
        self.rules.append(r)
        self.save()
        return r.to_dict()

    def remove_rule(self, rule_id: str) -> bool:
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.id != rule_id]
        if len(self.rules) != before:
            self.save()
            return True
        return False

    def update_rule(self, rule_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        for r in self.rules:
            if r.id == rule_id:
                for k, v in kwargs.items():
                    if hasattr(r, k) and v is not None:
                        setattr(r, k, v)
                self.save()
                return r.to_dict()
        return None

    def apply_rules_to_text(self, text: str) -> str:
        out = text
        for r in self.rules:
            if r.match_type == "exact":
                out = out.replace(r.pattern, r.replacement)
            elif r.match_type == "case_insensitive":
                pattern = re.escape(r.pattern)
                out = re.sub(pattern, r.replacement, out, flags=re.IGNORECASE)
            elif r.match_type == "regex":
                out = re.sub(r.pattern, r.replacement, out)
            else:
                continue
        return out
