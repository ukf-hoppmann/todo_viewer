// Pure functions for the Notes area: no React, no DOM, no network. Types come from the generated API schema.
import type { Schemas } from "../api/client";

export type IndexNote = Schemas["IndexNoteOut"];
export type IndexTopic = Schemas["IndexTopicOut"];

export interface TopicNode {
  topic: IndexTopic;
  children: TopicNode[];
}

const topicKey = (project: string, label: string) => `${project}\u0000${label}`;

const byName = (a: TopicNode, b: TopicNode) =>
  a.topic.project.localeCompare(b.topic.project) || a.topic.name.localeCompare(b.topic.name) || a.topic.label.localeCompare(b.topic.label);

/** The topics as a forest. Labels count per project, so parents are looked up within the project; an orphan becomes a root. */
export function buildTopicTree(topics: readonly IndexTopic[]): TopicNode[] {
  const nodes = new Map(topics.map((topic) => [topicKey(topic.project, topic.label), { topic, children: [] as TopicNode[] }]));
  const roots: TopicNode[] = [];
  for (const node of nodes.values()) {
    const parent = node.topic.parent === null ? undefined : nodes.get(topicKey(node.topic.project, node.topic.parent));
    (parent ? parent.children : roots).push(node);
  }
  const sort = (list: TopicNode[]) => {
    list.sort(byName);
    for (const node of list) sort(node.children);
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

/**
 * The notes of one topic (with `includeSubtopics` of everything below it). Without a topic: all notes, or those of
 * `project` if one is given.
 */
export function notesOfTopic(
  notes: readonly IndexNote[],
  topics: readonly IndexTopic[],
  project: string | null,
  topicLabel: string | null,
  includeSubtopics: boolean,
): IndexNote[] {
  const inProject = project === null ? notes : notes.filter((n) => n.project === project);
  if (project === null || topicLabel === null) return [...inProject];
  const labels = includeSubtopics ? topicSubtree(topics, project, topicLabel) : new Set([topicLabel]);
  return inProject.filter((n) => n.topic !== null && labels.has(n.topic));
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
