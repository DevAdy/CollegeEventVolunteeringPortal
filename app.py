from flask import Flask, render_template, redirect, url_for, request, session, flash
import db  # Import our database module
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'volunteer_management_secret_key'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Basic validation
        if not username or not password:
            flash('Both email/username and password are required.')
            return render_template('login.html')
        
        # Verify user credentials using the database
        user = db.verify_user(username, password)
        
        if user:
            session['user_id'] = user['id']
            session['is_admin'] = user['is_admin']
            session['is_user'] = not user['is_admin']
            session['name'] = user['name']
            
            if user['is_admin']:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        
        flash('Invalid credentials. Please try again.')
    
    return render_template('login.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone', '')  # Optional field
        
        # Validate all inputs
        errors = []
        
        # Validate name
        name_valid, name_msg = db.is_valid_name(name)
        if not name_valid:
            errors.append(name_msg)
        
        # Validate email
        if not db.is_valid_email(email):
            errors.append("Please enter a valid email address")
        
        # Validate password
        password_valid, password_msg = db.is_valid_password(password)
        if not password_valid:
            errors.append(password_msg)
        
        # Validate password confirmation
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        # Validate phone if provided
        if phone:
            phone_valid, phone_msg = db.is_valid_phone(phone)
            if not phone_valid:
                errors.append(phone_msg)
        
        # If there are validation errors, show them
        if errors:
            for error in errors:
                flash(error)
            return render_template('signup.html')
        
        # Create user account in the database
        user_id = db.create_user(name, email, password, phone)
        
        if user_id:
            flash('Account created successfully! Please log in.')
            return redirect(url_for('login'))
        else:
            flash('Email address already exists. Please use a different email.')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Admin routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get data from database
    students = db.get_all_students()
    events = db.get_all_events()
    
    total_students = len(students)
    total_events = len(events)
    total_points = sum(student['points'] for student in students)
    
    return render_template('admin/dashboard.html', 
                          total_students=total_students,
                          total_events=total_events,
                          total_points=total_points,
                          events=events)

@app.route('/admin/students')
def student_list():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get students from database
    students = db.get_all_students()
    return render_template('admin/students.html', students=students)

@app.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone', '')  # Optional field
        initial_points = request.form.get('initial_points', 0)
        
        try:
            initial_points = int(initial_points)
        except ValueError:
            initial_points = 0
        
        # Validate all inputs
        errors = []
        
        # Validate name
        name_valid, name_msg = db.is_valid_name(name)
        if not name_valid:
            errors.append(name_msg)
        
        # Validate email
        if not db.is_valid_email(email):
            errors.append("Please enter a valid email address")
        
        # Validate password
        password_valid, password_msg = db.is_valid_password(password)
        if not password_valid:
            errors.append(password_msg)
        
        # Validate password confirmation
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        # Validate phone if provided
        if phone:
            phone_valid, phone_msg = db.is_valid_phone(phone)
            if not phone_valid:
                errors.append(phone_msg)
        
        # If there are validation errors, show them
        if errors:
            for error in errors:
                flash(error)
            return render_template('admin/add_student.html')
        
        # Create user account in the database
        user_id = db.create_user(name, email, password, phone)
        
        if user_id:
            # If initial points > 0, update points
            if initial_points > 0:
                db.update_student_points(user_id, initial_points)
                
            flash('Student added successfully!')
            return redirect(url_for('student_list'))
        else:
            flash('Email address already exists.')
    
    return render_template('admin/add_student.html')
@app.route('/admin/events')
def event_list():
    # Get events from database
    events = db.get_all_events()
    return render_template('events.html', events=events)

