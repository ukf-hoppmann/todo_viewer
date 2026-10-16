import { createModals } from "./createModals";

/**
 * The central dialog object of the application; callable from anywhere, also
 * outside React components. `ModalHost` shows its dialogs.
 */
export const modals = createModals();
