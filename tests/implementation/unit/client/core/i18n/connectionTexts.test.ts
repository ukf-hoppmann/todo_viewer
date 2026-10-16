import { describe, expect, it } from "vitest";
import { initI18n } from "../../../../../../client/src/core/i18n/initI18n";
import { translateText } from "../../../../../../client/src/core/modals/text";

const keys = [
	["connection.title", {}],
	["connection.message", { attempts: 3 }],
	["connection.startMessage", { attempts: 3 }],
] as const;

describe("texts of the connection loss", () => {
	it.each(["de", "en"])("exist in %s, without a missing key or a left-over placeholder", async (lng) => {
		const i18n = await initI18n({ lng });

		for (const [key, params] of keys) {
			const text = translateText(i18n.t, { key, params });
			expect(text, key).not.toBe(key);
			expect(text, key).not.toContain("{{");
		}
	});

	it("names the number of failed tests", async () => {
		const i18n = await initI18n({ lng: "de" });

		expect(translateText(i18n.t, { key: "connection.message", params: { attempts: 3 } })).toContain("3");
	});
});
