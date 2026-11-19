from .models import Activity, Message, Registration, Student

ACTIVITY_SELECT = """
SELECT
    a.*,
    COALESCE(SUM(CASE WHEN r.status = 'approved' THEN 1 ELSE 0 END), 0) AS approved_count,
    COALESCE(SUM(CASE WHEN r.status = 'pending' THEN 1 ELSE 0 END), 0) AS pending_count,
    COUNT(r.id) AS registration_count
FROM activities a
LEFT JOIN registrations r ON r.activity_id = a.id
"""

REGISTRATION_SELECT = """
SELECT
    r.*,
    a.title AS activity_title,
    a.start_at AS activity_start_at,
    a.location AS activity_location,
    a.policy_type AS activity_policy_type,
    s.name AS student_name
FROM registrations r
JOIN activities a ON a.id = r.activity_id
JOIN students s ON s.student_id = r.student_id
"""


def _escape_like(value):
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class StudentRepository:
    def __init__(self, database):
        self.db = database

    def get(self, student_id):
        row = self.db.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        return Student.from_row(row) if row else None

    def list_all(self):
        rows = self.db.execute("SELECT * FROM students ORDER BY student_id").fetchall()
        return [Student.from_row(row) for row in rows]


class ActivityRepository:
    def __init__(self, database):
        self.db = database

    def list(self, search=None):
        sql = ACTIVITY_SELECT
        parameters = []
        if search:
            sql += " WHERE a.title LIKE ? ESCAPE '\\'"
            parameters.append(f"%{_escape_like(search)}%")
        sql += " GROUP BY a.id ORDER BY a.start_at ASC, a.id DESC"
        rows = self.db.execute(sql, parameters).fetchall()
        return [Activity.from_row(row) for row in rows]

    def get(self, activity_id):
        row = self.db.execute(
            ACTIVITY_SELECT + " WHERE a.id = ? GROUP BY a.id", (activity_id,)
        ).fetchone()
        return Activity.from_row(row) if row else None

    def insert(self, data):
        cursor = self.db.execute(
            """
            INSERT INTO activities
                (title, category, start_at, location, capacity, policy_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["title"],
                data["category"],
                data["start_at"],
                data["location"],
                data["capacity"],
                data["policy_type"],
            ),
        )
        return cursor.lastrowid

    def update(self, activity_id, data):
        cursor = self.db.execute(
            """
            UPDATE activities
            SET title = ?, category = ?, start_at = ?, location = ?,
                capacity = ?, policy_type = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (
                data["title"],
                data["category"],
                data["start_at"],
                data["location"],
                data["capacity"],
                data["policy_type"],
                activity_id,
            ),
        )
        return cursor.rowcount > 0

    def delete(self, activity_id):
        cursor = self.db.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
        return cursor.rowcount > 0

    def approved_count(self, activity_id):
        row = self.db.execute(
            "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ? AND status = 'approved'",
            (activity_id,),
        ).fetchone()
        return row["n"]

    def registration_count(self, activity_id):
        row = self.db.execute(
            "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ?",
            (activity_id,),
        ).fetchone()
        return row["n"]


class RegistrationRepository:
    def __init__(self, database):
        self.db = database

    def get(self, registration_id):
        row = self.db.execute(
            REGISTRATION_SELECT + " WHERE r.id = ?", (registration_id,)
        ).fetchone()
        return Registration.from_row(row) if row else None

    def get_active(self, activity_id, student_id):
        row = self.db.execute(
            REGISTRATION_SELECT
            + """
            WHERE r.activity_id = ? AND r.student_id = ?
              AND r.status IN ('pending', 'approved')
            ORDER BY r.id DESC LIMIT 1
            """,
            (activity_id, student_id),
        ).fetchone()
        return Registration.from_row(row) if row else None

    def latest_for_student_activity(self, activity_id, student_id):
        row = self.db.execute(
            REGISTRATION_SELECT
            + """
            WHERE r.activity_id = ? AND r.student_id = ?
            ORDER BY r.id DESC LIMIT 1
            """,
            (activity_id, student_id),
        ).fetchone()
        return Registration.from_row(row) if row else None

    def list_for_activity(self, activity_id):
        rows = self.db.execute(
            REGISTRATION_SELECT
            + """
            WHERE r.activity_id = ?
            ORDER BY CASE r.status
                WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END, r.id ASC
            """,
            (activity_id,),
        ).fetchall()
        return [Registration.from_row(row) for row in rows]

    def list_for_student(self, student_id):
        rows = self.db.execute(
            REGISTRATION_SELECT
            + " WHERE r.student_id = ? ORDER BY r.created_at DESC, r.id DESC",
            (student_id,),
        ).fetchall()
        return [Registration.from_row(row) for row in rows]

    def list_pending(self):
        rows = self.db.execute(
            REGISTRATION_SELECT
            + " WHERE r.status = 'pending' ORDER BY r.created_at ASC, r.id ASC"
        ).fetchall()
        return [Registration.from_row(row) for row in rows]

    def count_status(self, activity_id, status):
        row = self.db.execute(
            "SELECT COUNT(*) AS n FROM registrations WHERE activity_id = ? AND status = ?",
            (activity_id, status),
        ).fetchone()
        return row["n"]

    def insert(self, activity_id, student_id, status):
        cursor = self.db.execute(
            """
            INSERT INTO registrations (activity_id, student_id, status)
            VALUES (?, ?, ?)
            """,
            (activity_id, student_id, status),
        )
        return cursor.lastrowid

    def update_status(self, registration_id, status):
        cursor = self.db.execute(
            """
            UPDATE registrations
            SET status = ?, updated_at = datetime('now', 'localtime')
            WHERE id = ?
            """,
            (status, registration_id),
        )
        return cursor.rowcount > 0


class MessageRepository:
    def __init__(self, database):
        self.db = database

    def add(self, student_id, activity_id, content):
        cursor = self.db.execute(
            """
            INSERT INTO messages (student_id, activity_id, content)
            VALUES (?, ?, ?)
            """,
            (student_id, activity_id, content),
        )
        return cursor.lastrowid

    def list_for_student(self, student_id):
        rows = self.db.execute(
            """
            SELECT m.*, a.title AS activity_title
            FROM messages m
            LEFT JOIN activities a ON a.id = m.activity_id
            WHERE m.student_id = ?
            ORDER BY m.created_at DESC, m.id DESC
            """,
            (student_id,),
        ).fetchall()
        return [Message.from_row(row) for row in rows]

    def unread_count(self, student_id):
        row = self.db.execute(
            "SELECT COUNT(*) AS n FROM messages WHERE student_id = ? AND is_read = 0",
            (student_id,),
        ).fetchone()
        return row["n"]

    def mark_all_read(self, student_id):
        self.db.execute(
            "UPDATE messages SET is_read = 1 WHERE student_id = ? AND is_read = 0",
            (student_id,),
        )


class NotificationFailureRepository:
    def __init__(self, database):
        self.db = database

    def record(self, event, error):
        self.db.execute(
            """
            INSERT INTO notification_failures
                (event_type, activity_id, registration_id, student_id, error)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event.event_type,
                event.activity_id,
                event.registration_id,
                event.student_id,
                str(error)[:1000],
            ),
        )