import { describe, expect, it } from "vitest";
import { mockLogBackend } from "../../../../../src/app/logging/mockLogBackend";

const valid = {
	id: "a3f9c2d1",
	time: "2026-09-30T14:32:05.123Z",
	level: "error",
	origin: "process-manager",
	sessionId: "5c1e0b7f9a2d4e6b8c0a1f3e5d7b9c2a",
	route: "/patients/123/process",
	element: "process-manager.save-button",
	action: "click",
	message: "POST childForm failed",
	userMessage: "process-manager:errors.save-unreachable",
	error: { name: "TypeError", message: "Failed to fetch", stack: "TypeError: …", cause: { name: "NonError", message: "x" } },
	data: { beliebig: ["JSON", 1, null] },
};

async function post(body: unknown) {
	const response = await mockLogBackend("persistLogFromUi", {
		method: "POST",
		body: typeof body === "string" ? body : JSON.stringify(body),
	});
	return { status: response.status, text: await response.text() };
}

describe("mockLogBackend", () => {
	it("accepts an entry in the format of the backend with 204", async () => {
		expect(await post(valid)).toEqual({ status: 204, text: "" });
	});

	it("accepts an entry with only the required fields", async () => {
		const { id, time, level, origin, sessionId, route } = valid;

		expect((await post({ id, time, level, origin, sessionId, route })).status).toBe(204);
	});

	it("accepts unknown additional fields, as the backend should", async () => {
		expect((await post({ ...valid, later: "field" })).status).toBe(204);
	});

	it("accepts cause null", async () => {
		expect((await post({ ...valid, error: { ...valid.error, cause: null } })).status).toBe(204);
	});

	it.each([
		["a missing session id", { ...valid, sessionId: undefined }, "sessionId"],
		["an error id of the wrong length", { ...valid, id: "abc" }, "/id"],
		["an unknown level", { ...valid, level: "fatal" }, "/level"],
		["a time that is no ISO time in UTC", { ...valid, time: "30.09.2026" }, "/time"],
		["an error without name", { ...valid, error: { message: "x" } }, "/error"],
		["a nested cause without message", { ...valid, error: { name: "E", message: "x", cause: { name: "C" } } }, "/error/cause"],
		["a message that is no text", { ...valid, message: 5 }, "/message"],
	])("rejects %s with 400 and names the problem", async (_name, body, expected) => {
		const { status, text } = await post(body);

		expect(status).toBe(400);
		expect(text).toContain(expected);
	});

	it("rejects a body that is no JSON", async () => {
		const { status, text } = await post("{not json");

		expect(status).toBe(400);
		expect(text).toContain("JSON");
	});
});
