/** The query parameter with which a link chooses the language; the language detection of i18next reads it before the stored choice. */
const languageParameter = "lng";

/**
 * The address without the language parameter, so that a choice made in the interface is not overruled by the
 * link on the next load. Takes and returns path, query and fragment; an address without the parameter comes
 * back unchanged.
 */
export function withoutLanguageParameter(url: string): string {
	const parsed = new URL(url, "http://localhost");
	if (!parsed.searchParams.has(languageParameter)) return url;

	parsed.searchParams.delete(languageParameter);
	return parsed.pathname + parsed.search + parsed.hash;
}
