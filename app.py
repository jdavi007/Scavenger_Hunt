# Scavenger Hunt Web Application for UVA Wise
# For CSC 4990 - Computer Science Seminar with Dr. Frazier

# ------------------------------Setup------------------------------------ #

import sqlite3 # For database
from flask import Flask, render_template, url_for, request, flash, redirect, Response, send_file # For construction of web apps
from werkzeug.exceptions import abort # For exception handling
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user # For login management
import base64 # For displaying images stored as binary in database
import bcrypt # For password hashing
import requests # For accessing outside weblinks (QR Code)
import json # For JSON management
app = Flask(__name__)
app.config['SECRET_KEY'] = 'SeCrEtKeY' # Probably needs to be changed but not entirely sure what this is for

userRole = "" # Global variable for user type, i.e. staff or student




# ------------------------------Functions------------------------------ #

# Connects to database - working
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn
#end get_db_connection()




# Event loader - working
# Precondition: Request for an event
# Postcondition: Event info is returned
def get_event(id):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # Set row factory to sqlite3.Row
    
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM events WHERE id = ?', (id,))
    event = dict(cursor.fetchone())  # Convert row to dictionary
    
    if event:
        # Get event tasks
        cursor.execute('SELECT * FROM tasks WHERE event_id = ?', (id,))
        tasks = cursor.fetchall()
        event['tasks'] = tasks

    conn.close()
    return event
#end get_event()




# ---------------Login Management--------------- #

login_manager = LoginManager(app)
login_manager.login_view = "login"




# User Class - working
class User(UserMixin):
    def __init__(self, id, email, password, firstName, lastName, isAdmin):
        self.id = id # Internal ID from auto incremented int in database
        self.email = email # UVA Wise email address
        self.password = password
        self.firstName = firstName
        self.lastName = lastName
        self.isAdmin = isAdmin # Distinction between staff and student
        self.authenticated = False
    
    def is_active(self):
        return self.is_active()
    
    def is_anonymous(self):
        return False
    
    def is_authenticated(self):
        return self.authenticated
    
    def is_active(self):
        return True
    
    def get_email(self):
        return self.email
    
    def get_admin_stat(self):
        return self.isAdmin
    
    def get_user_name(self):
        return self.firstName
    
    def get_id(self):
        return self.id
#end User Class




# Logout Function - working
# Precondition: User is logged in
# Postcondition: User logged out, redirect to login page
@app.route('/logout')
@login_required
def logout():
    global userRole
    userRole = ''
    logout_user()
    return redirect(url_for('login'))
# end logout()
    



# User Loader Function - working
# Connects to user table in database and fetches user based on user_id
# Precondition: No user is loaded
# Postcondition: If user exists, user information is returned
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor=conn.cursor()

    cursor.execute('SELECT * FROM users where user_id=?', (user_id,))
    lu = cursor.fetchone()

    if lu is None:
        return None
    else:
        return User(int(lu[0]), lu[1], lu[2], lu[3], lu[4], lu[5])
# end load_user()




# ---------------Image Processing--------------- #

# Function to encode student image blob data to base64
def base64_encode(data):
    return base64.b64encode(data).decode('utf-8')
app.jinja_env.filters['b64encode'] = base64_encode


# ---------------QR Code Generation--------------- #
def generate_qr_code(data):
    endpoint = "https://chart.googleapis.com/chart"
    params = {
            "cht": "qr",
            "chs": "300x300",
            "chl": data
    }

    response = requests.get(endpoint, params=params)

    # 200 represents success
    if response.status_code == 200:
        return response.url
    else:
        # Failed to generate a QR code URL
        return None

def generate_event_json(data):
    # Holds event objects
    event_json = []
    for event, value in data.items():
        # Event name, completed value (True/False)
        event_obj = {
                "event": event,
                "value": value
        }
        event_json.append(event_obj)
    return json.dumps(event_json)


# ------------------------------Pages------------------------------ #

