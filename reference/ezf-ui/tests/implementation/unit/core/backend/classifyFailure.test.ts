import { describe, expect, it } from "vitest";
import { failureKindOfStatus } from "../../../../../src/core/backend/classifyFailure";

describe("failureKindOfStatus", () => {
	it.each([401, 407])("takes %i as not logged in", (status) => {
		expect(failureKindOfStatus(status)).toBe("unauthorized");
	});

	it("takes no answer as unreachable", () => {
		expect(failureKindOfStatus("no-response")).toBe("unreachable");
	});

	it.each([500, 502, 503, 504, 599])("takes %i as unreachable", (status) => {
		expect(failureKindOfStatus(status)).toBe("unreachable");
	});

	it.each([200, 204, 301, 400, 403, 404, 406, 408, 409, 422, 499])("leaves %i to the caller", (status) => {
		expect(failureKindOfStatus(status)).toBeUndefined();
	});
});
