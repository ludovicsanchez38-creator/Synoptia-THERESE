"""Rattacher les anciennes notes à leur vrai dossier, une seule fois."""
from typing import Any

LIER_NOTES = """UPDATE activities SET
 project_id = (SELECT e.project_id FROM calendar_events e
   WHERE e.id = json_extract(activities.extra_data, '$.calendar_event_id')
     AND e.calendar_id = json_extract(activities.extra_data, '$.calendar_id')),
 extra_data = json_set(extra_data, '$.meeting_note_v', 1)
 WHERE type = 'note' AND json_valid(extra_data)
 AND coalesce(json_extract(CASE WHEN json_valid(extra_data) THEN extra_data ELSE '{}' END, '$.meeting_note_v'), 0) != 1
 AND EXISTS (SELECT 1 FROM calendar_events e
   WHERE e.id = json_extract(CASE WHEN json_valid(activities.extra_data) THEN activities.extra_data ELSE '{}' END, '$.calendar_event_id')
     AND e.calendar_id = json_extract(CASE WHEN json_valid(activities.extra_data) THEN activities.extra_data ELSE '{}' END, '$.calendar_id'))"""


def lier_notes_heritees(conn: Any) -> None:
    if not {'project_id', 'extra_data', 'type'} <= {r[1] for r in conn.execute('PRAGMA table_info(activities)')}:
        return
    if not {'id', 'calendar_id', 'project_id'} <= {r[1] for r in conn.execute('PRAGMA table_info(calendar_events)')}:
        return
    conn.execute(LIER_NOTES)
    conn.commit()
