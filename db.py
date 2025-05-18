import sqlite3
import os
import hashlib
from datetime import datetime
import re 

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'volunteer_db.sqlite')

def get_db_connection():
    """Create a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def init_db():
    """Initialize the database with tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create Student table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        created_at TIMESTAMP
    )
    ''')
    
    # Create Events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        location TEXT NOT NULL,
        points INTEGER NOT NULL,
        description TEXT,
        created_at TIMESTAMP
    )
    ''')
    
    # Create VolunteerRegistration table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        event_id INTEGER NOT NULL,
        role_assigned TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (event_id) REFERENCES events (id)
    )
    ''')
    
    # Create Points table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS points (
        student_id INTEGER PRIMARY KEY,
        total_points INTEGER DEFAULT 0,
        last_updated TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )
    ''')
    
    # Create Rewards table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rewards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        points_required INTEGER NOT NULL,
        description TEXT,
        created_at TIMESTAMP
    )
    ''')
    
    # Create Redemptions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS redemptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        reward_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        created_at TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (reward_id) REFERENCES rewards (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS points_adjustments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        points_amount INTEGER NOT NULL,
        reason TEXT,
        adjusted_at TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )
    ''')
    # Add admin user if not exists
    cursor.execute('SELECT * FROM students WHERE email = ?', ('admin@volunteerhub.com',))
    admin = cursor.fetchone()
    
    if not admin:
        # Hash the admin password
        hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
        
        cursor.execute('''
        INSERT INTO students (name, email, password, created_at)
        VALUES (?, ?, ?, ?)
        ''', ('Administrator', 'admin@volunteerhub.com', hashed_password, datetime.now()))
        
        # Create points entry for admin
        cursor.execute('''
        INSERT INTO points (student_id, total_points, last_updated)
        VALUES ((SELECT id FROM students WHERE email = 'admin@volunteerhub.com'), 0, ?)
        ''', (datetime.now(),))
    
    # Insert sample data if tables are empty
    # Check if events table is empty
    cursor.execute('SELECT COUNT(*) FROM events')
    event_count = cursor.fetchone()[0]
    
    if event_count == 0:
        # Insert sample events
        events_data = [
            ('Campus Cleanup', '2025-05-15', 'Main Quad', 50, 'Help clean up the campus grounds', datetime.now()),
            ('Charity Run', '2025-05-20', 'City Park', 75, 'Annual charity run for local causes', datetime.now()),
            ('Food Drive', '2025-06-01', 'Student Center', 60, 'Collect food items for local food banks', datetime.now()),
            ('Tech Workshop', '2025-06-10', 'Engineering Building', 40, 'Teach basic coding to high school students', datetime.now())
        ]
        
        cursor.executemany('''
        INSERT INTO events (name, date, location, points, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', events_data)
    
    # Check if rewards table is empty
    cursor.execute('SELECT COUNT(*) FROM rewards')
    reward_count = cursor.fetchone()[0]
    
    if reward_count == 0:
        # Insert sample rewards
        rewards_data = [
            ('Campus Bookstore Voucher', 100, 'A $20 voucher for the campus bookstore', datetime.now()),
            ('Cafeteria Meal Pass', 75, 'Free meal at the university cafeteria', datetime.now()),
            ('University Merchandise', 150, 'Choose from university-branded items', datetime.now()),
            ('Priority Course Registration', 200, 'Register for courses before your peers', datetime.now())
        ]
        
        cursor.executemany('''
        INSERT INTO rewards (name, points_required, description, created_at)
        VALUES (?, ?, ?, ?)
        ''', rewards_data)
    
    conn.commit()
    conn.close()

def create_user(name, email, password, phone=None):
    """Create a new user account"""
    # First validate inputs
    name_valid, name_msg = is_valid_name(name)
    if not name_valid:
        return None
        
    if not is_valid_email(email):
        return None
        
    password_valid, password_msg = is_valid_password(password)
    if not password_valid:
        return None
        
    if phone:
        phone_valid, phone_msg = is_valid_phone(phone)
        if not phone_valid:
            return None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Insert the new user
        cursor.execute('''
        INSERT INTO students (name, email, password, phone, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, email, hashed_password, phone, datetime.now()))
        
        # Get the inserted user ID
        user_id = cursor.lastrowid
        
        # Initialize points for the user
        cursor.execute('''
        INSERT INTO points (student_id, total_points, last_updated)
        VALUES (?, ?, ?)
        ''', (user_id, 0, datetime.now()))
        
        conn.commit()
        return user_id
    
    except sqlite3.IntegrityError:
        # This will occur if the email already exists
        return None
    finally:
        conn.close()
