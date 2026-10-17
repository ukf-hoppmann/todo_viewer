import { describe, expect, it } from "vitest";
import { extractHeadings, renderMarkdown, slugify } from "../../../../../../client/src/shared/markdown/renderMarkdown";

describe("slugify", () => {
	it.each([
		["Hello World", "hello-world"],
		["Übersicht & Ziele", "ubersicht-ziele"],
		["  --  ", "section"],
		["Task 12.3", "task-12-3"],
	])("%s → %s", (text, slug) => {
		expect(slugify(text)).toBe(slug);
	});
});

describe("extractHeadings", () => {
	it("lists the headings with depth and unique slugs", () => {
		const headings = extractHeadings("# Eins\n\ntext\n\n## Zwei\n\n## Zwei\n\n### Drei `x`\n");

		expect(headings).toEqual([
			{ depth: 1, text: "Eins", slug: "eins" },
			{ depth: 2, text: "Zwei", slug: "zwei" },
			{ depth: 2, text: "Zwei", slug: "zwei-2" },
			{ depth: 3, text: "Drei `x`", slug: "drei-x" },
		]);
	});

	it("returns nothing for a text without headings", () => {
		expect(extractHeadings("nur Text")).toEqual([]);
	});
});

describe("renderMarkdown", () => {
	it("renders markdown to HTML", () => {
		const html = renderMarkdown("**fett** und `code`\n\n- a\n- b");

		expect(html).toContain("<strong>fett</strong>");
		expect(html).toContain("<code>code</code>");
		expect(html).toContain("<li>a</li>");
	});

	it("gives headings the ids of extractHeadings", () => {
		const html = renderMarkdown("# Eins\n\n## Zwei\n\n## Zwei");

		expect(html).toContain('<h1 id="eins">Eins</h1>');
		expect(html).toContain('<h2 id="zwei">Zwei</h2>');
		expect(html).toContain('<h2 id="zwei-2">Zwei</h2>');
	});

	it("removes scripts, event handlers and javascript links", () => {
		const html = renderMarkdown('<script>alert(1)</script>\n\n<img src=x onerror="alert(2)">\n\n[x](javascript:alert(3))');

		expect(html).not.toContain("<script");
		expect(html).not.toContain("onerror");
		expect(html).not.toContain("javascript:");
	});

	it("renders inline markup in headings", () => {
		expect(renderMarkdown("# Mit *Betonung*")).toContain('<h1 id="mit-betonung">Mit <em>Betonung</em></h1>');
	});
});