@app.route('/admin/add_event', methods=['GET', 'POST'])
def add_event():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        event_name = request.form.get('event_name')
        event_date = request.form.get('event_date')
        event_location = request.form.get('event_location')
        event_points = request.form.get('event_points')
        event_description = request.form.get('event_description')
        
        # Validate inputs
        errors = []
        
        # Validate name
        if not event_name or len(event_name) < 3:
            errors.append("Event name must be at least 3 characters long")
        
        # Validate date
        date_valid, date_msg = db.is_valid_date(event_date)
        if not date_valid:
            errors.append(date_msg)
            
        # Validate location
        if not event_location or len(event_location) < 3:
            errors.append("Location must be at least 3 characters long")
            
        # Validate points
        try:
            points = int(event_points)
            if points <= 0:
                errors.append("Points must be a positive number")
        except (ValueError, TypeError):
            errors.append("Points must be a valid number")
        
        # If there are errors, show them
        if errors:
            for error in errors:
                flash(error)
            return render_template('admin/add_event.html')
        
        # Create the event
        success, result = db.create_event(
            event_name, 
            event_date, 
            event_location, 
            event_points, 
            event_description
        )
        
        if success:
            flash('Event added successfully!')
            return redirect(url_for('event_list'))
        else:
            flash(f'Error creating event: {result}')
    
    return render_template('admin/add_event.html')

@app.route('/admin/points')
def points_page():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get students with points from database
    students = db.get_all_students()
    return render_template('admin/points.html', students=students)

@app.route('/admin/rewards')
def rewards_list():
    # Get rewards from database
    rewards = db.get_all_rewards()
    return render_template('rewards.html', rewards=rewards)

@app.route('/admin/add_reward', methods=['GET', 'POST'])
def add_reward():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        reward_name = request.form.get('reward_name')
        points_required = request.form.get('points_required')
        reward_description = request.form.get('reward_description')
        
        # Validate inputs
        errors = []
        
        # Validate name
        if not reward_name or len(reward_name) < 3:
            errors.append("Reward name must be at least 3 characters long")
        
        # Validate points
        try:
            points = int(points_required)
            if points <= 0:
                errors.append("Points required must be a positive number")
        except (ValueError, TypeError):
            errors.append("Points required must be a valid number")
        
        # If there are errors, show them
        if errors:
            for error in errors:
                flash(error)
            return render_template('admin/add_reward.html')
        
        # Create the reward
        success, result = db.create_reward(
            reward_name,
            points_required,
            reward_description
        )
        
        if success:
            flash('Reward added successfully!')
            return redirect(url_for('rewards_list'))
        else:
            flash(f'Error creating reward: {result}')
    
    return render_template('admin/add_reward.html')

@app.route('/admin/redemptions')
def redemption_history():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get redemption history from database
    redemptions = db.get_all_redemptions()
    return render_template('admin/redemptions.html', redemptions=redemptions)

