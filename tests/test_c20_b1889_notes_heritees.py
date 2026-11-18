"""Le rattachement hérité attend un projet connu sur le rendez-vous."""

import json
import sqlite3
from contextlib import closing

from app.models.meeting_note_migration import lier_notes_heritees


def test_note_rattachee_preservee_si_evenement_sans_projet():
    with closing(sqlite3.connect(':memory:')) as conn:
        conn.execute('CREATE TABLE activities (type TEXT, project_id TEXT, extra_data TEXT)')
        conn.execute('CREATE TABLE calendar_events (id TEXT, calendar_id TEXT, project_id TEXT)')
        donnees = json.dumps({'calendar_event_id': 'rdv', 'calendar_id': 'agenda'})
        conn.execute('INSERT INTO activities VALUES (?, ?, ?)', ('note', 'projet-existant', donnees))
        conn.execute('INSERT INTO calendar_events VALUES (?, ?, ?)', ('rdv', 'agenda', None))
        conn.commit()

        lier_notes_heritees(conn)

        projet, extra = conn.execute('SELECT project_id, extra_data FROM activities').fetchone()
        assert projet == 'projet-existant'
        assert 'meeting_note_v' not in json.loads(extra)
        conn.execute("UPDATE calendar_events SET project_id='projet-rdv'")
        lier_notes_heritees(conn)
        projet, extra = conn.execute('SELECT project_id, extra_data FROM activities').fetchone()
        assert projet == 'projet-rdv'
        assert json.loads(extra)['meeting_note_v'] == 1
