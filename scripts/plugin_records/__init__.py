"""Skillit record definitions.

Each module defines a typed FsRecord subclass representing a domain entity.
Records are persisted to disk as JSON and managed via ResourceRecordList
collections.

Collection management
---------------------
Records are grouped into **collections** using ``ResourceRecordList``, which
provides CRUD operations and three storage backends:

* ``LIST_ITEM``  — all records in one JSONL file (compact, append-friendly).
* ``FILE``       — one ``<type>-@<uid>.json`` per record in a directory.
* ``FOLDER``     — one ``<type>-@<uid>/record.json`` directory per record
                   (best when records need sibling files like outputs or logs).

Default storage path
--------------------
When ``list_path`` is not provided, ``ResourceRecordList`` stores records
under ``~/.flow/records/<record_type>/``.  The record type is inferred from
the ``record_class``.  You can override this base path by passing
``records_path`` to the constructor.

Example::

    from plugin_records.skillit_records import skillit_records

    session = skillit_records.sessions.create(SkillitSession(session_id="abc-123"))
"""

from .skillit_config import SkillitConfig
from .skillit_session import SkillitSession
from .skillit_records import skillit_records
