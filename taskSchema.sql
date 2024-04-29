-- Schema for event tasks

DROP TABLE IF EXISTS tasks;

CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Task id
    event_id INTEGER NOT NULL, -- Foreign key referencing events table
    description TEXT NOT NULL, -- Task description
    uploadType TEXT NOT NULL -- Student upload type
);