def verify_user(email, password):
    """Verify user credentials"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Hash the input password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Check for special admin case
    if email == 'admin' and password == 'admin123':
        cursor.execute('SELECT * FROM students WHERE email = ?', ('admin@volunteerhub.com',))
        user = cursor.fetchone()
        if user:
            conn.close()
            return {'id': user['id'], 'name': user['name'], 'email': user['email'], 'is_admin': True}
    
    # Regular user login
    cursor.execute('''
    SELECT s.*, p.total_points 
    FROM students s
    LEFT JOIN points p ON s.id = p.student_id
    WHERE s.email = ? AND s.password = ?
    ''', (email, hashed_password))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Check if this is the admin account
        is_admin = user['email'] == 'admin@volunteerhub.com'
        
        return {
            'id': user['id'],
            'name': user['name'], 
            'email': user['email'],
            'points': user['total_points'] or 0,
            'is_admin': is_admin
        }
    
    return None

def get_user(user_id):
    """Get user information by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT s.*, p.total_points 
    FROM students s
    LEFT JOIN points p ON s.id = p.student_id
    WHERE s.id = ?
    ''', (user_id,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {
            'id': user['id'],
            'name': user['name'], 
            'email': user['email'],
            'phone': user['phone'],
            'points': user['total_points'] or 0,
            'is_admin': user['email'] == 'admin@volunteerhub.com'
        }
    
    return None

def get_all_students():
    """Get all students"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT s.*, p.total_points 
    FROM students s
    LEFT JOIN points p ON s.id = p.student_id
    ORDER BY s.name
    ''')
    
    students = []
    for row in cursor.fetchall():
        students.append({
            'id': row['id'],
            'name': row['name'],
            'email': row['email'],
            'points': row['total_points'] or 0
        })
    
    conn.close()
    return students

def get_all_events():
    """Get all events"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM events ORDER BY date')
    
    events = []
    for row in cursor.fetchall():
        # Fix: Use direct access instead of .get() method
        description = row['description'] if 'description' in row.keys() else ''
        events.append({
            'id': row['id'],
            'name': row['name'],
            'date': row['date'],
            'location': row['location'],
            'points': row['points'],
            'description': description
        })
    
    conn.close()
    return events

def get_all_rewards():
    """Get all rewards"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM rewards ORDER BY points_required')
    
    rewards = []
    for row in cursor.fetchall():
        # Fix: Use direct access instead of .get() method
        description = row['description'] if 'description' in row.keys() else ''
        rewards.append({
            'id': row['id'],
            'name': row['name'],
            'points_required': row['points_required'],
            'description': description
        })
    
    conn.close()
    return rewards

