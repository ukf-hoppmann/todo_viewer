import { render } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { initI18n, ModalHost } from "../../../client/src/core";
import { createModals } from "../../../client/src/core/modals/createModals";

/** Renders a `ModalHost` with its own dialog queue and the core texts. */
export async function renderHost(lng = "en") {
	const modals = createModals();
	const i18n = await initI18n({ lng });
	render(
		<I18nextProvider i18n={i18n}>
			<ModalHost modals={modals} />
		</I18nextProvider>,
	);
	return { modals, i18n };
}
