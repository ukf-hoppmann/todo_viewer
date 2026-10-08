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