def get_all_redemptions():
    """Get all redemptions with student and reward details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.id, r.date, s.name AS student_name, rw.name AS reward_name
    FROM redemptions r
    JOIN students s ON r.student_id = s.id
    JOIN rewards rw ON r.reward_id = rw.id
    ORDER BY r.date DESC
    ''')
    
    redemptions = []
    for row in cursor.fetchall():
        redemptions.append({
            'id': row['id'],
            'student_name': row['student_name'],
            'reward_name': row['reward_name'],
            'date': row['date']
        })
    
    conn.close()
    return redemptions

def get_user_redemptions(user_id):
    """Get all redemptions for a user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.id, r.date, rw.name AS reward_name
    FROM redemptions r
    JOIN rewards rw ON r.reward_id = rw.id
    WHERE r.student_id = ?
    ORDER BY r.date DESC
    ''', (user_id,))
    
    redemptions = []
    for row in cursor.fetchall():
        redemptions.append({
            'id': row['id'],
            'reward_name': row['reward_name'],
            'date': row['date']
        })
    
    conn.close()
    return redemptions

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_password(password):
    """
    Validate password strength:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def is_valid_name(name):
    """
    Validate name:
    - At least 2 characters
    - Only letters, spaces, and hyphens allowed
    """
    if len(name) < 2:
        return False, "Name must be at least 2 characters long"
    
    if not re.match(r'^[A-Za-z\s\-]+$', name):
        return False, "Name can only contain letters, spaces, and hyphens"
    
    return True, "Name is valid"

def is_valid_phone(phone):
    """
    Validate phone number:
    - Optional (can be None or empty)
    - If provided, must be a valid format (10 digits)
    """
    if not phone:
        return True, "Phone is optional"
    
    # Remove any non-digit characters for validation
    digits_only = re.sub(r'\D', '', phone)
    
    if len(digits_only) != 10:
        return False, "Phone number must be 10 digits"
    
    return True, "Phone number is valid"

def update_student_points(student_id, points_to_add):
    """Update a student's points (add points)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get current points
        cursor.execute('SELECT total_points FROM points WHERE student_id = ?', (student_id,))
        result = cursor.fetchone()
        
        if result:
            current_points = result['total_points'] or 0
            new_total = current_points + points_to_add
            
            # Update points
            cursor.execute('''
            UPDATE points 
            SET total_points = ?, last_updated = ?
            WHERE student_id = ?
            ''', (new_total, datetime.now(), student_id))
        else:
            # Create points record if it doesn't exist
            cursor.execute('''
            INSERT INTO points (student_id, total_points, last_updated)
            VALUES (?, ?, ?)
            ''', (student_id, points_to_add, datetime.now()))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating points: {e}")
        return False
    finally:
        conn.close()

def create_event(name, date, location, points, description=None):
    """Create a new event in the database"""
    # Validate inputs
    if not name or len(name) < 3:
        return False, "Event name must be at least 3 characters long"
    
    if not date:
        return False, "Event date is required"
    
    if not location or len(location) < 3:
        return False, "Location must be at least 3 characters long"
    
    try:
        points = int(points)
        if points <= 0:
            return False, "Points must be a positive number"
    except (ValueError, TypeError):
        return False, "Points must be a valid number"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO events (name, date, location, points, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, date, location, points, description, datetime.now()))
        
        event_id = cursor.lastrowid
        conn.commit()
        return True, event_id
    except Exception as e:
        print(f"Error creating event: {e}")
        return False, str(e)
    finally:
        conn.close()

def is_valid_date(date_str):
    """Validate if a string is a valid date in YYYY-MM-DD format"""
    try:
        if not date_str:
            return False, "Date is required"
            
        # Check if the format is YYYY-MM-DD
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return False, "Date must be in YYYY-MM-DD format"
            
        # Parse the date to ensure it's valid
        year, month, day = map(int, date_str.split('-'))
        datetime(year, month, day)
        
        # Check if the date is in the future
        today = datetime.now().date()
        event_date = datetime(year, month, day).date()
        
        if event_date < today:
            return False, "Event date must be in the future"
            
        return True, "Date is valid"
    except ValueError:
        return False, "Invalid date"
    
# Add this function after the create_event function
def create_reward(name, points_required, description=None):
    """Create a new reward in the database"""
    # Validate inputs
    if not name or len(name) < 3:
        return False, "Reward name must be at least 3 characters long"
    
    try:
        points_required = int(points_required)
        if points_required <= 0:
            return False, "Points required must be a positive number"
    except (ValueError, TypeError):
        return False, "Points required must be a valid number"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        INSERT INTO rewards (name, points_required, description, created_at)
        VALUES (?, ?, ?, ?)
        ''', (name, points_required, description, datetime.now()))
        
        reward_id = cursor.lastrowid
        conn.commit()
        return True, reward_id
    except Exception as e:
        print(f"Error creating reward: {e}")
        return False, str(e)
    finally:
        conn.close()

# Add these functions at the end of the file (before init_db())

