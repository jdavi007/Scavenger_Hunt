-- Schema for Scavenger Hunt Events Table

DROP TABLE IF EXISTS events;

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, --event id
    title TEXT NOT NULL, --event title
    imageBlob TEXT NOT NULL --cover image viewable on index pages stored as binary data
);