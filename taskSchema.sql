-- Schema for event tasks

DROP TABLE IF EXISTS tasks;

CREATE TABLE tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT, -- task id
    event_id INTEGER NOT NULL, -- foreign key referencing events table
    description TEXT NOT NULL, -- task description
    uploadType TEXT NOT NULL -- student upload type
);