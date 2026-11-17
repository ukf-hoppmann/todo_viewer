import { renderHook } from "@testing-library/react";
import { act, type ReactNode } from "react";
import { MemoryRouter, useLocation } from "react-router";
import { describe, expect, it } from "vitest";
import { mapAddress, useMapNavigation } from "../../../../../../client/src/plugins/mindmap/navigation";

function setup(entry: string) {
	const wrapper = ({ children }: { children: ReactNode }) => <MemoryRouter initialEntries={[entry]}>{children}</MemoryRouter>;
	return renderHook(() => ({ navigation: useMapNavigation(), location: useLocation() }), { wrapper });
}

describe("mapAddress", () => {
	it("is the main route of the map, with the focus as query parameter", () => {
		expect(mapAddress()).toBe("/mindmap/main");
		expect(mapAddress(null)).toBe("/mindmap/main");
		expect(mapAddress("")).toBe("/mindmap/main");
		expect(mapAddress("n-1")).toBe("/mindmap/main?focus=n-1");
	});

	it("encodes the uid", () => {
		expect(mapAddress("a b&c")).toBe("/mindmap/main?focus=a%20b%26c");
	});
});

describe("useMapNavigation", () => {
	it("reads the focus from the address", () => {
		expect(setup("/mindmap/main?focus=n-1").result.current.navigation.focus).toBe("n-1");
	});

	it("has no focus without the parameter or with an empty one", () => {
		expect(setup("/mindmap/main").result.current.navigation.focus).toBeNull();
		expect(setup("/mindmap/main?focus=").result.current.navigation.focus).toBeNull();
	});

	it("opens a focus by navigating to the address of the map", () => {
		const { result } = setup("/trash/main");

		act(() => result.current.navigation.openFocus("n-2"));

		expect(result.current.location.pathname).toBe("/mindmap/main");
		expect(result.current.location.search).toBe("?focus=n-2");
		expect(result.current.navigation.focus).toBe("n-2");
	});

	it("opens the whole map without a focus", () => {
		const { result } = setup("/mindmap/main?focus=n-2");

		act(() => result.current.navigation.openFocus());

		expect(result.current.location.search).toBe("");
		expect(result.current.navigation.focus).toBeNull();
	});
});
