import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { renderWithProviders } from "../test/render";
import { Modal } from "./Modal";

function Stacked({ closeUnder, closeOver }: { closeUnder: () => void; closeOver: () => void }) {
  const [overOpen, setOverOpen] = useState(true);
  const [, setRenders] = useState(0);
  return (
    <>
      <button onClick={() => setRenders((n) => n + 1)}>render again</button>
      <Modal labelledBy="under" onDismiss={() => closeUnder()}>
        <h3 id="under">Under</h3>
      </Modal>
      {overOpen && (
        <Modal
          labelledBy="over"
          onDismiss={() => {
            closeOver();
            setOverOpen(false);
          }}
        >
          <h3 id="over">Over</h3>
        </Modal>
      )}
    </>
  );
}

describe("Modal: dialogs on top of each other", () => {
  it("lets Escape close only the topmost dialog", async () => {
    const closeUnder = vi.fn();
    const closeOver = vi.fn();
    renderWithProviders(<Stacked closeUnder={closeUnder} closeOver={closeOver} />);

    await userEvent.keyboard("{Escape}");

    expect(closeOver).toHaveBeenCalledTimes(1);
    expect(closeUnder).not.toHaveBeenCalled();
    expect(screen.queryByText("Over")).not.toBeInTheDocument();
  });

  it("keeps the order when the parent renders again with new callbacks", async () => {
    const closeUnder = vi.fn();
    const closeOver = vi.fn();
    renderWithProviders(<Stacked closeUnder={closeUnder} closeOver={closeOver} />);

    await userEvent.click(screen.getByRole("button", { name: "render again" }));
    await userEvent.keyboard("{Escape}");

    expect(closeOver).toHaveBeenCalledTimes(1);
    expect(closeUnder).not.toHaveBeenCalled();
  });

  it("gives Escape back to the dialog below once the top one is gone", async () => {
    const closeUnder = vi.fn();
    renderWithProviders(<Stacked closeUnder={closeUnder} closeOver={vi.fn()} />);

    await userEvent.keyboard("{Escape}");
    await userEvent.keyboard("{Escape}");

    expect(closeUnder).toHaveBeenCalledTimes(1);
  });
});
