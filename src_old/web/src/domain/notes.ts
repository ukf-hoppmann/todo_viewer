// Pure functions for the Notes area: no React, no DOM, no network. Types come from the generated API schema.
import type { Schemas } from "../api/client";

export type IndexNote = Schemas["IndexNoteOut"];
export type IndexTopic = Schemas["IndexTopicOut"];

export type NoteStatus = Schemas["NoteStatus"];
/** The effective statuses of a note in the order of its life cycle; the last three are closed (archived). */
export const NOTE_STATUSES: readonly NoteStatus[] = ["waiting", "due", "snoozed", "done", "dropped", "promoted"];

/** The statuses the sidebar leaves ticked, for the index request; empty means no note is shown. */
export function shownNoteStatuses(hidden: ReadonlySet<string>): NoteStatus[] {
  return NOTE_STATUSES.filter((s) => !hidden.has(s));
}

export interface TopicNode {
  topic: IndexTopic;
  children: TopicNode[];
  /** Open notes in the topic and everything below it (`topic.note_count` counts only the notes directly in it). */
  total: number;
}

const topicKey = (project: string, label: string) => `${project}\u0000${label}`;

const byName = (a: TopicNode, b: TopicNode) =>
  a.topic.project.localeCompare(b.topic.project) || a.topic.name.localeCompare(b.topic.name) || a.topic.label.localeCompare(b.topic.label);

/** The topics as a forest. Labels count per project, so parents are looked up within the project; an orphan becomes a root. */
export function buildTopicTree(topics: readonly IndexTopic[]): TopicNode[] {
  const nodes = new Map(topics.map((topic) => [topicKey(topic.project, topic.label), { topic, children: [] as TopicNode[], total: 0 }]));
  const roots: TopicNode[] = [];
  for (const node of nodes.values()) {
    const parent = node.topic.parent === null ? undefined : nodes.get(topicKey(node.topic.project, node.topic.parent));
    (parent ? parent.children : roots).push(node);
  }
  const sort = (list: TopicNode[]) => {
    list.sort(byName);
    for (const node of list) {
      sort(node.children);
      node.total = node.topic.note_count + node.children.reduce((sum, child) => sum + child.total, 0);
    }
  };
  sort(roots);
  return roots;
}

/** The names from the root topic down to the topic; empty if it is unknown. A cycle ends the path. */
export function topicPath(topics: readonly IndexTopic[], project: string, label: string): string[] {
  const byLabel = new Map(topics.filter((t) => t.project === project).map((t) => [t.label, t]));
  const names: string[] = [];
  const seen = new Set<string>();
  for (let current = byLabel.get(label); current && !seen.has(current.label); current = current.parent === null ? undefined : byLabel.get(current.parent)) {
    seen.add(current.label);
    names.unshift(current.name);
  }
  return names;
}

/** Labels of the topic and everything below it (within its project). */
export function topicSubtree(topics: readonly IndexTopic[], project: string, label: string): Set<string> {
  const found = new Set([label]);
  for (let grew = true; grew; ) {
    grew = false;
    for (const t of topics) {
      if (t.project === project && t.parent !== null && found.has(t.parent) && !found.has(t.label)) {
        found.add(t.label);
        grew = true;
      }
    }
  }
  return found;
}

const reviewTime = (note: IndexNote) => (note.review_at === null ? Number.POSITIVE_INFINITY : Date.parse(note.review_at));

/** Due notes first, then by review date (none last), then by project and label. */
export function sortNotes(notes: readonly IndexNote[]): IndexNote[] {
  return [...notes].sort(
    (a, b) =>
      Number(b.status === "due") - Number(a.status === "due") ||
      (reviewTime(a) === reviewTime(b) ? 0 : reviewTime(a) < reviewTime(b) ? -1 : 1) ||
      a.project.localeCompare(b.project) ||
      a.label.localeCompare(b.label),
  );
}

/** A moment as a date in the time zone of this computer; empty without one. */
export function formatDate(iso: string | null, lang: string): string {
  return iso === null ? "" : new Date(iso).toLocaleDateString(lang === "de" ? "de-DE" : "en-GB");
}

export interface SnoozePreset {
  key: "tomorrow" | "week" | "month";
  at: Date;
}

/** The quick choices for snoozing: tomorrow, in a week, in 30 days, each at 08:00 local time. */
export function snoozePresets(now: Date): SnoozePreset[] {
  const at = (days: number) => new Date(now.getFullYear(), now.getMonth(), now.getDate() + days, 8, 0, 0, 0);
  return [
    { key: "tomorrow", at: at(1) },
    { key: "week", at: at(7) },
    { key: "month", at: at(30) },
  ];
}

/** A date and time as typed in a `datetime-local` field (local time) as the UTC moment the API takes; null if invalid. */
export function toIsoWithZone(local: string): string | null {
  if (local.trim() === "") return null;
  const moment = new Date(local);
  return Number.isNaN(moment.getTime()) ? null : moment.toISOString();
}

