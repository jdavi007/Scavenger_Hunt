-- Schema for Scavenger Hunt Events Table

DROP TABLE IF EXISTS events;

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Event id
    title TEXT NOT NULL, -- Event title
    imageBlob TEXT NOT NULL -- Cover image viewable on index pages stored as binary data
);
