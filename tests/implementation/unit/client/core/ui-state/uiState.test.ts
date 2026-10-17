import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { selectUiDocument, setUiStateValue, flushUiState, uiStateWriteDelayMs } from "../../../../../../client/src/core/ui-state/uiState";
import { fakeUiStateBackend } from "../../../../../helpers/client/fakeUiStateBackend";

beforeEach(() => {
	vi.useFakeTimers();
});
afterEach(() => {
	vi.useRealTimers();
});

describe("setUiStateValue", () => {
	it("loads the document first and keeps what the server holds", async () => {
		const backend = fakeUiStateBackend({ backlog: { filter: "open" } });

		await setUiStateValue(backend.store, "backlog", "expanded", ["EPIC-007"]);

		expect(selectUiDocument(backend.store.getState(), "backlog")).toEqual({ filter: "open", expanded: ["EPIC-007"] });
		expect(backend.requests.map((request) => request.method)).toEqual(["GET"]);
	});

	it("changes the cache at once and sends the whole document after the delay", async () => {
		const backend = fakeUiStateBackend({ backlog: { filter: "open" } });

		await setUiStateValue(backend.store, "backlog", "expanded", [1]);
		expect(backend.puts()).toHaveLength(0);
		await vi.advanceTimersByTimeAsync(uiStateWriteDelayMs);

		expect(backend.puts()).toEqual([{ method: "PUT", owner: "backlog", body: { document: { filter: "open", expanded: [1] } } }]);
		expect(backend.documents.get("backlog")).toEqual({ filter: "open", expanded: [1] });
	});

	it("sends one request for a burst of changes, with the last values", async () => {
		const backend = fakeUiStateBackend();

		await setUiStateValue(backend.store, "backlog", "a", 1);
		await setUiStateValue(backend.store, "backlog", "b", 2);
		await setUiStateValue(backend.store, "backlog", "a", 3);
		await vi.advanceTimersByTimeAsync(uiStateWriteDelayMs);

		expect(backend.puts()).toHaveLength(1);
		expect(backend.documents.get("backlog")).toEqual({ a: 3, b: 2 });
	});

	it("keeps the documents of different owners apart", async () => {
		const backend = fakeUiStateBackend();

		await setUiStateValue(backend.store, "backlog", "a", 1);
		await setUiStateValue(backend.store, "notes", "a", 2);
		await vi.advanceTimersByTimeAsync(uiStateWriteDelayMs);

		expect(backend.documents.get("backlog")).toEqual({ a: 1 });
		expect(backend.documents.get("notes")).toEqual({ a: 2 });
	});

	it("writes nothing when the document could not be loaded, so that it never replaces the server's", async () => {
		const backend = fakeUiStateBackend({ backlog: { precious: true } }, { failGet: true });

		await setUiStateValue(backend.store, "backlog", "a", 1);
		await vi.advanceTimersByTimeAsync(uiStateWriteDelayMs * 2);

		expect(backend.puts()).toHaveLength(0);
		expect(backend.documents.get("backlog")).toEqual({ precious: true });
	});
});

describe("flushUiState", () => {
	it("sends what is waiting at once and not a second time", async () => {
		const backend = fakeUiStateBackend();
		await setUiStateValue(backend.store, "backlog", "a", 1);

		await flushUiState(backend.store);
		await vi.advanceTimersByTimeAsync(uiStateWriteDelayMs * 2);

		expect(backend.puts()).toHaveLength(1);
		expect(backend.documents.get("backlog")).toEqual({ a: 1 });
	});

	it("does nothing without waiting writes", async () => {
		const backend = fakeUiStateBackend();

		await flushUiState(backend.store);

		expect(backend.requests).toEqual([]);
	});
});