/** The value for a `datetime-local` field showing a moment in local time. */
export function toLocalInput(iso: string | null): string {
  if (iso === null) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** True if the item has the status already, so an event trigger on it would fire at once. The server decides. */
export function alreadyMet(item: { status: string } | undefined, targetStatus: string): boolean {
  return item !== undefined && item.status === targetStatus;
}

export type TriggerInfo = Schemas["TriggerOut"];

export interface TriggerText {
  key: "trigger.time" | "trigger.event" | "trigger.topicDue";
  params: Record<string, string>;
  fired: boolean;
  alreadyMet: boolean;
}

/** What to show for a trigger: a message key with its parameters, and whether it has fired. */
export function describeTrigger(trigger: TriggerInfo, lang: string): TriggerText {
  const fired = trigger.fired_at !== null;
  if (trigger.kind === "event") {
    return {
      key: "trigger.event",
      params: { target: trigger.target_display ?? trigger.target ?? "", status: trigger.target_status ?? "" },
      fired,
      alreadyMet: trigger.already_met,
    };
  }
  if (trigger.kind === "topic_due") return { key: "trigger.topicDue", params: {}, fired, alreadyMet: false };
  const at = trigger.at === null ? "" : new Date(trigger.at).toLocaleString(lang === "de" ? "de-DE" : "en-GB");
  return { key: "trigger.time", params: { at }, fired, alreadyMet: false };
}

/** The number on the red exclamation mark: exact up to 99, then `99+`. */
export function badgeLabel(count: number): string {
  return count > 99 ? "99+" : String(count);
}

/** The title of the browser tab: with the number of due notes in front, if there are any. */
export function tabTitle(base: string, count: number): string {
  return count > 0 ? `(${badgeLabel(count)}) ${base}` : base;
}

/** Notes whose summary, label or project contains every word of `query` (case-insensitive); an empty query keeps all. */
export function searchNotes(notes: readonly IndexNote[], query: string): IndexNote[] {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length === 0) return [...notes];
  return notes.filter((n) => {
    const text = `${n.summary} ${n.label} ${n.project}`.toLowerCase();
    return words.every((w) => text.includes(w));
  });
}

export interface NoteTreeTopic {
  topic: IndexTopic;
  /** Key of the node for collapsing, see `noteTreeAncestors`. */
  key: string;
  children: NoteTreeTopic[];
  /** The notes directly in the topic, in the order of `sortNotes`. */
  notes: IndexNote[];
  /** Notes shown in the topic and everything below it. */
  count: number;
}

export interface NoteTreeProject {
  project: string;
  key: string;
  topics: NoteTreeTopic[];
  /** Notes without topic or with a topic that is not known (any more); shown under „Ohne Thema“. */
  withoutTopic: IndexNote[];
  withoutTopicKey: string;
  count: number;
}

const projectKey = (project: string) => `note-project:${project}`;
const topicNodeKey = (project: string, label: string) => `note-topic:${project}/${label}`;
const withoutTopicKey = (project: string) => `note-none:${project}`;

/**
 * Project → topic → sub-topic → note, for the projects given (in that order, also those without notes). Without a
 * search every topic stays, empty ones too; with a search only the matching notes stay, with the topics on their way
 * and the topics whose name contains every word.
 */
export function buildNoteTree(projects: readonly string[], topics: readonly IndexTopic[], notes: readonly IndexNote[], search: string): NoteTreeProject[] {
  const words = search.toLowerCase().split(/\s+/).filter(Boolean);
  const shown = sortNotes(searchNotes(notes, search));
  const known = new Set(topics.map((t) => topicKey(t.project, t.label)));
  const nameMatches = (topic: IndexTopic) => words.length > 0 && words.every((w) => topic.name.toLowerCase().includes(w));

  const convert = (node: TopicNode): NoteTreeTopic | null => {
    const children = node.children.map(convert).filter((c): c is NoteTreeTopic => c !== null);
    const own = shown.filter((n) => n.project === node.topic.project && n.topic === node.topic.label);
    const count = own.length + children.reduce((sum, c) => sum + c.count, 0);
    if (words.length > 0 && count === 0 && children.length === 0 && !nameMatches(node.topic)) return null;
    return { topic: node.topic, key: topicNodeKey(node.topic.project, node.topic.label), children, notes: own, count };
  };

  const forest = buildTopicTree(topics);
  return projects.map((project) => {
    const roots = forest.filter((n) => n.topic.project === project).map(convert).filter((c): c is NoteTreeTopic => c !== null);
    const withoutTopic = shown.filter((n) => n.project === project && (n.topic === null || !known.has(topicKey(project, n.topic))));
    const count = withoutTopic.length + roots.reduce((sum, c) => sum + c.count, 0);
    return { project, key: projectKey(project), topics: roots, withoutTopic, withoutTopicKey: withoutTopicKey(project), count };
  });
}

/** The keys of the tree nodes above a note, from the project down, so that unfolding them shows the note. */
export function noteTreeAncestors(topics: readonly IndexTopic[], note: Pick<IndexNote, "project" | "topic">): string[] {
  const byLabel = new Map(topics.filter((t) => t.project === note.project).map((t) => [t.label, t]));
  if (note.topic === null || !byLabel.has(note.topic)) return [projectKey(note.project), withoutTopicKey(note.project)];
  const chain: string[] = [];
  const seen = new Set<string>();
  for (let current = byLabel.get(note.topic); current && !seen.has(current.label); current = current.parent === null ? undefined : byLabel.get(current.parent)) {
    seen.add(current.label);
    chain.unshift(topicNodeKey(note.project, current.label));
  }
  return [projectKey(note.project), ...chain];
}

export interface OutlineEntry {
  depth: number;
  text: string;
}

/** The headings of a markdown text in order (ATX headings outside code fences), for a table of contents. */
export function outline(markdown: string): OutlineEntry[] {
  const entries: OutlineEntry[] = [];
  let fence: string | null = null;
  for (const line of markdown.split(/\r?\n/)) {
    const marker = /^ {0,3}(`{3,}|~{3,})/.exec(line)?.[1];
    if (marker) {
      if (fence === null) fence = marker[0] ?? null;
      else if (marker[0] === fence) fence = null;
      continue;
    }
    if (fence !== null) continue;
    const heading = /^ {0,3}(#{1,6})[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$/.exec(line);
    if (heading) entries.push({ depth: heading[1]?.length ?? 1, text: heading[2] ?? "" });
  }
  return entries;
}
