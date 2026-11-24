"""Der gemeinsame Satz für die KI: wie ein neues Item einem Knoten zugeordnet wird (`TASK-077`).

Er steht an dieser einen Stelle und hängt an den Beschreibungen der Tools `mindmap_get_tree`,
`mindmap_create_node`, `mindmap_assign_item` und `mindmap_create_item_at_node`.
"""

ASSIGNMENT_RULE = (
    "Regel beim Anlegen eines Items: Lies zuerst den Themenbaum (mindmap_get_tree). Passt ein Knoten, lege das Item "
    "dort an (mindmap_create_item_at_node) oder ordne ein vorhandenes zu (mindmap_assign_item). Passt keiner, schlage "
    "dem Owner im Gespräch einen Knoten oder Unterknoten vor (Titel, Ort im Baum) und lege ihn "
    "(mindmap_create_node) erst nach seiner Zustimmung an; erfinde keine Themen. Ohne Zustimmung lege das Item "
    "ohne Knoten an (backlog_create_item); es steht dann unter „Nicht zugeordnet“"
)