def register_volunteer(student_id, event_id, role_assigned=None):
    """Register a student for an event as a volunteer"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if the student is already registered for this event
        cursor.execute('''
        SELECT id FROM registrations 
        WHERE student_id = ? AND event_id = ?
        ''', (student_id, event_id))
        
        existing = cursor.fetchone()
        if existing:
            return False, "Student is already registered for this event"
        
        # Check if the event exists and is in the future
        cursor.execute('SELECT date FROM events WHERE id = ?', (event_id,))
        event = cursor.fetchone()
        
        if not event:
            return False, "Event not found"
        
        # Convert event date to datetime object
        event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
        today = datetime.now().date()
        
        if event_date < today:
            return False, "Cannot register for past events"
        
        # Insert the registration
        cursor.execute('''
        INSERT INTO registrations (student_id, event_id, role_assigned, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (student_id, event_id, role_assigned, 'Pending', datetime.now()))
        
        registration_id = cursor.lastrowid
        conn.commit()
        return True, registration_id
    except Exception as e:
        print(f"Error registering volunteer: {e}")
        return False, str(e)
    finally:
        conn.close()

def get_student_registrations(student_id):
    """Get all event registrations for a student"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.id, r.status, r.role_assigned, r.created_at,
           e.id as event_id, e.name as event_name, e.date, e.location, e.points,
           e.description as event_description
    FROM registrations r
    JOIN events e ON r.event_id = e.id
    WHERE r.student_id = ?
    ORDER BY e.date
    ''', (student_id,))
    
    registrations = []
    for row in cursor.fetchall():
        description = row['event_description'] if 'event_description' in row.keys() else ''
        registrations.append({
            'id': row['id'],
            'status': row['status'],
            'role_assigned': row['role_assigned'],
            'created_at': row['created_at'],
            'event': {
                'id': row['event_id'],
                'name': row['event_name'],
                'date': row['date'],
                'location': row['location'],
                'points': row['points'],
                'description': description
            }
        })
    
    conn.close()
    return registrations

def complete_volunteer_registration(registration_id):
    """Mark a volunteer registration as completed and award points"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get the registration details
        cursor.execute('''
        SELECT r.student_id, r.event_id, r.status, e.points
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.id = ?
        ''', (registration_id,))
        
        registration = cursor.fetchone()
        
        if not registration:
            return False, "Registration not found"
        
        if registration['status'] == 'Completed':
            return False, "Registration is already marked as completed"
        
        # Update registration status
        cursor.execute('''
        UPDATE registrations
        SET status = 'Completed'
        WHERE id = ?
        ''', (registration_id,))
        
        # Award points to student
        student_id = registration['student_id']
        points_to_award = registration['points']
        
        # Get current points
        cursor.execute('SELECT total_points FROM points WHERE student_id = ?', (student_id,))
        result = cursor.fetchone()
        
        if result:
            current_points = result['total_points'] or 0
            new_total = current_points + points_to_award
            
            # Update points
            cursor.execute('''
            UPDATE points 
            SET total_points = ?, last_updated = ?
            WHERE student_id = ?
            ''', (new_total, datetime.now(), student_id))
        else:
            # Create points record if it doesn't exist
            cursor.execute('''
            INSERT INTO points (student_id, total_points, last_updated)
            VALUES (?, ?, ?)
            ''', (student_id, points_to_award, datetime.now()))
        
        conn.commit()
        return True, points_to_award
    except Exception as e:
        print(f"Error completing registration: {e}")
        return False, str(e)
    finally:
        conn.close()

def get_event_volunteers(event_id):
    """Get all volunteers registered for an event"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT r.id, r.status, r.role_assigned, r.created_at,
           s.id as student_id, s.name as student_name, s.email as student_email
    FROM registrations r
    JOIN students s ON r.student_id = s.id
    WHERE r.event_id = ?
    ORDER BY r.created_at
    ''', (event_id,))
    
    volunteers = []
    for row in cursor.fetchall():
        volunteers.append({
            'id': row['id'],
            'status': row['status'],
            'role_assigned': row['role_assigned'],
            'created_at': row['created_at'],
            'student': {
                'id': row['student_id'],
                'name': row['student_name'],
                'email': row['student_email']
            }
        })
    
    conn.close()
    return volunteers

