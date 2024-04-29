DROP TABLE IF EXISTS studentTasks;

CREATE TABLE studentTasks (
    task_id INTEGER NOT NULL, -- Task id
    event_id INTEGER NOT NULL, -- Foreign key referencing events table
    user_id INTEGER NOT NULL, -- Foreign key referencing user table
    hasResponse BOOLEAN NOT NULL, -- 0=no response, 1=has response
    response TEXT,
    UNIQUE(task_id, event_id, user_id)
);
