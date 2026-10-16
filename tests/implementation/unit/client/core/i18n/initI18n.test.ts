import { describe, expect, it } from "vitest";
import { initI18n } from "../../../../../../client/src/core";

describe("initI18n", () => {
	it("returns texts of the requested language", async () => {
		const i18n = await initI18n({ lng: "en" });

		expect(i18n.t("core:layout.main")).toBe("Main content");
	});

	it("falls back to German for an unsupported language", async () => {
		const i18n = await initI18n({ lng: "xx" });

		expect(i18n.t("core:layout.main")).toBe("Hauptbereich");
	});

	it("creates a separate instance on every call", async () => {
		const english = await initI18n({ lng: "en" });
		const german = await initI18n({ lng: "de" });

		expect(english.t("core:layout.main")).toBe("Main content");
		expect(german.t("core:layout.main")).toBe("Hauptbereich");
	});
});
