from flask import Flask, render_template, redirect, url_for, request, session, flash

app = Flask(__name__)
app.secret_key = 'volunteer_management_secret_key'

# Simulated data
events = [
    {"id": 1, "name": "Campus Cleanup", "date": "2025-05-15", "location": "Main Quad", "points": 50},
    {"id": 2, "name": "Charity Run", "date": "2025-05-20", "location": "City Park", "points": 75},
    {"id": 3, "name": "Food Drive", "date": "2025-06-01", "location": "Student Center", "points": 60},
    {"id": 4, "name": "Tech Workshop", "date": "2025-06-10", "location": "Engineering Building", "points": 40}
]

students = [
    {"id": 1, "name": "John Doe", "email": "john@example.com", "password": "password", "points": 125},
    {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "password": "password", "points": 90},
    {"id": 3, "name": "Alex Johnson", "email": "alex@example.com", "password": "password", "points": 200}
]

rewards = [
    {"id": 1, "name": "Campus Bookstore Voucher", "points_required": 100},
    {"id": 2, "name": "Cafeteria Meal Pass", "points_required": 75},
    {"id": 3, "name": "University Merchandise", "points_required": 150},
    {"id": 4, "name": "Priority Course Registration", "points_required": 200}
]

redemptions = [
    {"id": 1, "student_id": 1, "reward_id": 1, "date": "2025-04-10"},
    {"id": 2, "student_id": 3, "reward_id": 4, "date": "2025-04-15"}
]

registrations = [
    {"id": 1, "student_id": 1, "event_id": 1},
    {"id": 2, "student_id": 2, "event_id": 2},
    {"id": 3, "student_id": 3, "event_id": 1},
    {"id": 4, "student_id": 1, "event_id": 3}
]

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin123':
            session['user_id'] = 'admin'
            session['is_admin'] = True
            session['is_user'] = False
            session['name'] = 'Administrator'
            return redirect(url_for('admin_dashboard'))
        
        for student in students:
            if student['email'] == username and student['password'] == password:
                session['user_id'] = student['id']
                session['is_admin'] = False
                session['is_user'] = True
                session['name'] = student['name']
                return redirect(url_for('user_dashboard'))
        
        flash('Invalid credentials. Please try again.')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # In a real app, we would save the user data
        # Here we just simulate a successful signup
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))
    
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
    
    return render_template('admin/students.html', students=students)

@app.route('/admin/add_student', methods=['GET', 'POST'])
def add_student():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Simulate adding a student
        flash('Student added successfully!')
        return redirect(url_for('student_list'))
    
    return render_template('admin/add_student.html')

@app.route('/admin/events')
def event_list():
    return render_template('events.html', events=events)

@app.route('/admin/add_event', methods=['GET', 'POST'])
def add_event():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Simulate adding an event
        flash('Event added successfully!')
        return redirect(url_for('event_list'))
    
    return render_template('admin/add_event.html')

@app.route('/admin/points')
def points_page():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    return render_template('admin/points.html', students=students)

@app.route('/admin/rewards')
def rewards_list():
    return render_template('rewards.html', rewards=rewards)

@app.route('/admin/add_reward', methods=['GET', 'POST'])
def add_reward():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Simulate adding a reward
        flash('Reward added successfully!')
        return redirect(url_for('rewards_list'))
    
    return render_template('admin/add_reward.html')

@app.route('/admin/redemptions')
def redemption_history():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    # Join redemptions with student and reward data
    history = []
    for redemption in redemptions:
        student = next((s for s in students if s['id'] == redemption['student_id']), None)
        reward = next((r for r in rewards if r['id'] == redemption['reward_id']), None)
        
        if student and reward:
            history.append({
                'id': redemption['id'],
                'student_name': student['name'],
                'reward_name': reward['name'],
                'date': redemption['date']
            })
    
    return render_template('admin/redemptions.html', redemptions=history)

@app.route('/register_volunteer', methods=['GET', 'POST'])
def register_volunteer():
    if not session.get('is_admin') and not session.get('is_user'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Simulate registering a volunteer
        flash('Volunteer registration successful!')
        if session.get('is_admin'):
            return redirect(url_for('event_list'))
        else:
            return redirect(url_for('user_dashboard'))
    
    return render_template('register_volunteer.html', events=events, students=students)

@app.route('/redeem_reward', methods=['GET', 'POST'])
def redeem_reward():
    if not session.get('is_admin') and not session.get('is_user'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Simulate redeeming a reward
        flash('Reward redeemed successfully!')
        if session.get('is_admin'):
            return redirect(url_for('rewards_list'))
        else:
            return redirect(url_for('user_dashboard'))
    
    return render_template('redeem_reward.html', rewards=rewards, students=students)

# User routes
@app.route('/user/dashboard')
def user_dashboard():
    if not session.get('is_user'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    user = next((s for s in students if s['id'] == user_id), None)
    
    if not user:
        return redirect(url_for('logout'))
    
    # Get upcoming events
    upcoming_events = events[:2]  # Just show first 2 events for demo
    
    return render_template('user/dashboard.html', 
                          user=user,
                          upcoming_events=upcoming_events,
                          rewards=rewards)

@app.route('/user/my_points')
def my_points():
    if not session.get('is_user'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    user = next((s for s in students if s['id'] == user_id), None)
    
    if not user:
        return redirect(url_for('logout'))
    
    # Get user's registrations
    user_registrations = [r for r in registrations if r['student_id'] == user_id]
    registered_events = []
    
    for reg in user_registrations:
        event = next((e for e in events if e['id'] == reg['event_id']), None)
        if event:
            registered_events.append(event)
    
    return render_template('user/my_points.html', 
                          user=user,
                          registered_events=registered_events)

@app.route('/user/my_redemptions')
def my_redemptions():
    if not session.get('is_user'):
        return redirect(url_for('login'))
    
    user_id = session.get('user_id')
    # Get user data
    user = next((s for s in students if s['id'] == user_id), None)
    
    if not user:
        return redirect(url_for('logout'))
    
    # Get user's redemptions
    user_redemptions = [r for r in redemptions if r['student_id'] == user_id]
    history = []
    
    for redemption in user_redemptions:
        reward = next((r for r in rewards if r['id'] == redemption['reward_id']), None)
        
        if reward:
            history.append({
                'id': redemption['id'],
                'reward_name': reward['name'],
                'date': redemption['date']
            })
    
    return render_template('user/my_redemptions.html', 
                         redemptions=history,
                         user=user)  # Pass the user data to the template

if __name__ == '__main__':
    app.run(debug=True)
