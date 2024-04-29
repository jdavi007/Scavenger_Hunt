-- Schema for Users Table

DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT, -- User ID
    email NVARCHAR(40) UNIQUE NOT NULL, -- UVA Wise email address
    password NVARCHAR(64) NOT NULL, -- User password
    firstName NVARCHAR(40) NULL, -- First & last name are never referenced but kept just in case
    lastName NVARCHAR(40) NULL,
    isAdmin BOOLEAN NOT NULL, -- 0=student, 1=staff
    verificationToken NVARCAR(32) NULL, -- For email verification
    verified BOOLEAN NOT NULL DEFAULT 0 -- 0=not verified, 1=verified
);
