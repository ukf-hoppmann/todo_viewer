import { Autocomplete, TextField } from "@mui/material";
import { entityText, type Entity } from "./entityText";
import { sharedTestIds } from "./testIds";

interface EntityPickerBase {
	label: string;
	options: readonly Entity[];
	/** Elements that cannot be chosen (e.g. the element itself or its descendants). */
	disabledIds?: readonly string[];
	/** Text when nothing matches. */
	noOptionsText?: string;
}

type EntityPickerProps =
	| (EntityPickerBase & { multiple: true; value: readonly string[]; onChange: (ids: string[]) => void })
	| (EntityPickerBase & { multiple?: false; value: string | null; onChange: (id: string | null) => void });

/** Chooses one element or several (parent, dependencies, links); the search matches label and title. */
export function EntityPicker(props: EntityPickerProps) {
	const { label, options, disabledIds = [], noOptionsText } = props;
	const byId = new Map(options.map((option) => [option.id, option]));
	const shared = {
		options: [...options],
		getOptionLabel: entityText,
		getOptionDisabled: (option: Entity) => disabledIds.includes(option.id),
		isOptionEqualToValue: (option: Entity, selected: Entity) => option.id === selected.id,
		noOptionsText,
		size: "small" as const,
		"data-testid": sharedTestIds.entityPicker,
	};

	if (props.multiple) {
		const { value, onChange } = props;
		return (
			<Autocomplete<Entity, true>
				{...shared}
				multiple
				value={value.map((id) => byId.get(id)).filter((entity): entity is Entity => Boolean(entity))}
				onChange={(_event, selected) => onChange(selected.map((entity) => entity.id))}
				renderInput={(params) => <TextField {...params} label={label} />}
			/>
		);
	}
	const { value, onChange } = props;
	return (
		<Autocomplete<Entity, false>
			{...shared}
			value={value ? (byId.get(value) ?? null) : null}
			onChange={(_event, selected) => onChange(selected ? selected.id : null)}
			renderInput={(params) => <TextField {...params} label={label} />}
		/>
	);
}
