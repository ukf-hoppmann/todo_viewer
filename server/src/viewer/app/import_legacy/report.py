"""Der Bericht der Übernahme: Zahlen je Typ und jede Abweichung."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class Report:
    counts: Counter[str] = field(default_factory=Counter)
    deviations: list[str] = field(default_factory=list)

    def count(self, what: str, number: int = 1) -> None:
        self.counts[what] += number

    def deviation(self, text: str) -> None:
        self.deviations.append(text)

    def render(self, *, dry_run: bool) -> str:
        lines = ["Übernahme aus dem alten Viewer" + (" (Probelauf, nichts geschrieben)" if dry_run else ""), ""]
        width = max((len(name) for name in self.counts), default=0)
        lines += [f"  {name.ljust(width)}  {number}" for name, number in sorted(self.counts.items())]
        lines += ["", f"Abweichungen: {len(self.deviations)}"]
        lines += [f"  - {text}" for text in self.deviations]
        return "\n".join(lines) + "\n"