# Login / Landing Page - working, might need security updates
# Precondition: Navigation to website url, no user logged in
# Postcondition: Login page is displayed
@app.route('/', methods=('GET','POST'))
def login():
    global userRole

    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor=conn.cursor()
        cursor.execute('SELECT * FROM users where email=(?)', [email,])
        user=list(cursor.fetchone())
        Us = load_user(user[0])

        if email == Us.email and bcrypt.checkpw(password.encode('utf-8'), Us.password):
            login_user(Us)
            if Us.get_admin_stat() == 1:
                userRole = "staff"
                return redirect(url_for('staffIndex'))
            else:
                userRole = "student"
                return redirect(url_for('studentIndex'))
        else:
            flash('Login unsuccessful')

        cursor.connection.commit()
        conn.close()
        
    return render_template('login.html', bool=True)
# end login()

    


# Student Sign Up Page - needs security updates
# Precondition: User is not registered
# Postcondition: User is registered, redirect to login page 
@app.route('/signup', methods=('GET','POST'))
def signup():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        password = request.form['password']
        confPass = request.form['confPass']

        #********add check to see if user is already registered*********

        if password != confPass:
            flash('Passwords do not match', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters', category='error')
        elif "@uvawise.edu" not in email:
            flash('You must use a vaild UVA Wise email address')
        else:
            conn = get_db_connection()
            password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            conn.execute('INSERT INTO users (email, password, firstName, lastName, isAdmin) VALUES (?, ?, ?, ? ,?)',
                         (email, password, firstName, lastName, 0))
            conn.commit()
            conn.close()
            flash('Account created', category='success')
            return redirect(url_for('login'))

    return render_template('signup.html', bool=True)
# end signup()




# Add Staff Member Page - needs security updates
# Precondition: An already registered staff member login is required
# Postcondition: New staff member is registered, redirect to staff home. Current user is not changed
@app.route('/addStaff', methods=('GET','POST'))
@login_required
def addStaff():
    global userRole

    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        password = request.form['password']
        confPass = request.form['confPass']

        # Needs more password requirements
        # Needs password hashing
        if password != confPass:
            flash('Passwords do not match', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters', category='error')
        elif "@uvawise.edu" not in email:
            flash('You must use a vaild UVA Wise email address')
        else:
            conn = get_db_connection()
            password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            conn.execute('INSERT INTO users (email, password, firstName, lastName, isAdmin) VALUES (?, ?, ?, ? ,?)',
                         (email, password, firstName, lastName, 1))
            conn.commit()
            conn.close()
            flash('Account created successfully', category='success')
            return redirect(url_for('staffIndex'))

    return render_template('addStaff.html', bool=True, user_role=userRole)
# end signup()




# Staff Home Page - working
# Precondition: Staff login required
# Postcondition: List of current events is displayed, links go to "Edit Event" page
@app.route('/staffIndex')
@login_required
def staffIndex():
    global userRole

    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events').fetchall()

    conn.close()

    return render_template('staffIndex.html', events=events, user_role=userRole)
# end staffIndex()




# Student Home Page - working
# Precondition: Student login required
# Postcondition: List of current incomplete events is displayed, links go to "Event" pages
@app.route('/studentIndex')
@login_required
def studentIndex():
    global userRole

    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events WHERE id NOT IN (SELECT event_id FROM completedEvents WHERE user_id=(?))', [current_user.id]).fetchall()
    
    conn.close()

    return render_template('studentIndex.html', events=events, user_role=userRole)
# end studentIndex()




# Event Page - working
# Precondition: Student login required
# Postcondition: Tasks of specific event is displayed, allows uploads and completion of task, and completion of event
@app.route('/<int:eventID>', methods=('GET','POST'))
@login_required
def event(eventID):
    global userRole

    event = get_event(eventID)
    tasks = event['tasks']

    # Fetch the responses from studentTasks table for current user
    responses = {}
    conn = get_db_connection()
    for task in tasks:
        task_id = task['task_id']
        response = conn.execute('SELECT response FROM studentTasks WHERE event_id = ? AND user_id = ? AND task_id = ?', (eventID, current_user.id, task_id)).fetchone()
        responses[task_id] = response[0] if response else None
    conn.close()

    if request.method == 'POST':
        conn = get_db_connection()

        for task in tasks:
            task_id = task['task_id']
            uploadType = task['uploadType']
            
            if uploadType == 'text':
                response = request.form.get(f'text_{task_id}')
            elif uploadType == 'image':
                image = request.files.get(f'imageFile_{task_id}')
                response = image.read() if image else None
            elif uploadType == 'link':
                response = request.form.get(f'link_{task_id}')

            if response:
                conn.execute('INSERT OR REPLACE INTO studentTasks (task_id, event_id, user_id, hasResponse, response) VALUES (?, ?, ?, ?, ?)',
                             (task_id, eventID, current_user.id, 1, response))

        # Check which submit button is used
        action = request.form['action']

        if action == "completeTask":
            # Complete individual task
            flash('Task completed successfully!', category='success')
            conn.commit()
            conn.close()
            return redirect(url_for('event', eventID=eventID))
        
        elif action == "completeEvent":
            # Check if all tasks are completed
            completedTasks = conn.execute('SELECT COUNT(*) FROM studentTasks WHERE event_id = ? AND user_id = ? AND hasResponse = 1', (eventID, current_user.id)).fetchone()[0]
            totalTasks = len(tasks)

            if completedTasks == totalTasks:
                # Move completed event to completedEvents table
                conn.execute('INSERT INTO completedEvents (event_id, user_id, title, imageBlob) VALUES (?, ?, ?, ?)', 
                             (eventID, current_user.id, event['title'], event['imageBlob']))
                flash('Congratulations! Experience successfully completed')
                conn.commit()
                conn.close()
                return redirect(url_for('studentIndex'))
            else:
                flash('Error: Some tasks were not completed')

        conn.close()

    return render_template('event.html', event=event, user_role=userRole, responses=responses)
# end event()




# Completed Events Index - working
# Precondition: Student login required
# Poscondition: Displays list of completed events of current user
@app.route('/completedEvents')
@login_required
def completedEvents():
    global userRole

    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events WHERE id IN (SELECT event_id FROM completedEvents WHERE user_id=(?))', [current_user.id]).fetchall()

    conn.close()

    return render_template('completedEvents.html', events=events, user_role=userRole)
# end completedEvents()




# Completed Event Page - working
# Page for a specific event completed by a student, also displays content uploaded by student
# Precondition: Student login and completed event required
# Postcondition: Content of specific completed event is displayed
@app.route('/completedEvent/<int:eventID>', methods=('GET','POST'))
@login_required
def completedEvent(eventID):
    global userRole

    event = get_event(eventID)
    tasks = event['tasks']

    responses = {}
    conn = get_db_connection()
    for task in tasks:
        task_id = task['task_id']
        response = conn.execute('SELECT response FROM studentTasks WHERE event_id = ? AND user_id = ? AND task_id = ?', (eventID, current_user.id, task_id)).fetchone()
        responses[task_id] = response[0] if response is not None else None
    conn.close()
     
    return render_template('completedEvent.html', eventID=eventID, event=event, user_role=userRole, responses=responses)
# end completedEvent()




# Badges Page - working
# Precondition: Student login required
# Postcondition: Displays earned and unearned badges for events of current user
@app.route('/badges')
@login_required
def badges():
    global userRole

    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events WHERE id NOT IN (SELECT event_id FROM completedEvents WHERE user_id=(?))', [current_user.id]).fetchall()
    completedEvents = conn.execute('SELECT * FROM events WHERE id IN (SELECT event_id FROM completedEvents WHERE user_id=(?))', [current_user.id]).fetchall()
    conn.close()
    
    return render_template('badges.html', user_role=userRole, events=events, completedEvents=completedEvents)
# end badges()




# Event Creation Page - working
# Precondition: Staff login required
# Postcondition: "Event Creation" form is displayed
@app.route('/create', methods=('GET','POST'))
@login_required
def create():
    global userRole

    if request.method == 'POST':
        image = request.files.get('imageFile')
        title = request.form.get('title')
        image_blob = None
        
        # Check for image
        if image:
            image_blob = image.read()  # Read image data

        if not title:
            flash('Title is required')
        elif not image_blob:
            flash('Cover image is required')
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Insert event title and in database
                cursor.execute('INSERT INTO events (title, imageBlob) VALUES (?, ?)', (title, image_blob))
                event_id = cursor.lastrowid  # Get ID of new event
                
                # Get task info
                taskDescriptions = request.form.getlist('taskDescription[]')
                uploadTypes = request.form.getlist('uploadType[]')
                
                # Insert each task into database
                for description, upload_type in zip(taskDescriptions, uploadTypes):
                    cursor.execute('INSERT INTO tasks (event_id, description, uploadType) VALUES (?, ?, ?)', (event_id, description, upload_type))
                
                conn.commit()
                flash('Event created successfully', category='success')
                return redirect(url_for('staffIndex'))
            
            except sqlite3.Error:
                flash("Error creating event")
            
            finally:
                conn.close()
        
    return render_template('create.html', user_role=userRole)
# end create()




# Edit Event Page - working
# Precondition: Staff login required
# Postcondition: "Edit Event" form is displayed
@app.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    global userRole
    event = get_event(id)

    if request.method == 'POST':
        title = request.form['title']
        image = request.files.get('imageFile')
        image_blob = None
        
        # Check for image
        if image:
            image_blob = image.read()  # Read image data

        if not title:
            flash('Title is required')
        else:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Update event title and cover image
                if image_blob:
                    cursor.execute('UPDATE events SET title = ?, imageBlob = ? WHERE id = ?', (title, image_blob, id))
                else:
                    cursor.execute('UPDATE events SET title = ? WHERE id = ?', (title, id))
                
                conn.commit()
                
                # Update task info
                taskDescriptions = request.form.getlist('task_description[]')
                uploadTypes = request.form.getlist('task_upload_type[]')
                
                # Delete existing tasks to be replaced
                cursor.execute('DELETE FROM tasks WHERE event_id = ?', (id,))
                
                # Update new tasks in database
                for description, upload_type in zip(taskDescriptions, uploadTypes):
                    cursor.execute('INSERT INTO tasks (event_id, description, uploadType) VALUES (?, ?, ?)', (id, description, upload_type))

                conn.commit()
                
                flash("Event updated successfully", category='success')
                return redirect(url_for('staffIndex'))
            
            except sqlite3.Error:
                flash("Error editing event")
            
            finally:
                conn.close()

    return render_template('edit.html', event=event, user_role=userRole)
# end edit()




# Delete Event Function - working
# Precondition: Staff login and exisiting event required, "Delete" is on "Edit Event" page
# Postcondition: All instances of the event are removed from the database
@app.route('/<int:id>/delete', methods=('POST', 'GET'))
@login_required
def delete(id):
    event=get_event(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM events WHERE id = ?', (id,))
    conn.execute('DELETE FROM tasks WHERE event_id = ?', (id,))
    conn.execute('DELETE FROM studentTasks WHERE event_id = ?', (id,))
    conn.execute('DELETE FROM completedEvents WHERE event_id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted.'.format(event['title']))
    return redirect(url_for('staffIndex'))
# end delete()




# ------------------------------Hosting------------------------------ #

# App hosted locally at http://127.0.0.1:8000 for testing
#if(__name__=='__main__'):
#    app.run(host="127.0.0.1", port=8000, debug=True)

# App hosted at http://sc-hunt.mcs.uvawise.edu:22
#if(__name__=='__main__'):
#    app.run(host="sc-hunt.mcs.uvawise.edu", port=22, debug=True)

# App hosted at http://sc-hunt.mcs.uvawise.edu:80
#if(__name__=='__main__'):
#    app.run(host="sc-hunt.mcs.uvawise.edu", port=80, debug=True)

# App hosted at http://sc-hunt.mcs.uvawise.edu:443
if(__name__=='__main__'):
    app.run(host="sc-hunt.mcs.uvawise.edu", port=443, debug=True)

# EOF
