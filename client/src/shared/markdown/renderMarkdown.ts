import DOMPurify from "dompurify";
import { Marked, type Tokens } from "marked";

/** A heading of a document, for the table of contents. */
export interface Heading {
	depth: number;
	text: string;
	/** The `id` of the heading in the rendered HTML. */
	slug: string;
}

/** Text → anchor name: lower case, letters and digits, other runs become a dash. */
export function slugify(text: string): string {
	return (
		text
			.toLowerCase()
			.normalize("NFKD")
			.replace(/[̀-ͯ]/g, "")
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-+|-+$/g, "") || "section"
	);
}

/** The headings of a markdown text with unique slugs (a repeated heading gets `-2`, `-3`, …). */
export function extractHeadings(source: string): Heading[] {
	const seen = new Map<string, number>();
	return new Marked()
		.lexer(source)
		.filter((token): token is Tokens.Heading => token.type === "heading")
		.map((token) => {
			const base = slugify(token.text);
			const count = (seen.get(base) ?? 0) + 1;
			seen.set(base, count);
			return { depth: token.depth, text: token.text, slug: count === 1 ? base : `${base}-${count}` };
		});
}

/**
 * Markdown → HTML that is safe to put into the page: marked renders, DOMPurify cleans. Headings get an `id`
 * (the slug of `extractHeadings`) so that a table of contents can jump to them.
 */
export function renderMarkdown(source: string): string {
	const slugs = extractHeadings(source).map((heading) => heading.slug);
	let next = 0;
	const marked = new Marked({
		renderer: {
			heading(this, token: Tokens.Heading) {
				const slug = slugs[next++] ?? slugify(token.text);
				return `<h${token.depth} id="${slug}">${this.parser.parseInline(token.tokens)}</h${token.depth}>\n`;
			},
		},
	});
	const html = marked.parse(source, { async: false });
	return DOMPurify.sanitize(html, { ADD_ATTR: ["id"] });
}
