import {
	toWriteError,
	useArchiveTopicMutation,
	useCreateMemoMutation,
	useCreateTopicMutation,
	useDeleteTopicMutation,
	useMoveTopicMutation,
	useMemoActionMutation,
	useReactivateTopicMutation,
	useUpdateMemoMutation,
	useUpdateTopicMutation,
	type MemoOut,
	type TopicChoice,
} from "./api";

type Versioned = { uid: string; version: number };

/** The writes of the memos as promises that reject with a `WriteError` (the server's message and code). */
export function useMemoWrite() {
	const [createMemo] = useCreateMemoMutation();
	const [updateMemo] = useUpdateMemoMutation();
	const [memoAction] = useMemoActionMutation();
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
		createMemo: (project: string, fields: Record<string, unknown>): Promise<MemoOut> => run(() => createMemo({ project, fields }).unwrap()),
		updateMemo: (memo: Versioned, fields: Record<string, unknown>): Promise<MemoOut> => run(() => updateMemo({ uid: memo.uid, version: memo.version, fields }).unwrap()),
		keep: (memo: Versioned): Promise<MemoOut> => run(() => memoAction({ uid: memo.uid, version: memo.version, action: "keep" }).unwrap()),
		snooze: (memo: Versioned, reviewAt?: string): Promise<MemoOut> => run(() => memoAction({ uid: memo.uid, version: memo.version, action: "snooze", review_at: reviewAt }).unwrap()),
		finish: (memo: Versioned, status: "done" | "dropped"): Promise<MemoOut> => run(() => memoAction({ uid: memo.uid, version: memo.version, action: "finish", status }).unwrap()),
		restore: (memo: Versioned): Promise<MemoOut> => run(() => memoAction({ uid: memo.uid, version: memo.version, action: "restore" }).unwrap()),
		createTopic: (project: string, name: string, parent: string | null, dueAt: string | null) => run(() => createTopic({ project, name, parent, due_at: dueAt }).unwrap()),
		updateTopic: (topic: Versioned, fields: Record<string, unknown>) => run(() => updateTopic({ uid: topic.uid, version: topic.version, fields }).unwrap()),
		moveTopic: (topic: Versioned, parent: string | null) => run(() => moveTopic({ uid: topic.uid, version: topic.version, parent }).unwrap()),
		archiveTopic: (topic: Versioned, choice?: TopicChoice) => run(() => archiveTopic({ uid: topic.uid, version: topic.version, ...choice }).unwrap()),
		reactivateTopic: (topic: Versioned) => run(() => reactivateTopic({ uid: topic.uid, version: topic.version }).unwrap()),
		deleteTopic: (topic: Versioned, choice?: TopicChoice) => run(() => deleteTopic({ uid: topic.uid, version: topic.version, ...choice }).unwrap()),
	};
}
