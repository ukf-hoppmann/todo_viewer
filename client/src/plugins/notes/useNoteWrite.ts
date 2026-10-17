import {
	toWriteError,
	useArchiveTopicMutation,
	useCreateNoteMutation,
	useCreateTopicMutation,
	useDeleteTopicMutation,
	useMoveTopicMutation,
	useNoteActionMutation,
	useReactivateTopicMutation,
	useUpdateNoteMutation,
	useUpdateTopicMutation,
	type NoteOut,
	type TopicChoice,
} from "./api";

type Versioned = { uid: string; version: number };

/** The writes of the notes as promises that reject with a `WriteError` (the server's message and code). */
export function useNoteWrite() {
	const [createNote] = useCreateNoteMutation();
	const [updateNote] = useUpdateNoteMutation();
	const [noteAction] = useNoteActionMutation();
	const [createTopic] = useCreateTopicMutation();
	const [updateTopic] = useUpdateTopicMutation();
	const [moveTopic] = useMoveTopicMutation();
	const [archiveTopic] = useArchiveTopicMutation();
	const [reactivateTopic] = useReactivateTopicMutation();
	const [deleteTopic] = useDeleteTopicMutation();

	const run = async <T,>(action: () => Promise<T>): Promise<T> => {
		try {
			return await action();
		} catch (failure) {
			throw toWriteError(failure);
		}
	};

	return {
		createNote: (project: string, fields: Record<string, unknown>): Promise<NoteOut> => run(() => createNote({ project, fields }).unwrap()),
		updateNote: (note: Versioned, fields: Record<string, unknown>): Promise<NoteOut> => run(() => updateNote({ uid: note.uid, version: note.version, fields }).unwrap()),
		keep: (note: Versioned): Promise<NoteOut> => run(() => noteAction({ uid: note.uid, version: note.version, action: "keep" }).unwrap()),
		snooze: (note: Versioned, reviewAt?: string): Promise<NoteOut> => run(() => noteAction({ uid: note.uid, version: note.version, action: "snooze", review_at: reviewAt }).unwrap()),
		finish: (note: Versioned, status: "done" | "dropped"): Promise<NoteOut> => run(() => noteAction({ uid: note.uid, version: note.version, action: "finish", status }).unwrap()),
		restore: (note: Versioned): Promise<NoteOut> => run(() => noteAction({ uid: note.uid, version: note.version, action: "restore" }).unwrap()),
		createTopic: (project: string, name: string, parent: string | null, dueAt: string | null) => run(() => createTopic({ project, name, parent, due_at: dueAt }).unwrap()),
		updateTopic: (topic: Versioned, fields: Record<string, unknown>) => run(() => updateTopic({ uid: topic.uid, version: topic.version, fields }).unwrap()),
		moveTopic: (topic: Versioned, parent: string | null) => run(() => moveTopic({ uid: topic.uid, version: topic.version, parent }).unwrap()),
		archiveTopic: (topic: Versioned, choice?: TopicChoice) => run(() => archiveTopic({ uid: topic.uid, version: topic.version, ...choice }).unwrap()),
		reactivateTopic: (topic: Versioned) => run(() => reactivateTopic({ uid: topic.uid, version: topic.version }).unwrap()),
		deleteTopic: (topic: Versioned, choice?: TopicChoice) => run(() => deleteTopic({ uid: topic.uid, version: topic.version, ...choice }).unwrap()),
	};
}
