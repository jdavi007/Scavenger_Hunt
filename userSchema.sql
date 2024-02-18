-- Schema for Users Table

DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT, --internal user id (not UVA Wise ID)
    email NVARCHAR(40) UNIQUE NOT NULL, --UVA Wise email address
    password NVARCHAR(64) NOT NULL, --user password
    firstName NVARCHAR(40) NULL, --first & last name are never referenced but kept just in case
    lastName NVARCHAR(40) NULL,
    isAdmin BOOLEAN NOT NULL -- 0=student, 1=staff
);

