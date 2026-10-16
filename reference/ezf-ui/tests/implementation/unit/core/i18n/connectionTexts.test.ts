import { describe, expect, it } from "vitest";
import { initI18n } from "../../../../../src/core/i18n/initI18n";
import { translateText } from "../../../../../src/core/modals/text";

const keys = [
	["connection.title", {}],
	["connection.messageMinutes", { attempts: 3, count: 5 }],
	["connection.messageSeconds", { attempts: 3, count: 20 }],
	["connection.startMessage", { attempts: 3 }],
	["connection.loggedOut", {}],
] as const;

describe("texts of the connection loss", () => {
	it.each(["de", "en", "fr"])("exist in %s, without a missing key or a left-over placeholder", async (lng) => {
		const i18n = await initI18n({ lng });

		for (const [key, params] of keys) {
			const text = translateText(i18n.t, { key, params });
			expect(text, key).not.toBe(key);
			expect(text, key).not.toContain("{{");
		}
	});

	it("names the number of failed tests and the time until the logout (de)", async () => {
		const i18n = await initI18n({ lng: "de" });

		const text = translateText(i18n.t, { key: "connection.messageMinutes", params: { attempts: 3, count: 5 } });

		expect(text).toContain("3");
		expect(text).toContain("5 Minuten");
	});

	it.each([
		["de", 1, "1 Sekunde", 20, "20 Sekunden"],
		["en", 1, "1 second", 20, "20 seconds"],
		["fr", 1, "1 seconde", 20, "20 secondes"],
	])("uses the singular and the plural of seconds in %s", async (lng, one, oneText, many, manyText) => {
		const i18n = await initI18n({ lng });

		expect(translateText(i18n.t, { key: "connection.messageSeconds", params: { attempts: 1, count: one } })).toContain(oneText);
		expect(translateText(i18n.t, { key: "connection.messageSeconds", params: { attempts: 1, count: many } })).toContain(manyText);
	});

	it("uses the plural of minutes in en and fr", async () => {
		const en = await initI18n({ lng: "en" });
		const fr = await initI18n({ lng: "fr" });

		expect(translateText(en.t, { key: "connection.messageMinutes", params: { attempts: 1, count: 5 } })).toContain("5 minutes");
		expect(translateText(fr.t, { key: "connection.messageMinutes", params: { attempts: 1, count: 5 } })).toContain("5 minutes");
	});

	it("says in all three languages that the user was logged out", async () => {
		expect(translateText((await initI18n({ lng: "de" })).t, { key: "connection.loggedOut" })).toContain("abgemeldet");
		expect(translateText((await initI18n({ lng: "en" })).t, { key: "connection.loggedOut" })).toContain("logged out");
		expect(translateText((await initI18n({ lng: "fr" })).t, { key: "connection.loggedOut" })).toContain("déconnecté");
	});
});
