# Scavenger Hunt Web Application for UVA Wise
# For CSC 4990 - Computer Science Seminar with Dr. Frazier

# ------------------------------Setup------------------------------------ #

import sqlite3 # For database
from flask import Flask, render_template, url_for, request, flash, redirect, Response, send_file # For construction of web app
from werkzeug.exceptions import abort # For exception handling
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user # For login management
import base64 # For displaying images stored as binary in database
import bcrypt # For password hashing
import requests # For accessing outside weblinks (QR Code)
import json # For JSON management
import secrets # For email
from flask_mail import Mail, Message # For email
import smtplib, ssl # For email
app = Flask(__name__)
mail = Mail(app) # For email

app.config['SECRET_KEY'] = 'SeCrEtKeY'

# Email Auth - removed info for security reasons
app.config['MAIL_SERVER'] = ''
app.config['MAIL_PORT'] = 000
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
mail.init_app(app)

userRole = "" # Global variable for user type, i.e. staff or student




# ------------------------------Functions------------------------------ #

# Connects to database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn
#end get_db_connection()




# Event loader
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




# User Class
class User(UserMixin):
    def __init__(self, id, email, password, firstName, lastName, isAdmin, verificationToken, verified):
        self.id = id # Internal ID from auto incremented int in database
        self.email = email # UVA Wise email address
        self.password = password
        self.firstName = firstName
        self.lastName = lastName
        self.isAdmin = isAdmin # Distinction between staff and student
        self.verificationToken = verificationToken # Email verification token
        self.verified = verified # Boolean for if user is verified or not
    
    def is_active(self):
        return self.is_active()
    
    def is_anonymous(self):
        return False
    
    def is_verified(self):
        return self.verified
    
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




# Logout Function
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
    



# User Loader Function
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
        return User(int(lu[0]), lu[1], lu[2], lu[3], lu[4], lu[5], lu[6], lu[7])
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
    for event in data:
        # Event name, completed value (True/False)
        event_obj = {
                "event": event['Title'],
                "value": True
        }
        event_json.append(event_obj)
    return json.dumps(event_json)


# ---------------Email Verification & Password Reset--------------- #

# Function to email a verification link
def emailVerification(email, token):
    context = ssl._create_unverified_context()
    recipient = [email]
    verification_link = url_for('verifyEmail', token=token, _external=True)
    
    message = f"""From: {app.config['MAIL_USERNAME']}
    To: {email}
    Subject: Confirm Your Email with UVA Wise Scavenger Hunt
    
    Click the following link to confirm your account: {verification_link}
    """
    

    with smtplib.SMTP_SSL(app.config['MAIL_SERVER'], app.config['MAIL_PORT'], context=context) as server:
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.sendmail(app.config['MAIL_USERNAME'], recipient, message)
# end emailVerification()




# Function to email a password reset link
def emailPassword(email, token):
    context = ssl._create_unverified_context()
    recipient = [email]
    reset_link = url_for('passwordReset', token=token, _external=True)
    
    message = f"""From: {app.config['MAIL_USERNAME']}
    To: {email}
    Subject: Confirm Your Email with UVA Wise Scavenger Hunt
    
    Click the following link to reset your password: {reset_link}
    """
    

    with smtplib.SMTP_SSL(app.config['MAIL_SERVER'], app.config['MAIL_PORT'], context=context) as server:
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.sendmail(app.config['MAIL_USERNAME'], recipient, message)
#end emailPassword



        
# Funtion to verify a user
@app.route('/verify/<token>')
def verifyEmail(token):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE verificationToken = ?', [token,])
    user = list(cursor.fetchone())
    if user:
        Us = load_user(user[0])
        id = Us.get_id
        cursor.execute('UPDATE users SET verified = ? WHERE id = ?', (True, id))
        flash('Your account was successfully verified', category='success')
    else:
        flash('There was an issue processing your request', category='error')
    return redirect(url_for('login'))

        
# ------------------------------Pages------------------------------ #

