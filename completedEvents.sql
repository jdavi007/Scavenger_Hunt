-- Schema for Completed Student Events Table
-- Could probably get rid of this table and just use a bool on the events table
-- to mark complete but it's working as is so maybe better to leave it alone

DROP TABLE IF EXISTS completedEvents;

CREATE TABLE completedEvents (
    event_id INTEGER PRIMARY KEY, --event id
    user_id INTEGER NOT NULL, --user id
    title TEXT NOT NULL, --event title
    imageBlob TEXT NOT NULL --cover image viewable on index pages stored as binary data
);