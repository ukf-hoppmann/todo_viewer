import { describe, expect, it } from "vitest";
import { coreTestIds, initI18n } from "../../../../../src/core";
import de from "../../../../../src/core/i18n/locales/de.json";
import en from "../../../../../src/core/i18n/locales/en.json";
import fr from "../../../../../src/core/i18n/locales/fr.json";
import { translateText } from "../../../../../src/core/modals/text";

function keysOf(value: unknown, prefix = ""): string[] {
	if (typeof value !== "object" || value === null) return [prefix];
	return Object.entries(value).flatMap(([key, item]) => keysOf(item, prefix ? `${prefix}.${key}` : key));
}

describe("translateText", () => {
	it("returns a finished text unchanged", async () => {
		const i18n = await initI18n({ lng: "en" });

		expect(translateText(i18n.t, "Saved {{x}}")).toBe("Saved {{x}}");
	});

	it("translates a key of the namespace core", async () => {
		const i18n = await initI18n({ lng: "en" });

		expect(translateText(i18n.t, { key: "modals.close" })).toBe("Close");
	});

	it("follows the language of the instance", async () => {
		const i18n = await initI18n({ lng: "fr" });

		expect(translateText(i18n.t, { key: "modals.close" })).toBe("Fermer");
	});

	it("translates a key with an explicit namespace", async () => {
		const i18n = await initI18n({ lng: "en" });
		i18n.addResourceBundle("en", "variant-filter", { errors: { x: "Filter failed" } });

		expect(translateText(i18n.t, { key: "variant-filter:errors.x" })).toBe("Filter failed");
	});

	it("inserts params", async () => {
		const i18n = await initI18n({ lng: "en" });
		i18n.addResourceBundle("en", "core", { test: { hello: "Hello {{name}}" } }, true);

		expect(translateText(i18n.t, { key: "test.hello", params: { name: "Ada" } })).toBe("Hello Ada");
	});
});

describe("texts of the modals", () => {
	it("exist in German, English and French with the same keys", () => {
		const german = keysOf(de.modals).sort();

		expect(german.length).toBeGreaterThan(0);
		expect(keysOf(en.modals).sort()).toEqual(german);
		expect(keysOf(fr.modals).sort()).toEqual(german);
	});

	it("are translated, not copied from German", () => {
		expect(en.modals.close).not.toBe(de.modals.close);
		expect(fr.modals.close).not.toBe(de.modals.close);
	});
});

describe("test ids of the modals", () => {
	it("follow the form core.<element>", () => {
		const ids = [
			coreTestIds.modal,
			coreTestIds.modalTitle,
			coreTestIds.modalMessage,
			coreTestIds.modalBody,
			coreTestIds.modalDetailsToggle,
			coreTestIds.modalDetails,
			coreTestIds.modalDetailsCopy,
			coreTestIds.modalClose,
			coreTestIds.modalConfirm,
			coreTestIds.modalCancel,
		];

		expect(new Set(ids).size).toBe(10);
		for (const id of ids) expect(id).toMatch(/^core\.[a-z-]+$/);
	});
});
