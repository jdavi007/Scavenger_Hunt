# Database initialization
# Run this only once to initialize database
# Running again resets all info in databse

import sqlite3
connection = sqlite3.connect('database.db')




# Initializing table for scavenger hunt events
with open('eventSchema.sql') as f:
    connection.executescript(f.read())
cur = connection.cursor()
f.close()




# Initializing table for event tasks
with open('taskSchema.sql') as f:
    connection.executescript(f.read())
cur = connection.cursor()
f.close()




# Initializing table for student tasks
with open('studentTasks.sql') as f:
    connection.executescript(f.read())
cur = connection.cursor()
f.close()




# Initializaing User Table (generic info for testing)
with open('userSchema.sql') as f:
    connection.executescript(f.read())
cur = connection.cursor()

cur.execute("INSERT INTO users (email, password, firstName, lastName, isAdmin) VALUES (?, ?, ?, ?, ?)",
            ('student@uvawise.edu', 'password', 'Stu', 'Dent', 0)
            )

cur.execute("INSERT INTO users (email, password, firstName, lastName, isAdmin) VALUES (?, ?, ?, ?, ?)",
            ('student1@uvawise.edu', 'password', 'Stud', 'Ent', 0)
            )

cur.execute("INSERT INTO users (email, password, firstName, lastName, isAdmin) VALUES (?, ?, ?, ?, ?)",
            ('staff@uvawise.edu', 'password', 'Charles', 'Xavier', 1)
            )

f.close()




# Initializing Completed Events Table
with open('completedEvents.sql') as f:
    connection.executescript(f.read())
cur = connection.cursor()
f.close()




connection.commit()
connection.close()