def update_volunteer_role(registration_id, role):
    """Update the assigned role for a volunteer registration"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if registration exists
        cursor.execute('SELECT id FROM registrations WHERE id = ?', (registration_id,))
        registration = cursor.fetchone()
        
        if not registration:
            return False, "Registration not found"
        
        # Update the role
        cursor.execute('''
        UPDATE registrations
        SET role_assigned = ?
        WHERE id = ?
        ''', (role, registration_id))
        
        conn.commit()
        return True, "Role updated successfully"
    except Exception as e:
        print(f"Error updating volunteer role: {e}")
        return False, str(e)
    finally:
        conn.close()

# Add this function before the init_db() call
# Modified redeem_reward function in db.py
def redeem_reward(student_id, reward_id, notes=None):
    """Process a reward redemption by a student"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get student's available points
        cursor.execute('SELECT total_points FROM points WHERE student_id = ?', (student_id,))
        student_points = cursor.fetchone()
        
        if not student_points:
            return False, "Student points record not found"
        
        available_points = student_points['total_points'] or 0
        
        # Get reward details
        cursor.execute('SELECT points_required, name FROM rewards WHERE id = ?', (reward_id,))
        reward = cursor.fetchone()
        
        if not reward:
            return False, "Reward not found"
        
        points_required = reward['points_required']
        reward_name = reward['name']
        
        # FINAL SAFETY CHECK - Prevent negative points
        if available_points < points_required:
            conn.close()
            return False, f"Insufficient points. Need {points_required}, have {available_points}."
        
        # Process the redemption
        # 1. Create redemption record
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
        INSERT INTO redemptions (student_id, reward_id, date, created_at)
        VALUES (?, ?, ?, ?)
        ''', (student_id, reward_id, today, datetime.now()))
        
        redemption_id = cursor.lastrowid
        
        # 2. Calculate new points balance
        new_points = available_points - points_required
        
        # 3. Another safety check before updating
        if new_points < 0:
            # Roll back the transaction
            conn.rollback()
            conn.close()
            return False, "Transaction would result in negative points balance"
            
        # 4. Update points
        cursor.execute('''
        UPDATE points 
        SET total_points = ?, last_updated = ?
        WHERE student_id = ?
        ''', (new_points, datetime.now(), student_id))
        
        conn.commit()
        return True, {
            'redemption_id': redemption_id,
            'reward_name': reward_name,
            'points_used': points_required,
            'remaining_points': new_points
        }
    except Exception as e:
        print(f"Error redeeming reward: {e}")
        # Ensure we roll back the transaction on error
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()
                
# Update this function in db.py
def get_student_points_history(student_id):
    """Get a detailed history of points earned and spent by a student"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get points earned from completed volunteer activities
    cursor.execute('''
    SELECT 
        r.id, 
        e.name as activity_name, 
        r.status, 
        e.points as points_earned, 
        r.created_at as date,
        'earned' as type
    FROM registrations r
    JOIN events e ON r.event_id = e.id
    WHERE r.student_id = ? AND r.status = 'Completed'
    ''', (student_id,))
    
    earned_points = [dict(row) for row in cursor.fetchall()]
    
    # Get points spent on redemptions
    cursor.execute('''
    SELECT 
        rd.id, 
        rw.name as activity_name, 
        'Completed' as status,
        rw.points_required as points_spent, 
        rd.date,
        'spent' as type
    FROM redemptions rd
    JOIN rewards rw ON rd.reward_id = rw.id
    WHERE rd.student_id = ?
    ''', (student_id,))
    
    spent_points = [dict(row) for row in cursor.fetchall()]
    
    # Combine the results
    all_history = earned_points + spent_points
    
    # Convert all dates to datetime objects for consistent sorting
    for item in all_history:
        # Skip if date is None
        if item['date'] is None:
            item['date'] = datetime.now()  # Use current time as fallback
            continue
            
        # If it's already a datetime object, keep it as is
        if isinstance(item['date'], datetime):
            continue
            
        # For string dates, try to parse based on expected formats
        if isinstance(item['date'], str):
            try:
                # Try ISO format (YYYY-MM-DD)
                if re.match(r'^\d{4}-\d{2}-\d{2}$', item['date']):
                    item['date'] = datetime.strptime(item['date'], '%Y-%m-%d')
                # Try timestamp format from SQLite
                else:
                    # Try various formats that SQLite might return
                    formats = [
                        '%Y-%m-%d %H:%M:%S',  # Standard SQLite timestamp
                        '%Y-%m-%d %H:%M:%S.%f',  # With microseconds
                        '%Y-%m-%d',  # Just date
                    ]
                    
                    for fmt in formats:
                        try:
                            item['date'] = datetime.strptime(item['date'], fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        # If all parsing attempts failed, use current time
                        item['date'] = datetime.now()
            except Exception:
                # If any error occurs during parsing, use current time
                item['date'] = datetime.now()
    
    # Sort by date (most recent first)
    all_history.sort(key=lambda x: x['date'], reverse=True)
    
    conn.close()
    return all_history

# Add this function to db.py
def get_students_detailed():
    """Get all students with their registration details"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Joining students with points table
    cursor.execute('''
    SELECT 
        s.id, s.name, s.email, s.phone, s.created_at, 
        p.total_points
    FROM students s
    LEFT JOIN points p ON s.id = p.student_id
    ORDER BY s.name
    ''')
    
    students = []
    for row in cursor.fetchall():
        # Basic student info
        student = {
            'id': row['id'],
            'name': row['name'],
            'email': row['email'],
            'phone': row['phone'] or 'Not provided',
            'created_at': row['created_at'],
            'points': row['total_points'] or 0,
            'latest_registration': None
        }
        
        # Get latest registration info for this student
        cursor.execute('''
        SELECT 
            r.id, r.status, r.role_assigned, r.created_at,
            e.id as event_id, e.name as event_name
        FROM registrations r
        JOIN events e ON r.event_id = e.id
        WHERE r.student_id = ?
        ORDER BY r.created_at DESC
        LIMIT 1
        ''', (row['id'],))
        
        latest_reg = cursor.fetchone()
        if latest_reg:
            student['latest_registration'] = {
                'id': latest_reg['id'],
                'status': latest_reg['status'],
                'role': latest_reg['role_assigned'] or 'Not assigned',
                'created_at': latest_reg['created_at'],
                'event_id': latest_reg['event_id'],
                'event_name': latest_reg['event_name']
            }
        
        students.append(student)
    
    conn.close()
    return students

# Add this function to db.py
def adjust_student_points(student_id, points_amount, reason=None):
    """
    Manually adjust a student's points (add or subtract)
    Returns: (success, new_total_points)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if student exists
        cursor.execute('SELECT id FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()
        if not student:
            return False, "Student not found"
        
        # Get current points
        cursor.execute('SELECT total_points FROM points WHERE student_id = ?', (student_id,))
        result = cursor.fetchone()
        
        if result:
            current_points = result['total_points'] or 0
            new_total = current_points + points_amount
            
            # Ensure points don't go negative
            if new_total < 0:
                return False, "Cannot reduce points below zero"
            
            # Update points
            cursor.execute('''
            UPDATE points 
            SET total_points = ?, last_updated = ?
            WHERE student_id = ?
            ''', (new_total, datetime.now(), student_id))
        else:
            # Create points record if it doesn't exist
            if points_amount < 0:
                return False, "Cannot reduce points below zero"
                
            cursor.execute('''
            INSERT INTO points (student_id, total_points, last_updated)
            VALUES (?, ?, ?)
            ''', (student_id, points_amount, datetime.now()))
            new_total = points_amount
        
        # Log the points adjustment (if you want to track history)
        # This is optional but recommended for audit purposes
        if reason:
            cursor.execute('''
            INSERT INTO points_adjustments (student_id, points_amount, reason, adjusted_at)
            VALUES (?, ?, ?, ?)
            ''', (student_id, points_amount, reason, datetime.now()))
        
        conn.commit()
        return True, new_total
    except Exception as e:
        print(f"Error adjusting points: {e}")
        return False, str(e)
    finally:
        conn.close()

# Add this function to db.py near the create_user function
def update_student(student_id, name, email, phone=None, password=None, points=None):
    """Update student information and points"""
    # First validate inputs
    name_valid, name_msg = is_valid_name(name)
    if not name_valid:
        return False, name_msg
        
    if not is_valid_email(email):
        return False, "Invalid email format"
        
    if phone:
        phone_valid, phone_msg = is_valid_phone(phone)
        if not phone_valid:
            return False, phone_msg
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if student exists
        cursor.execute('SELECT id FROM students WHERE id = ?', (student_id,))
        student = cursor.fetchone()
        if not student:
            return False, "Student not found"
        
        # Check if email is already used by another student
        cursor.execute('SELECT id FROM students WHERE email = ? AND id != ?', (email, student_id))
        existing_email = cursor.fetchone()
        if existing_email:
            return False, "Email already in use by another account"
        
        # Update student information
        if password:
            # Hash the new password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('''
            UPDATE students 
            SET name = ?, email = ?, phone = ?, password = ?
            WHERE id = ?
            ''', (name, email, phone, hashed_password, student_id))
        else:
            # Update without changing password
            cursor.execute('''
            UPDATE students 
            SET name = ?, email = ?, phone = ?
            WHERE id = ?
            ''', (name, email, phone, student_id))
        
        # Update points if provided
        if points is not None:
            # Convert to integer
            try:
                points = int(points)
                if points < 0:
                    points = 0
            except ValueError:
                points = 0
                
            # Check if points record exists
            cursor.execute('SELECT student_id FROM points WHERE student_id = ?', (student_id,))
            points_record = cursor.fetchone()
            
            if points_record:
                cursor.execute('''
                UPDATE points 
                SET total_points = ?, last_updated = ?
                WHERE student_id = ?
                ''', (points, datetime.now(), student_id))
            else:
                cursor.execute('''
                INSERT INTO points (student_id, total_points, last_updated)
                VALUES (?, ?, ?)
                ''', (student_id, points, datetime.now()))
        
        conn.commit()
        return True, "Student updated successfully"
    except Exception as e:
        print(f"Error updating student: {e}")
        return False, str(e)
    finally:
        conn.close()

# Initialize the database when this module is imported
init_db()