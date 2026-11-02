"""Index of the notes kept as files in a backlog folder (todo module, backend files).

The format is the ToDo-Viewer's file format version 2 (notes/NOTE-001.md, notes/new-<name>.md, notes/topics.md); the
viewer owns labels, uids and triggers. --index and --due read only the head lines of each note, never the long text, and
do not validate the format; --check does (notes_format.py). The counterpart for backlog items is backlog.py.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from notes_format import check_notes_folder

NOTES_DIR = "notes"
TOPICS_FILE = "topics.md"
USAGE = "usage: notes_files.py <backlog folder> [--index | --due [--today YYYY-MM-DD] | --check]"

# NOTE-001.md and new-<name>.md; the documents (NOTE-001_notes.md, ...), topics.md and counters.md do not match.
_NOTE_FILE = re.compile(r"^(NOTE-[0-9]+|new-[A-Za-z0-9-]+)\.md$")
_FIELD = re.compile(r"^(?P<name>[A-Z][A-Za-z]*):[ \t]*(?P<value>.*?)[ \t]*$")
_TOPIC_LINE = re.compile(r"^[ \t]*- (?P<label>\S+) \| (?P<rest>.*)$")
_DAY = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}")
_OPEN_STATUSES = {"waiting", "due", "snoozed"}
_NEW_TOPIC = "new:"


@dataclass(frozen=True)
class Topic:
    label: str
    name: str
    due: str = ""


@dataclass
class Note:
    file: str
    fields: dict[str, str] = field(default_factory=dict)

    def value(self, name: str) -> str:
        return self.fields.get(name, "")


@dataclass
class NotesReport:
    notes: list[Note] = field(default_factory=list)
    topics: list[Topic] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    def topic_of(self, note: Note) -> Topic | None:
        """The note's topic: by label, or by name for a topic without a label (new:<name>)."""
        reference = note.value("Topic")
        if not reference:
            return None
        if reference.startswith(_NEW_TOPIC):
            name = reference[len(_NEW_TOPIC):]
            return next((t for t in self.topics if t.label == "NEW" and t.name == name), Topic("NEW", name))
        return next((t for t in self.topics if t.label == reference), Topic(reference, reference))


def read_notes(backlog: Path) -> NotesReport:
    """Reads the head of every active note below <backlog>/notes; notes in the trash or archive are left out."""
    report = NotesReport()
    folder = backlog / NOTES_DIR
    if not folder.is_dir():
        return report
    report.topics = _read_topics(folder / TOPICS_FILE, report)
    for path in sorted(p for p in folder.iterdir() if _NOTE_FILE.match(p.name)):
        note = _read_note(path, report)
        if note is None or note.value("Deleted") or note.value("Archived").lower() == "true":
            continue
        if not note.value("Summary"):
            report.problems.append(f"{path.name}: no Summary line")
            continue
        report.notes.append(note)
    return report


def _read_note(path: Path, report: NotesReport) -> Note | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        report.problems.append(f"{path.name}: cannot be read ({error.__class__.__name__})")
        return None
    note = Note(path.name)
    for line in text.splitlines()[1:]:
        if not line.strip():
            break
        match = _FIELD.match(line)
        if match:
            note.fields[match["name"]] = match["value"]
    return note


def _read_topics(path: Path, report: NotesReport) -> list[Topic]:
    if not path.is_file():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        report.problems.append(f"{path.name}: cannot be read ({error.__class__.__name__})")
        return []
    topics = []
    for line in text.splitlines():
        match = _TOPIC_LINE.match(line)
        if not match:
            continue
        # The name keeps its escapes (\| and \\), so a row stays one row.
        name, *attributes = match["rest"].split(" | ")
        due = next((a[len("due="):] for a in attributes if a.startswith("due=")), "")
        topics.append(Topic(match["label"], name, due))
    return topics


def format_index(report: NotesReport) -> str:
    rows = [
        " | ".join(
            [n.file, n.value("Status") or "-", n.value("Review") or "-", _topic_name(report, n), n.value("Summary")]
        )
        for n in report.notes
    ]
    return "\n".join(["File | Status | Review | Topic | Summary", *rows]) if rows else ""


def due_reasons(report: NotesReport, note: Note, today: date) -> list[str]:
    """Why an open note is due: its review day or its topic's day has come. Events need the viewer."""
    if note.value("Status") not in _OPEN_STATUSES:
        return []
    reasons = []
    review = _day(note.value("Review"))
    if review and review <= today.isoformat():
        reasons.append(f"review {review}")
    topic = report.topic_of(note)
    topic_due = _day(topic.due) if topic else ""
    if topic_due and topic_due <= today.isoformat():
        reasons.append(f"topic due {topic_due}")
    return reasons


def format_due(report: NotesReport, today: date) -> str:
    rows = []
    for note in report.notes:
        reasons = due_reasons(report, note, today)
        if reasons:
            rows.append(
                " | ".join(
                    [
                        note.file,
                        note.value("Status"),
                        ", ".join(reasons),
                        note.value("Review") or "-",
                        _topic_name(report, note),
                        note.value("Summary"),
                    ]
                )
            )
    return "\n".join(["File | Status | Reason | Review | Topic | Summary", *rows]) if rows else ""


def _topic_name(report: NotesReport, note: Note) -> str:
    topic = report.topic_of(note)
    return topic.name if topic else "-"


def _day(timestamp: str) -> str:
    match = _DAY.match(timestamp)
    return match.group(0) if match else ""


def main(argv: list[str]) -> int:
    args = argv[1:]
    today = date.today()
    due = "--due" in args
    today_given = "--today" in args
    if today_given:
        at = args.index("--today")
        try:
            if not due or at + 1 >= len(args) or not _DAY.fullmatch(args[at + 1]):
                raise ValueError
            today = date.fromisoformat(args[at + 1])
        except ValueError:
            print(USAGE, file=sys.stderr)
            return 2
        args = args[:at] + args[at + 2:]
    index = "--index" in args
    check = "--check" in args
    args = [a for a in args if a not in ("--index", "--due", "--check")]
    if len(args) != 1 or args[0].startswith("-") or [index, due, check].count(True) > 1 or (check and today_given):
        print(USAGE, file=sys.stderr)
        return 2
    if check:
        findings = check_notes_folder(Path(args[0]) / NOTES_DIR)
        for finding in findings:
            print(finding)
        return 1 if any(f.error for f in findings) else 0
    report = read_notes(Path(args[0]))
    output = format_due(report, today) if due else format_index(report)
    if output:
        print(output)
    for problem in report.problems:
        print(problem, file=sys.stderr)
    return 1 if report.problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