@app.route('/register_volunteer', methods=['GET', 'POST'])
def register_volunteer():
    if not session.get('is_admin') and not session.get('is_user'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Get form data
        event_id = request.form.get('event')
        notes = request.form.get('notes')  # This will be used as role_assigned
        
        # Determine student ID based on user type
        if session.get('is_admin'):
            student_id = request.form.get('student')
            if not student_id:
                flash('Please select a student.')
                events = db.get_all_events()
                students = db.get_all_students()
                return render_template('register_volunteer.html', events=events, students=students)
        else:
            student_id = session.get('user_id')
        
        # Validate form data
        if not event_id:
            flash('Please select an event.')
            events = db.get_all_events()
            students = db.get_all_students() if session.get('is_admin') else []
            return render_template('register_volunteer.html', events=events, students=students)
        
        # Register volunteer in the database
        success, result = db.register_volunteer(student_id, event_id, notes)
        
        if success:
            flash('Volunteer registration successful!')
            if session.get('is_admin'):
                return redirect(url_for('event_list'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash(f'Error: {result}')
    
    # Get future events only for registration
    all_events = db.get_all_events()
    events = []
    today = datetime.now().date()
    
    for event in all_events:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
        if event_date >= today:
            events.append(event)
    
    students = db.get_all_students() if session.get('is_admin') else []
    return render_template('register_volunteer.html', events=events, students=students)

@app.route('/redeem_reward', methods=['GET', 'POST'])
def redeem_reward():
    if not session.get('is_admin') and not session.get('is_user'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Reward redemption would go here
        flash('Reward redeemed successfully!')
        if session.get('is_admin'):
            return redirect(url_for('rewards_list'))
        else:
            return redirect(url_for('user_dashboard'))
    
    rewards = db.get_all_rewards()
    students = db.get_all_students()
    return render_template('redeem_reward.html', rewards=rewards, students=students)

# User routes
@app.route('/user/dashboard')
def user_dashboard():
    if not session.get('is_user'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    # Get user data from database
    user = db.get_user(user_id)
    
    if not user:
        return redirect(url_for('logout'))
    
    # Get upcoming events
    events = db.get_all_events()
    # Filter for future events only
    today = datetime.now().date()
    upcoming_events = []
    
    for event in events:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
        if event_date >= today:
            upcoming_events.append(event)
    
    # Get only the first 2 upcoming events
    upcoming_events = upcoming_events[:2]
    
    # Get user's registrations
    registrations = db.get_student_registrations(user_id)
    
    # Get rewards
    rewards = db.get_all_rewards()
    
    return render_template('user/dashboard.html', 
                          user=user,
                          upcoming_events=upcoming_events,
                          rewards=rewards,
                          registrations=registrations)

@app.route('/user/my_points')
def my_points():
    if not session.get('is_user'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    # Get user data from database
    user = db.get_user(user_id)
    
    if not user:
        return redirect(url_for('logout'))
    
    # Get user's registrations
    registered_events = db.get_student_registrations(user_id)
    
    return render_template('user/my_points.html', 
                          user=user,
                          registered_events=registered_events)

@app.route('/admin/event_volunteers/<int:event_id>')
def event_volunteers(event_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get event details
    event = None
    events = db.get_all_events()
    for e in events:
        if e['id'] == event_id:
            event = e
            break
    
    if not event:
        flash('Event not found.')
        return redirect(url_for('event_list'))
    
    # Get volunteers for this event
    volunteers = db.get_event_volunteers(event_id)
    
    return render_template('admin/event_volunteers.html', 
                          event=event,
                          volunteers=volunteers)

@app.route('/admin/update_volunteer_role/<int:registration_id>', methods=['POST'])
def update_volunteer_role(registration_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    role = request.form.get('role', '')
    event_id = request.form.get('event_id')
    student_id = request.form.get('student_id')
    
    # Update role in database
    success, result = db.update_volunteer_role(registration_id, role)
    
    if success:
        flash('Volunteer role updated successfully.')
    else:
        flash(f'Error updating role: {result}')
    
    # Redirect to appropriate page
    if event_id:
        return redirect(url_for('event_volunteers', event_id=event_id))
    elif student_id:
        return redirect(url_for('student_registrations', student_id=student_id))
    else:
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/student_registrations/<int:student_id>')
def student_registrations(student_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get student details
    student = db.get_user(student_id)
    
    if not student:
        flash('Student not found.')
        return redirect(url_for('student_list'))
    
    # Get registrations for this student
    registrations = db.get_student_registrations(student_id)
    
    return render_template('admin/student_registrations.html', 
                          student=student,
                          registrations=registrations)



@app.route('/admin/complete_registration/<int:registration_id>', methods=['POST'])
def complete_registration(registration_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Mark registration as completed and award points
    success, result = db.complete_volunteer_registration(registration_id)
    
    if success:
        flash(f'Registration marked as completed. {result} points awarded!')
    else:
        flash(f'Error: {result}')
    
    # Get the event ID to redirect back to the event volunteers page
    event_id = request.form.get('event_id', 0)
    return redirect(url_for('event_volunteers', event_id=event_id))


@app.route('/user/my_redemptions')
def my_redemptions():
    if not session.get('is_user'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    # Get user data from database
    user = db.get_user(user_id)
    
    if not user:
        return redirect(url_for('logout'))
    
    # Get user's redemptions from database
    redemptions = db.get_user_redemptions(user_id)
    
    return render_template('user/my_redemptions.html', 
                         redemptions=redemptions,
                         user=user)

if __name__ == '__main__':
    app.run(debug=True)