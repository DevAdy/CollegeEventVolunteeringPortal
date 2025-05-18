from flask import Flask, render_template, redirect, url_for, request, session, flash
import db  # Import our database module
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'volunteer_management_secret_key'


# Add this near the top of app.py after the app is created
@app.template_filter('format_date')
def format_date(date_string):
    if not date_string:
        return ''
    
    try:
        # Try parsing the date string
        if isinstance(date_string, str):
            # Try different date formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d'
            ]
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_string, fmt)
                    break
                except ValueError:
                    continue
            else:
                # If no format matches, return as is
                return date_string
        else:
            # Already a datetime object
            date_obj = date_string
            
        # Format the date
        return date_obj.strftime('%b %d, %Y %I:%M %p')
    except Exception:
        # Return original if any error occurs
        return date_string

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
    redemptions = db.get_all_redemptions()  # Add this to get redemption count
    
    total_students = len(students)
    total_events = len(events)
    total_points = sum(student['points'] for student in students)
    
    return render_template('admin/dashboard.html', 
                          total_students=total_students,
                          total_events=total_events,
                          total_points=total_points,
                          events=events,
                          students=students,        # Add this to pass students to template
                          redemptions=redemptions)  # Add this for redemption count

@app.route('/admin/students')
def student_list():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get detailed student info from database
    students = db.get_students_detailed()
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
@app.route('/rewards')
def rewards_list():
    # Get rewards from database
    rewards = db.get_all_rewards()
    
    # Get user redemptions if user is logged in (not admin)
    user_redemptions = []
    user = None
    
    if session.get('is_user'):
        user_id = session.get('user_id')
        user = db.get_user(user_id)
        user_redemptions = db.get_user_redemptions(user_id)
    
    return render_template('rewards.html', 
                          rewards=rewards, 
                          redemptions=user_redemptions,
                          user=user)

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
    
    pre_selected_student = request.args.get('student_id')
    pre_selected_event = request.args.get('event_id')
    
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
                return render_template('register_volunteer.html', events=events, students=students, 
                                      pre_selected_student=pre_selected_student, 
                                      pre_selected_event=pre_selected_event)
        else:
            student_id = session.get('user_id')
        
        # Validate form data
        if not event_id:
            flash('Please select an event.')
            events = db.get_all_events()
            students = db.get_all_students() if session.get('is_admin') else []
            return render_template('register_volunteer.html', events=events, students=students,
                                  pre_selected_student=pre_selected_student,
                                  pre_selected_event=pre_selected_event)
        
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
    return render_template('register_volunteer.html', 
                          events=events, 
                          students=students,
                          pre_selected_student=pre_selected_student,
                          pre_selected_event=pre_selected_event)

# Add this route to app.py
@app.route('/admin/adjust_points', methods=['POST'])
def adjust_points():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get form data
    student_id = request.form.get('studentId')
    points_amount = request.form.get('pointsAmount')
    reason = request.form.get('pointsReason')
    
    # Validate input
    try:
        student_id = int(student_id)
        points_amount = int(points_amount)
    except (ValueError, TypeError):
        flash('Invalid input data')
        return redirect(url_for('points_page'))
    
    # Call the database function to adjust points
    success, result = db.adjust_student_points(student_id, points_amount, reason)
    
    if success:
        flash(f'Points updated successfully! New total: {result}')
    else:
        flash(f'Error: {result}')
    
    return redirect(url_for('points_page'))

