-- Schema for Completed Student Events Table

DROP TABLE IF EXISTS completedEvents;

CREATE TABLE completedEvents (
    user_id INTEGER, -- student user id
    event_id INTEGER PRIMARY KEY, -- event id
    textUpload TEXT, -- text that student uploads
    imageBlob TEXT-- image that student uploads
);