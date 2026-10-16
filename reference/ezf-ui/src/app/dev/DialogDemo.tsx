import { Box, Button, Stack, TextField, Typography } from "@mui/material";
import { useState, type ReactNode } from "react";
import { useModals, useReportError, type ModalSeverity } from "../../core";
import { demoTestIds } from "./demoTestIds";

// Developer tool: the texts are German on purpose and not part of the i18n resources.

const alertMessages: Record<ModalSeverity, string> = {
	error: "Die Daten konnten nicht gespeichert werden.",
	warning: "Das Formular enthält noch ungespeicherte Änderungen.",
	info: "Die Daten wurden zuletzt heute um 08:15 Uhr aktualisiert.",
	success: "Der Prozess wurde gespeichert.",
};

const alertButtons = [
	["error", "Fehler", demoTestIds.alertError],
	["warning", "Warnung", demoTestIds.alertWarning],
	["info", "Information", demoTestIds.alertInfo],
	["success", "Erfolg", demoTestIds.alertSuccess],
] as const;

interface DemoData {
	name: string;
	count: number;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
	return (
		<Box component="section" sx={{ mb: 3 }}>
			<Typography variant="h6" component="h2" sx={{ mb: 1 }}>
				{title}
			</Typography>
			<Stack direction="row" useFlexGap spacing={1} sx={{ flexWrap: "wrap" }}>
				{children}
			</Stack>
		</Box>
	);
}

/**
 * Development page (`/dev/core/dialogs`): triggers every kind of dialog and
 * `reportError` by button, to look at the layout and to try the interface.
 */
export function DialogDemo() {
	const modals = useModals();
	const reportError = useReportError();
	const [result, setResult] = useState("–");

	const showAlert = async (severity: ModalSeverity) => {
		await modals.alert({ severity, message: alertMessages[severity] });
		setResult(`Hinweis (${severity}) geschlossen`);
	};

	const showAlertWithDetails = async () => {
		await modals.alert({
			severity: "error",
			title: "Fehler beim Speichern",
			message: "Der Prozess konnte nicht gespeichert werden.\n\nBitte prüfen Sie die Eingaben und versuchen Sie es erneut.",
			details: [
				{ label: "Zeitpunkt", value: "2026-09-30 15:26:36" },
				{ label: "Fehler-ID", value: "76f9cb12" },
				{ label: "Sitzungs-ID", value: "724a6562cad57a4f7f9ae00484c9ce2e" },
				{ label: "Backend", value: "Process name must be unique within the system" },
			],
		});
		setResult("Hinweis mit Details geschlossen");
	};

	const askConfirmation = async () => {
		const confirmed = await modals.confirm({
			title: "Formular wechseln?",
			message: "Sie haben ungespeicherte Änderungen. Beim Wechsel gehen sie verloren.",
			confirmText: "Fortfahren",
			cancelText: "Bleiben",
		});
		setResult(`Bestätigung: ${confirmed ? "bestätigt" : "abgebrochen"}`);
	};

	const askWithBody = async () => {
		const { confirmed, data } = await modals.confirmWithBody<DemoData>({
			title: "Prozess umbenennen",
			message: "Der Name muss im gesamten System eindeutig sein.",
			maxWidth: "md",
			initialData: { name: "", count: 0 },
			body: ({ data, updateData }) => (
				<Stack spacing={2}>
					<TextField
						label="Name"
						value={data.name}
						onChange={(event) => updateData({ name: event.target.value })}
						slotProps={{ htmlInput: { "data-testid": demoTestIds.bodyName } }}
						fullWidth
					/>
					<Box>
						<Button
							variant="outlined"
							onClick={() => updateData({ count: data.count + 1 })}
							data-testid={demoTestIds.bodyCounter}
						>
							Zähler erhöhen ({data.count})
						</Button>
					</Box>
				</Stack>
			),
		});
		setResult(`Dialog mit Inhalt: ${confirmed ? "bestätigt" : "abgebrochen"}, Daten: ${JSON.stringify(data)}`);
	};

	const showQueue = async () => {
		const first = modals.alert({ severity: "info", title: "Erster Hinweis", message: "Alle drei Dialoge wurden gleichzeitig angefordert." });
		const second = modals.confirm({ title: "Rückfrage dazwischen", message: "Sie erscheint erst nach dem ersten Hinweis." });
		const third = modals.alert({ severity: "success", title: "Letzter Hinweis" });
		await first;
		const confirmed = await second;
		await third;
		setResult(`Warteschlange abgearbeitet, Rückfrage: ${confirmed ? "bestätigt" : "abgebrochen"}`);
	};

	const reportFailure = async () => {
		await reportError({
			element: "app.dialog-demo-report-error",
			action: "click",
			userMessage: "Der Server ist nicht erreichbar. Bitte versuchen Sie es später erneut.",
			message: "POST childForm failed",
			error: new TypeError("Failed to fetch"),
			data: { form: 1 },
		});
		setResult("Fehler-Hinweis geschlossen");
	};

	const reportWarning = async () => {
		await reportError({
			element: "app.dialog-demo-report-warning",
			action: "click",
			severity: "warning",
			userMessage: "Ein Teil der Daten konnte nicht geladen werden.",
			error: "Timeout nach 10 s",
		});
		setResult("Warnung geschlossen");
	};

	return (
		<Box data-testid={demoTestIds.page} sx={{ p: 3, maxWidth: 900 }}>
			<Typography variant="h5" component="h1" sx={{ mb: 0.5 }}>
				Dialoge – Demo
			</Typography>
			<Typography color="text.secondary" sx={{ mb: 3 }}>
				Nur im Entwicklungsmodus. Jeder Button löst einen Dialog aus; das Ergebnis steht unten.
			</Typography>

			<Section title="Hinweise">
				{alertButtons.map(([severity, label, testId]) => (
					<Button key={severity} variant="outlined" onClick={() => void showAlert(severity)} data-testid={testId}>
						{label}
					</Button>
				))}
				<Button variant="outlined" onClick={() => void showAlertWithDetails()} data-testid={demoTestIds.alertDetails}>
					Mit technischen Details
				</Button>
			</Section>

			<Section title="Rückfragen">
				<Button variant="outlined" onClick={() => void askConfirmation()} data-testid={demoTestIds.confirm}>
					Bestätigung
				</Button>
				<Button variant="outlined" onClick={() => void askWithBody()} data-testid={demoTestIds.confirmBody}>
					Bestätigung mit Inhalt
				</Button>
				<Button variant="outlined" onClick={() => void showQueue()} data-testid={demoTestIds.queue}>
					Warteschlange (drei Dialoge)
				</Button>
			</Section>

			<Section title="reportError (Log-Eintrag und Hinweis)">
				<Button variant="outlined" color="error" onClick={() => void reportFailure()} data-testid={demoTestIds.reportError}>
					Fehler melden
				</Button>
				<Button variant="outlined" color="warning" onClick={() => void reportWarning()} data-testid={demoTestIds.reportWarning}>
					Warnung melden
				</Button>
			</Section>

			<Typography variant="subtitle2">Ergebnis</Typography>
			<Typography data-testid={demoTestIds.result} sx={{ fontFamily: "monospace", wordBreak: "break-word" }}>
				{result}
			</Typography>
		</Box>
	);
}
