import type { Progress } from "../domain/model";

/** Small pie that fills with the share of completed descendants, followed by "done/total". */
export function ProgressPie({ progress }: { progress: Progress }) {
  const percent = (progress.done / progress.total) * 100;
  return (
    <span className="node-progress" role="progressbar" aria-valuenow={progress.done} aria-valuemax={progress.total}>
      <span
        className="progress-pie"
        style={{ background: `conic-gradient(var(--status-done) ${percent}%, var(--panel-border) 0)` }}
      />
      {`${progress.done}/${progress.total}`}
    </span>
  );
}
