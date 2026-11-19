CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 40)
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL CHECK (length(trim(title)) BETWEEN 1 AND 100),
    category TEXT NOT NULL CHECK (length(trim(category)) BETWEEN 1 AND 40),
    start_at TEXT NOT NULL CHECK (length(trim(start_at)) >= 16),
    location TEXT NOT NULL CHECK (length(trim(location)) BETWEEN 1 AND 100),
    capacity INTEGER NOT NULL CHECK (capacity > 0 AND capacity <= 10000),
    policy_type TEXT NOT NULL CHECK (policy_type IN ('direct', 'review')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES activities(id) ON DELETE RESTRICT,
    student_id TEXT NOT NULL REFERENCES students(student_id),
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_registration_active
    ON registrations (activity_id, student_id)
    WHERE status IN ('pending', 'approved');

CREATE INDEX IF NOT EXISTS idx_registrations_activity
    ON registrations (activity_id, status);
CREATE INDEX IF NOT EXISTS idx_registrations_student
    ON registrations (student_id, created_at);
CREATE INDEX IF NOT EXISTS idx_activities_start
    ON activities (start_at);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(student_id),
    activity_id INTEGER REFERENCES activities(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    is_read INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_messages_student
    ON messages (student_id, created_at);

CREATE TABLE IF NOT EXISTS notification_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    activity_id INTEGER,
    registration_id INTEGER,
    student_id TEXT,
    error TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

INSERT OR IGNORE INTO students (student_id, name) VALUES
    ('S001', '张同学'),
    ('S002', '李同学'),
    ('S003', '王同学');