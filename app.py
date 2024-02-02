# Scavenger Hunt Web Application for UVA Wise
# For CSC/SWE 2300 - Intro to Software Engineering with Dr. Hatch
# Author: Jacob Davis
# Date Started: October 2, 2023

# ------------------------------Setup------------------------------------ #

import sqlite3 # For database
from flask import Flask, render_template, url_for, request, flash, redirect, Response, send_file # For construction of web apps
from werkzeug.exceptions import abort # For exception handling
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user # For login management
from base64 import b64encode # For displaying images stored as binary in database
import io
app = Flask(__name__)
app.config['SECRET_KEY'] = 'SeCrEtKeY' # Probably needs to be changed but not entirely sure what this is for

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
# Postcondition: Event info is returned or 404 if no event found
def get_event(eventID):
    conn = get_db_connection()
    event = conn.execute('SELECT * FROM events WHERE id = ?',
                        (eventID,)).fetchone()
    conn.close()
    if event is None:
        abort(404)
    return event
#end get_event()





# Completed event loader ****Unused****
# Precondition: Request for a completed event
# Postcondition: Event info is returned or 404 if no event found
def get_completed_event(eventID):
    userID = current_user.id
    conn = get_db_connection()
    completedEvent = conn.execute('SELECT * FROM completedEvents WHERE event_id = ? AND user_ID = ?',
                        (eventID,userID)).fetchone()
    conn.close()
    if completedEvent is None:
        abort(404)
    return completedEvent
#end get_completed_event()



# ---------------Login Management--------------- #

login_manager = LoginManager(app)
login_manager.login_view = "login"




# User Class
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
        return User(int(lu[0]), lu[1], lu[2], lu[3], lu[4], lu[5])
# end load_user()







# ---------------Image Processing--------------- #

# Function to convert images to binary data
# Precondition: Image file in original format
# Postcondition: Returns image converted to binary blob
def convertToBinary(filename):
    with open(filename, 'rb') as f:
        blobData = f.read()
    return blobData
# end convertToBinary()




# Function to display an image
# Precondition: ID of image to be loaded
# Poscondition: Returns image blob converted to jpeg
@app.route('/i/<int:id>')
def event_image(id):
    conn = get_db_connection()
    cursor=conn.cursor()
    cursor.execute("SELECT imageBlob FROM events WHERE id = ?", (id,))
    result = cursor.fetchone()
    image_bytes = result[0]
    bytes_io = io.BytesIO(image_bytes)
    return send_file(bytes_io, mimetype='image/jpeg')
# end event_image()




# ------------------------------Pages------------------------------ #

# Login / Landing Page
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

        if email == Us.email and password == Us.password:
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

        #********add check to see if user is already registered*********

        if password != confPass:
            flash('Passwords do not match', category='error')
        elif len(password) < 8:
            flash('Password must be at least 8 characters', category='error')
        elif "@uvawise.edu" not in email:
            flash('You must use a vaild UVA Wise email address')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (email, password, firstName, lastName, isAdmin) VALUES (?, ?, ?, ? ,?)',
                         (email, password, firstName, lastName, 0))
            conn.commit()
            conn.close()
            flash('Account created', category='success')
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
            conn.execute('INSERT INTO users (email, password, firstName, lastName, isAdmin) VALUES (?, ?, ?, ? ,?)',
                         (email, password, firstName, lastName, 1))
            conn.commit()
            conn.close()
            flash('Account created successfully', category='success')
            return redirect(url_for('staffIndex'))

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
# Postcondition: List of current incomplete events is displayed
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
# Postcondition: Content of specific event is displayed, allows uploads and completion of an event
@app.route('/<int:eventID>', methods=('GET','POST'))
@login_required
def event(eventID):
    global userRole

    event = get_event(eventID)
    uploadType = event[4]

    # Complete event
    if request.method == 'POST':
       conn = get_db_connection()

       if uploadType == 'image':
           image = request.files.get('imageFile')
           image.save(image.filename) # Saves image to project directory (temporary solution) <--This doesn't work here but works for cover images?
           imageBlob = convertToBinary(image.filename)
           conn.execute('INSERT INTO completedEvents (user_id, event_id, imageUpload) VALUES (?, ?, ?)', (current_user.id,eventID,imageBlob))
       else:
           content = request.form.get('content')
           conn.execute('INSERT INTO completedEvents (user_id, event_id, textUpload) VALUES (?, ?, ?)', (current_user.id,eventID,content))
       
       conn.commit()
       
       conn.close()
       flash('Task completed. Congratulations!', category='success')
       
       return redirect(url_for('studentIndex'))
    
     
    return render_template('event.html', event=event, user_role=userRole, uploadType=uploadType)
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

    conn.close()

    return render_template('completedEvents.html', events=events, user_role=userRole)
# end completedEvents()




# Completed Event Page **** Incomplete/Unused ****
# Page for a specific event completed by a student, also displays content uploaded by student
# Precondition: Student login and completed event required
# Postcondition: Content of specific completed event is displayed
@app.route('/completedEvent/<int:eventID>', methods=('GET','POST'))
@login_required
def completedEvent(eventID):
    conn = get_db_connection()
    global userRole

    event = get_event(eventID)
    title = event[1]
    content = event[2]
    uploadType = event[4]

    #completedEvent = get_completed_event(eventID)
    #
    #if uploadType == 'image':
    #   Convert image
    #   Set userContent = image  
    #else:
    #    userContent = completedEvent[2] #<--user uploaded text

    conn.close()
     
    return render_template('completedEvent.html', eventID=eventID, event=event, user_role=userRole,
                           title=title,content=content,uploadType=uploadType) # add userContent here
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
        content = request.form.get('content')
        uploadType = request.form.get('uploadType')

        if not image:
            flash('Cover image is required')
        elif not title:
            flash('Title is required')
        elif not content:
            flash('Content is required')
        else:
            image.save(image.filename) # Saves image to project directory (temporary solution)
            imageBlob = convertToBinary(image.filename)
            conn = get_db_connection()
            conn.execute('INSERT INTO events (title, content, imageBlob, uploadType) VALUES (?, ?, ?, ?)', (title, content, imageBlob, uploadType))
            conn.commit()
            conn.close()
            flash('Event created successfully', category='success')
            return redirect(url_for('staffIndex'))
        
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
        content = request.form['content']
        uploadType = request.form['uploadType']

        if not title:
            flash('Title is required')
        else:
            conn = get_db_connection()
            conn.execute('UPDATE events SET title = ?, content = ?, uploadType = ?'
                         'WHERE id = ?', (title, content, uploadType, id))
            conn.commit()
            conn.close()
            return redirect(url_for('staffIndex'))

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
    conn.execute('DELETE FROM completedEvents WHERE event_id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted.'.format(event['title']))
    return redirect(url_for('staffIndex'))
# end delete()




# ------------------------------Hosting------------------------------ #

# App hosted on http://127.0.0.1:8000 for testing

if(__name__=='__main__'):
    app.run(host="127.0.0.1", port=8000, debug=True)

# EOF