# Login / Landing Page
# Precondition: Navigation to website url, no user logged in
# Postcondition: Login page is displayed
@app.route('/', methods=('GET','POST'))
def login():
    global userRole

    if request.method=='POST':
        email = request.form['email'].lower()
        password = request.form['password']

        # Checks for SQL injection
        if sql_injection_detection(email) == False:
            email = None
            return redirect(url_for('login'))
        elif sql_injection_detection(password) == False:
            password = None
            return redirect(url_for('login'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users where email=(?)', [email,])
        try:
            user=list(cursor.fetchone())
            Us = load_user(user[0])

            if email == Us.email and bcrypt.checkpw(password.encode('utf-8'), Us.password):  # and Us.is_verified
                login_user(Us)
                if Us.get_admin_stat() == 1:
                    userRole = "staff"
                    return redirect(url_for('staffIndex'))
                else:
                    userRole = "student"
                    return redirect(url_for('studentIndex'))
        except:
            flash('Login unsuccessful', category='error')
            
        cursor.connection.commit()
        conn.close()
        
    return render_template('login.html', bool=True)
# end login()




# Forgot Password Page
@app.route('/forgotPassword', methods=('GET','POST'))
def forgotPassword():
    if request.method=='POST':
        email = request.form['email']

        # Check for SQL injection
        if sql_injection_detection(email) == False:
            email = None
            return redirect(url_for('forgotPassword'))

        # Generate password reset token
        token = secrets.token_hex(16)

        # Send password reset email
        #emailPassword(email, token)
            
        flash('Please check your email for a password reset link', category='success')
        return redirect(url_for('login'))
        
    return render_template('forgotPassword.html', bool=True)
# end forgotPassword()




# Password Reset Page
@app.route('/passwordReset/<token>', methods=('GET','POST'))
def passwordReset(token):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confPass = request.form['confPass']

        # Checks for SQL injection
        if sql_injection_detection(email) == False:
            email = None
            return redirect(url_for('passwordReset/<token>'))
        if sql_injection_detection(password) == False:
            password = None
            return redirect(url_for('passwordReset/<token>'))
        if sql_injection_detection(confPass) == False:
            confPass = None
            return redirect(url_for('passwordReset/<token>'))

        conn = get_db_connection()
        cursor.execute('SELECT * FROM users WHERE passwordToken = ?', [token,])
        user = list(cursor.fetchone())
        if user and password == confPass and len(password) > 8:
            Us = load_user(user[0])
            id = Us.get_id
            password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', (password, id))
            flash('Your password was successfully reset', category='success')
            return redirect(url_for('login'))
        else:
            flash('There was an issue processing your request', category='error')

    return render_template('passwordreset.html', bool=True)
#end passwordReset()




# Student Sign Up Page
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

        # Checks for SQL injection
        if sql_injection_detection(email) == False:
            email = None
            return redirect(url_for('signup'))
        elif sql_injection_detection(firstName) == False:
            firstName = None
            return redirect(url_for('signup'))
        elif sql_injection_detection(lastName) == False:
            lastName = None
            return redirect(url_for('signup'))
        elif sql_injection_detection(password) == False:
            password = None
            return redirect(url_for('signup'))
        elif sql_injection_detection(confPass) == False:
            confPass = None
            return redirect(url_for('signup'))

        # Check if user is already registered
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email=?', [email])
        if cursor.fetchone():
            conn.close()
            flash('Error: Email already registered', category='error')
            return redirect(url_for('signup'))

        if password != confPass:
            flash('Passwords do not match', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters', category='error')
        elif "@uvawise.edu" not in email:
            flash('You must use a vaild UVA Wise email address')
        else:
            # Generate verification token
            token = secrets.token_hex(16)
            
            # Insert user into database
            conn = get_db_connection()
            password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            conn.execute('INSERT INTO users (email, password, firstName, lastName, isAdmin, verificationToken, verified) VALUES (?, ?, ?, ? ,?, ?, ?)',
                         (email, password, firstName, lastName, 0, token, 0))
            conn.commit()
            conn.close()

            # Send verification email
            #emailVerification(email, token)
            
            flash('Account created. Please check your email for a verification link', category='success')
            return redirect(url_for('login'))

    return render_template('signup.html', bool=True)
# end signup()




# Add Staff Member Page
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

        # Check if user is already registered
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email=?', [email])
        if cursor.fetchone():
            conn.close()
            flash('Error: Email already registered', category='error')
            return redirect(url_for('signup'))

        
        if password != confPass:
            flash('Passwords do not match', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters', category='error')
        elif "@uvawise.edu" not in email:
            flash('You must use a vaild UVA Wise email address')
        else:
            # Generate verification token
            token = secrets.token_hex(16)
            
            # Insert user into database
            conn = get_db_connection()
            password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            conn.execute('INSERT INTO users (email, password, firstName, lastName, isAdmin, verificationToken, verified) VALUES (?, ?, ?, ? ,?, ?, ?)',
                         (email, password, firstName, lastName, 1, token, 0))
            conn.commit()
            conn.close()

            # Email verification
            #emailVerification(email, token)

            flash('Account created. Please check your email for a verification link', category='success')
            return redirect(url_for('addStaff.html'))

    return render_template('addStaff.html', bool=True, user_role=userRole)
# end signup()




# Staff Home Page
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




# Student Home Page
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




# Event Page
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
                if response and sql_injection_detection(response) == False:
                    response = None
            elif uploadType == 'image':
                image = request.files.get(f'imageFile_{task_id}')
                response = image.read() if image else None
            elif uploadType == 'link':
                response = request.form.get(f'link_{task_id}')
                if response and sql_injection_detection(response) == False:
                    response = None

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




# Completed Events Index
# Precondition: Student login required
# Poscondition: Displays list of completed events of current user
@app.route('/completedEvents')
@login_required
def completedEvents():
    global userRole

    conn = get_db_connection()
    events = conn.execute('SELECT * FROM events WHERE id IN (SELECT event_id FROM completedEvents WHERE user_id=(?))', [current_user.id]).fetchall()

    #json_events = generate_event_json(events)
    #qr_code = generate_qr_code(json_events)
    #print(qr_code)

    conn.close()

    return render_template('completedEvents.html', events=events, user_role=userRole)
# end completedEvents()




# Completed Event Page
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




# Badges Page
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




# Event Creation Page
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




# Edit Event Page
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




# Delete Event Function
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




# SQL Injection Scanner
# Precondition: User inputs a string when prompted where it is sent to the function
# Postcondition: Function checks the input for SQL injection patters. If found, input is denied. If not, input is accepted.
def sql_injection_detection(user_input):
        # Tuple of patterns found in SQL injections
        injection_patterns = (";", "--", "/*", "*/", "xp_", "sleep", "benchmark", "=")
        # Check input for patterns
        if any(pattern in user_input.lower() for pattern in injection_patterns):
            # Log the injection attempt
            # logging.warning(f"SQL injection detected - Input: {user_input}"): this line can be used to create a log file of all of the attempts on the server.
            # Return False to indicate login failure
            return False
        else:
            # Return True to indicate there are no SQL injection patterns within input
            return True
# end detect_sql_injection()




                        
# ------------------------------Hosting------------------------------ #

# App hosted locally at http://127.0.0.1:8000 for testing
if(__name__=='__main__'):
    app.run(host="127.0.0.1", port=8000, debug=True)

# App hosted at http://sc-hunt.mcs.uvawise.edu:##
#if(__name__=='__main__'):
#    app.run(host="sc-hunt.mcs.uvawise.edu", port=##, debug=True)

# App hosted at http://sc-hunt.mcs.uvawise.edu:##
#if(__name__=='__main__'):
#    app.run(host="sc-hunt.mcs.uvawise.edu", port=##, debug=True)

# App hosted at http://sc-hunt.mcs.uvawise.edu:###
#if(__name__=='__main__'):
#    app.run(host="sc-hunt.mcs.uvawise.edu", port=###, debug=True)

# EOF