@app.route('/redeem_reward', methods=['GET', 'POST'])
def redeem_reward():
    if not session.get('is_admin') and not session.get('is_user'):
        return redirect(url_for('login'))
    
    pre_selected_reward = request.args.get('reward_id')
    
    if request.method == 'POST':
        # Get form data
        reward_id = request.form.get('reward')
        notes = request.form.get('notes')
        
        # Determine student ID based on user type
        if session.get('is_admin'):
            student_id = request.form.get('student')
            if not student_id:
                flash('Please select a student.')
                rewards = db.get_all_rewards()
                students = db.get_all_students()
                return render_template('redeem_reward.html', rewards=rewards, students=students, pre_selected_reward=pre_selected_reward)
        else:
            student_id = session.get('user_id')
        
        # Validate basic form data
        if not reward_id:
            flash('Please select a reward.')
            rewards = db.get_all_rewards()
            students = db.get_all_students() if session.get('is_admin') else []
            return render_template('redeem_reward.html', rewards=rewards, students=students, pre_selected_reward=pre_selected_reward)
        
        # Strict validation: Get current student points and reward cost
        student = db.get_user(student_id)
        
        # Get reward details 
        rewards_list = db.get_all_rewards()
        reward = None
        for r in rewards_list:
            if str(r['id']) == str(reward_id):
                reward = r
                break
        
        if not student or not reward:
            flash('Invalid student or reward.')
            return redirect(url_for('rewards_list'))
        
        # CRITICAL CHECK: Ensure student has enough points
        if student['points'] < reward['points_required']:
            flash(f"Error: Insufficient points. You need {reward['points_required']} points but only have {student['points']}.")
            return redirect(url_for('rewards_list')) 
        
        # If we get here, the student definitely has enough points
        success, result = db.redeem_reward(student_id, reward_id, notes)
        
        if success:
            reward_details = result
            flash(f"Reward '{reward_details['reward_name']}' redeemed successfully! You have {reward_details['remaining_points']} points remaining.")
            
            if session.get('is_admin'):
                return redirect(url_for('redemption_history'))
            else:
                return redirect(url_for('rewards_list'))
        else:
            flash(f'Error: {result}')
    
    # Get available rewards for display
    rewards = db.get_all_rewards()
    
    # For admin, get all students; for users, get just their info
    if session.get('is_admin'):
        students = db.get_all_students()
    else:
        user_id = session.get('user_id')
        user = db.get_user(user_id)
        students = [{'id': user['id'], 'name': user['name'], 'points': user['points']}] if user else []
    
    return render_template('redeem_reward.html', rewards=rewards, students=students, pre_selected_reward=pre_selected_reward)

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
    
    # Get user's redemptions
    redemptions = db.get_user_redemptions(user_id)
    
    # Get rewards
    rewards = db.get_all_rewards()
    
    return render_template('user/dashboard.html', 
                          user=user,
                          upcoming_events=upcoming_events,
                          rewards=rewards,
                          registrations=registrations,
                          redemptions=redemptions,
                          redemption_count=len(redemptions))

@app.route('/user/my_points')
def my_points():
    if not session.get('is_user'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    # Get user data from database
    user = db.get_user(user_id)
    
    if not user:
        return redirect(url_for('logout'))
    
    # Get user's volunteer registrations (for the activities table)
    registered_events = db.get_student_registrations(user_id)
    
    # Get detailed points history (earned and spent)
    points_history = db.get_student_points_history(user_id)
    
    return render_template('user/my_points.html', 
                          user=user,
                          registered_events=registered_events,
                          points_history=points_history)

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

@app.route('/user/my_registrations')
def my_registrations():
    if not session.get('is_user'):
        return redirect(url_for('login'))
    
    # Redirect to my_points since we've consolidated the functionality
    return redirect(url_for('my_points'))


@app.route('/user/my_redemptions')
def my_redemptions():
    if not session.get('is_user'):
        return redirect(url_for('login'))
    
    # Redirect to rewards page
    return redirect(url_for('rewards_list'))

# Add this route to app.py after add_student route
@app.route('/admin/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Get student info for editing
    student = db.get_user(student_id)
    
    if not student:
        flash('Student not found.')
        return redirect(url_for('student_list'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        password = request.form.get('password', '')  # Optional (only update if provided)
        confirm_password = request.form.get('confirm_password', '')
        points = request.form.get('points', student['points'])
        
        try:
            points = int(points)
            if points < 0:
                points = 0
        except ValueError:
            points = student['points']
        
        # Validate inputs
        errors = []
        
        # Validate name
        name_valid, name_msg = db.is_valid_name(name)
        if not name_valid:
            errors.append(name_msg)
        
        # Validate email
        if not db.is_valid_email(email):
            errors.append("Please enter a valid email address")
        
        # Validate password if provided
        if password:
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
            return render_template('admin/edit_student.html', student=student)
        
        # Update student in the database
        success, result = db.update_student(student_id, name, email, phone, password, points)
        
        if success:
            flash('Student updated successfully!')
            return redirect(url_for('student_list'))
        else:
            flash(f'Error: {result}')
    
    return render_template('admin/edit_student.html', student=student)

if __name__ == '__main__':
    app.run(debug=True)