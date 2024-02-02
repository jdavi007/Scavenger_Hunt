-- Schema for Scavenger Hunt Events Table
-- need to update to a list of events (# of events can vary for each to-do list)

DROP TABLE IF EXISTS events;

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, --event id
    title TEXT NOT NULL, --event title
    content TEXT NOT NULL, --event content
    imageBlob TEXT NOT NULL, --cover image viewable on index pages stored as binary data
    uploadType TEXT NOT NULL --student upload type
);