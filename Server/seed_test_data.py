import re
from datetime import time
from app.core.database import SessionLocal, init_db
from app import models
from app.core.security import get_password_hash

# --- DATA CONSTANTS ---

FACULTY_EMAILS = {
    # CSE A
    "Prof. Anderson": "anderson@ABC.com",
    "Prof. Baker": "baker@ABC.com",
    "Prof. Clark": "clark@ABC.com",
    "Prof. Davis": "davis@ABC.com",
    "Prof. Evans": "evans@ABC.com",
    "Prof. Foster": "foster@ABC.com",
    "Prof. Green": "green@ABC.com",
    "Prof. Harris": "harris@ABC.com",
    # CSE B
    "Prof. Jones": "jones@ABC.com",
    "Prof. King": "king@ABC.com",
    "Prof. Lewis": "lewis@ABC.com",
    "Prof. Martin": "martin@ABC.com",
    "Prof. Nelson": "nelson@ABC.com",
    "Prof. Parker": "parker@ABC.com",
    "Prof. Roberts": "roberts@ABC.com",
    "Prof. Scott": "scott@ABC.com",
    # CSE C
    "Prof. Adams": "adams@ABC.com",
    "Prof. Hill": "hill@ABC.com",
    "Prof. Stone": "stone@ABC.com",
    "Prof. Turner": "turner@ABC.com",
    "Prof. Vance": "vance@ABC.com",
    "Prof. White": "white@ABC.com",
    "Prof. Wright": "wright@ABC.com",
    "Prof. Young": "young@ABC.com",
}

SCHEDULE_DATA = [
    {
        "class_info": {"class name": "CSE A", "department": "CSE", "classroom": "LH44"},
        "timetable": {
            "Monday": {
                "08:00-08:45": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Clark" },
                "08:45-09:30": { "subject": "Foundations of AI (UCS3461)", "faculty": "Prof. Davis" },
                "09:50-10:35": { "subject": "Internet Programming (UCS3462)", "faculty": "Prof. Evans" },
                "10:35-11:20": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. Foster" },
                "12:20-01:05": { "subject": "Foundations of AI (UCS3461)", "faculty": "Prof. Davis" },
                "01:05-01:50": { "subject": "Database Laboratory (UCS3411)", "faculty": "Prof. Foster" },
                "02:10-02:55": { "subject": "Database Laboratory (UCS3411)", "faculty": "Prof. Foster" },
                "02:55-03:40": { "subject": "Database Laboratory (UCS3411)", "faculty": "Prof. Foster" }
            },
            "Tuesday": {
                "08:00-08:45": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Anderson" },
                "08:45-09:30": { "subject": "Indian Constitution (UGA3476)", "faculty": "Prof. Baker" },
                "09:50-10:35": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Anderson" },
                "10:35-11:20": { "subject": "Internet Programming (UCS3462)", "faculty": "Prof. Evans" },
                "12:20-01:05": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. Foster" },
                "01:05-01:50": { "subject": "Tutorial", "faculty": None },
                "02:10-02:55": { "subject": "Self Learning", "faculty": None },
                "02:55-03:40": { "subject": "Library", "faculty": None }
            },
            "Wednesday": {
                "08:00-08:45": { "subject": "Indian Society and Empowerment (UPA3441)", "faculty": "Prof. Harris" },
                "08:45-09:30": { "subject": "Skill Development Lab (UCSV305)", "faculty": "Prof. Green" },
                "09:50-10:35": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Clark" },
                "10:35-11:20": { "subject": "Industry Oriented Course (UCSV304)", "faculty": "Prof. Green" },
                "12:20-01:05": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Anderson" },
                "01:05-01:50": { "subject": "Competitive Programming Lab (UCS3412)", "faculty": "Prof. Clark" },
                "02:10-02:55": { "subject": "Competitive Programming Lab (UCS3412)", "faculty": "Prof. Clark" },
                "02:55-03:40": { "subject": "Competitive Programming Lab (UCS3412)", "faculty": "Prof. Clark" }
            },
            "Thursday": {
                "08:00-08:45": { "subject": "AI Laboratory (UCS3461)", "faculty": "Prof. Davis" },
                "08:45-09:30": { "subject": "AI Laboratory (UCS3461)", "faculty": "Prof. Davis" },
                "09:50-10:35": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Anderson" },
                "10:35-11:20": { "subject": "AI Laboratory (UCS3461)", "faculty": "Prof. Davis" },
                "12:20-01:05": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Clark" },
                "01:05-01:50": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Clark" },
                "02:10-02:55": { "subject": "Beyond Syllabus", "faculty": None },
                "02:55-03:40": { "subject": "Indian Constitution (UGA3476)", "faculty": "Prof. Baker" }
            },
            "Friday": {
                "08:00-08:45": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. Foster" },
                "08:45-09:30": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. Foster" },
                "09:50-10:35": { "subject": "Internet Programming (UCS3462)", "faculty": "Prof. Evans" },
                "10:35-11:20": { "subject": "Foundations of AI (UCS3461)", "faculty": "Prof. Davis" },
                "12:20-01:05": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Anderson" },
                "01:05-01:50": { "subject": "Internet Programming Lab (UCS3462)", "faculty": "Prof. Evans" },
                "02:10-02:55": { "subject": "Internet Programming Lab (UCS3462)", "faculty": "Prof. Evans" },
                "02:55-03:40": { "subject": "Internet Programming Lab (UCS3462)", "faculty": "Prof. Evans" }
            }
        }
    },
    {
        "class_info": {"class name": "CSE B", "department": "CSE", "classroom": "LH50"},
        "timetable": {
            "Monday": {
                "08:00-08:45": { "subject": "Database Laboratory (UCS3411)", "faculty": "Prof. Martin" },
                "08:45-09:30": { "subject": "Database Laboratory (UCS3411)", "faculty": "Prof. Martin" },
                "09:50-10:35": { "subject": "Database Laboratory (UCS3411)", "faculty": "Prof. Martin" },
                "10:35-11:20": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Jones" },
                "12:20-01:05": { "subject": "Foundations of AI (UCS3461)", "faculty": "Prof. Nelson" },
                "01:05-01:50": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Lewis" },
                "02:10-02:55": { "subject": "Self Learning", "faculty": None },
                "02:55-03:40": { "subject": "Library", "faculty": None }
            },
            "Tuesday": {
                "08:00-08:45": { "subject": "AI Laboratory (UCS3461)", "faculty": "Prof. Nelson" },
                "08:45-09:30": { "subject": "AI Laboratory (UCS3461)", "faculty": "Prof. Nelson" },
                "09:50-10:35": { "subject": "AI Laboratory (UCS3461)", "faculty": "Prof. Nelson" },
                "10:35-11:20": { "subject": "Internet Programming (UCS3462)", "faculty": "Prof. Parker" },
                "12:20-01:05": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Jones" },
                "01:05-01:50": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. Martin" },
                "02:10-02:55": { "subject": "Foundations of AI (UCS3461)", "faculty": "Prof. Nelson" },
                "02:55-03:40": { "subject": "Beyond Syllabus", "faculty": None }
            },
            "Wednesday": {
                "08:00-08:45": { "subject": "Skill Development Lab (UCSV305)", "faculty": "Prof. Roberts" },
                "08:45-09:30": { "subject": "Skill Development Lab (UCSV305)", "faculty": "Prof. Roberts" },
                "09:50-10:35": { "subject": "Indian Society and Empowerment (UPA3441)", "faculty": "Prof. Scott" },
                "10:35-11:20": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Lewis" },
                "12:20-01:05": { "subject": "Industry Oriented Course (UCSV304)", "faculty": "Prof. Roberts" },
                "01:05-01:50": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Jones" },
                "02:10-02:55": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Lewis" },
                "02:55-03:40": { "subject": "Tutorial", "faculty": None }
            },
            "Thursday": {
                "08:00-08:45": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. Martin" },
                "08:45-09:30": { "subject": "Indian Constitution (UGA3476)", "faculty": "Prof. King" },
                "09:50-10:35": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Lewis" },
                "10:35-11:20": { "subject": "Internet Programming (UCS3462)", "faculty": "Prof. Parker" },
                "12:20-01:05": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. Martin" },
                "01:05-01:50": { "subject": "Internet Programming Lab (UCS3462)", "faculty": "Prof. Parker" },
                "02:10-02:55": { "subject": "Internet Programming Lab (UCS3462)", "faculty": "Prof. Parker" },
                "02:55-03:40": { "subject": "Internet Programming Lab (UCS3462)", "faculty": "Prof. Parker" }
            },
            "Friday": {
                "08:00-08:45": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Jones" },
                "08:45-09:30": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Jones" },
                "09:50-10:35": { "subject": "Internet Programming (UCS3462)", "faculty": "Prof. Parker" },
                "10:35-11:20": { "subject": "Foundations of AI (UCS3461)", "faculty": "Prof. Nelson" },
                "12:20-01:05": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. Martin" },
                "01:05-01:50": { "subject": "Competitive Programming Lab (UCS3412)", "faculty": "Prof. Lewis" },
                "02:10-02:55": { "subject": "Competitive Programming Lab (UCS3412)", "faculty": "Prof. Lewis" },
                "02:55-03:40": { "subject": "Tutorial", "faculty": None }
            }
        }
    },
    {
        "class_info": {"class name": "CSE C", "department": "CSE", "classroom": "LH51"},
        "timetable": {
            "Monday": {
                "08:00-08:45": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Turner" },
                "08:45-09:30": { "subject": "Foundations of AI (UCS3461)", "faculty": "Prof. Vance" },
                "09:50-10:35": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. White" },
                "10:35-11:20": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Wright" },
                "12:20-01:05": { "subject": "Internet Programming (UCS3462)", "faculty": "Prof. Young" },
                "01:05-01:50": { "subject": "AI Laboratory (UCS3461)", "faculty": "Prof. Vance" },
                "02:10-02:55": { "subject": "AI Laboratory (UCS3461)", "faculty": "Prof. Vance" },
                "02:55-03:40": { "subject": "AI Laboratory (UCS3461)", "faculty": "Prof. Vance" }
            },
            "Tuesday": {
                "08:00-08:45": { "subject": "Indian Constitution (UGA3476)", "faculty": "Prof. Stone" },
                "08:45-09:30": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Wright" },
                "09:50-10:35": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Turner" },
                "10:35-11:20": { "subject": "Foundations of AI (UCS3461)", "faculty": "Prof. Vance" },
                "12:20-01:05": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. White" },
                "01:05-01:50": { "subject": "Skill Development Lab (UCSV305)", "faculty": "Prof. Hill" },
                "02:10-02:55": { "subject": "Skill Development Lab (UCSV305)", "faculty": "Prof. Hill" },
                "02:55-03:40": { "subject": "Skill Development Lab (UCSV305)", "faculty": "Prof. Hill" }
            },
            "Wednesday": {
                "08:00-08:45": { "subject": "Indian Society and Empowerment (UPA3441)", "faculty": "Prof. Adams" },
                "08:45-09:30": { "subject": "Internet Programming (UCS3462)", "faculty": "Prof. Young" },
                "09:50-10:35": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. White" },
                "10:35-11:20": { "subject": "Industry Oriented Course (UCSV304)", "faculty": "Prof. Hill" },
                "12:20-01:05": { "subject": "Internet Programming Lab (UCS3462)", "faculty": "Prof. Young" },
                "01:05-01:50": { "subject": "Internet Programming Lab (UCS3462)", "faculty": "Prof. Young" },
                "02:10-02:55": { "subject": "Internet Programming Lab (UCS3462)", "faculty": "Prof. Young" },
                "02:55-03:40": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Turner" }
            },
            "Thursday": {
                "08:00-08:45": { "subject": "Database Management Systems (UCS3402)", "faculty": "Prof. White" },
                "08:45-09:30": { "subject": "Database Laboratory (UCS3411)", "faculty": "Prof. White" },
                "09:50-10:35": { "subject": "Database Laboratory (UCS3411)", "faculty": "Prof. White" },
                "10:35-11:20": { "subject": "Database Laboratory (UCS3411)", "faculty": "Prof. White" },
                "12:20-01:05": { "subject": "Indian Constitution (UGA3476)", "faculty": "Prof. Stone" },
                "01:05-01:50": { "subject": "Probability Theory and Statistics (UMA3476)", "faculty": "Prof. Turner" },
                "02:10-02:55": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Wright" },
                "02:55-03:40": { "subject": "Tutorial", "faculty": None }
            },
            "Friday": {
                "08:00-08:45": { "subject": "Competitive Programming Lab (UCS3412)", "faculty": "Prof. Wright" },
                "08:45-09:30": { "subject": "Competitive Programming Lab (UCS3412)", "faculty": "Prof. Wright" },
                "09:50-10:35": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Wright" },
                "10:35-11:20": { "subject": "Foundations of AI (UCS3461)", "faculty": "Prof. Vance" },
                "12:20-01:05": { "subject": "Internet Programming (UCS3462)", "faculty": "Prof. Young" },
                "01:05-01:50": { "subject": "Design And Analysis of Algorithms (UCS3401)", "faculty": "Prof. Wright" },
                "02:10-02:55": { "subject": "Self Learning", "faculty": None },
                "02:55-03:40": { "subject": "Library", "faculty": None }
            }
        }
    }
]

STUDENTS_DATA = {
    "CSE A": [
        {"id": 9283746510001, "digital_id": 3849101, "name": "Alice Smith", "email": "alicesmith@ABC.com"},
        {"id": 9283746510002, "digital_id": 3849102, "name": "Bob Johnson", "email": "bobjohnson@ABC.com"},
        {"id": 9283746510003, "digital_id": 3849103, "name": "Charlie Brown", "email": "charliebrown@ABC.com"},
        {"id": 9283746510004, "digital_id": 3849104, "name": "David Wilson", "email": "davidwilson@ABC.com"},
        {"id": 9283746510005, "digital_id": 3849105, "name": "Eve Davis", "email": "evedavis@ABC.com"},
        {"id": 9283746510006, "digital_id": 3849106, "name": "Frank Miller", "email": "frankmiller@ABC.com"},
        {"id": 9283746510007, "digital_id": 3849107, "name": "Grace Lee", "email": "gracelee@ABC.com"},
        {"id": 9283746510008, "digital_id": 3849108, "name": "Henry Taylor", "email": "henrytaylor@ABC.com"},
        {"id": 9283746510009, "digital_id": 3849109, "name": "Ivy Clark", "email": "ivyclark@ABC.com"},
        {"id": 9283746510010, "digital_id": 3849110, "name": "Jack White", "email": "jackwhite@ABC.com"}
    ],
    "CSE B": [
        {"id": 9283746510011, "digital_id": 3849111, "name": "Liam Harris", "email": "liamharris@ABC.com"},
        {"id": 9283746510012, "digital_id": 3849112, "name": "Mia Martin", "email": "miamartin@ABC.com"},
        {"id": 9283746510013, "digital_id": 3849113, "name": "Noah Thompson", "email": "noahthompson@ABC.com"},
        {"id": 9283746510014, "digital_id": 3849114, "name": "Olivia Garcia", "email": "oliviagarcia@ABC.com"},
        {"id": 9283746510015, "digital_id": 3849115, "name": "Peter Martinez", "email": "petermartinez@ABC.com"},
        {"id": 9283746510016, "digital_id": 3849116, "name": "Quinn Robinson", "email": "quinnrobinson@ABC.com"},
        {"id": 9283746510017, "digital_id": 3849117, "name": "Ryan Rodriguez", "email": "ryanrodriguez@ABC.com"},
        {"id": 9283746510018, "digital_id": 3849118, "name": "Sophia Lewis", "email": "sophialewis@ABC.com"},
        {"id": 9283746510019, "digital_id": 3849119, "name": "Thomas Walker", "email": "thomaswalker@ABC.com"},
        {"id": 9283746510020, "digital_id": 3849120, "name": "Ursula Hall", "email": "ursulahall@ABC.com"}
    ],
    "CSE C": [
        {"id": 9283746510021, "digital_id": 3849121, "name": "Victor Allen", "email": "victorallen@ABC.com"},
        {"id": 9283746510022, "digital_id": 3849122, "name": "Wendy Young", "email": "wendyyoung@ABC.com"},
        {"id": 9283746510023, "digital_id": 3849123, "name": "Xavier King", "email": "xavierking@ABC.com"},
        {"id": 9283746510024, "digital_id": 3849124, "name": "Yara Wright", "email": "yarawright@ABC.com"},
        {"id": 9283746510025, "digital_id": 3849125, "name": "Zachary Scott", "email": "zacharyscott@ABC.com"},
        {"id": 9283746510026, "digital_id": 3849126, "name": "Amber Green", "email": "ambergreen@ABC.com"},
        {"id": 9283746510027, "digital_id": 3849127, "name": "Brian Baker", "email": "brianbaker@ABC.com"},
        {"id": 9283746510028, "digital_id": 3849128, "name": "Chloe Adams", "email": "chloeadams@ABC.com"},
        {"id": 9283746510029, "digital_id": 3849129, "name": "Dylan Nelson", "email": "dylannelson@ABC.com"},
        {"id": 9283746510030, "digital_id": 3849130, "name": "Emma Carter", "email": "emmacarter@ABC.com"}
    ]
}

def parse_course_string(course_str):
    """
    Parses 'Subject Name (CODE)' -> ('Subject Name', 'CODE')
    If no code is found, returns (course_str, course_str_slug)
    """
    match = re.search(r"(.*)\s\((.*)\)", course_str)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return course_str.strip(), course_str.strip().upper().replace(" ", "_")

def get_day_index(day_name):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days.index(day_name)

def get_slot_number(time_range):
    """
    Map time range string starting time to slot number.
    8:00 -> 1, 8:45 -> 2, 9:50 -> 3, 10:35 -> 4, 12:20 -> 5, 1:05 -> 6, 2:10 -> 7, 2:55 -> 8
    """
    start_time = time_range.split("-")[0].strip()
    h, m = map(int, start_time.split(":"))
    if h == 8 and m == 0: return 1
    if h == 8 and m == 45: return 2
    if h == 9 and m == 50: return 3
    if h == 10 and m == 35: return 4
    if h == 12 and m == 20: return 5
    if h == 1 and m == 5: return 6 # Converted to 13:05 internally? No, input is 01:05
    if h == 13 and m == 5: return 6
    if h == 2 and m == 10: return 7
    if h == 14 and m == 10: return 7
    if h == 2 and m == 55: return 8
    if h == 14 and m == 55: return 8
    # Handle AM/PM logic if needed, but the provided strings are 01:05 etc.
    # Let's handle 12-hr format by checking values
    if h == 1: return 6
    if h == 2: return 7 # ambiguous if 02:55 vs 02:10,check m
    
    return 0

SLOT_MAPPING = {
    "08:00": 1, "08:45": 2, "09:50": 3, "10:35": 4, 
    "12:20": 5, "01:05": 6, "02:10": 7, "02:55": 8
}

def seed_data():
    init_db()
    db = SessionLocal()
    print("--- Seeding Sophisticated Data ---")

    # 1. Bell Schedule
    if db.query(models.BellSchedule).count() == 0:
        print("Seeding Bell Schedule...")
        # Defined slots based on input
        # 1: 08:00-08:45, 2: 08:45-09:30, 3: 09:50-10:35, 4: 10:35-11:20
        # 5: 12:20-01:05, 6: 01:05-01:50, 7: 02:10-02:55, 8: 02:55-03:40
        schedules = [
            (1, time(8, 0), time(8, 45)),
            (2, time(8, 45), time(9, 30)),
            (3, time(9, 50), time(10, 35)),
            (4, time(10, 35), time(11, 20)),
            (5, time(12, 20), time(13, 5)),
            (6, time(13, 5), time(13, 50)),
            (7, time(14, 10), time(14, 55)),
            (8, time(14, 55), time(15, 40))
        ]
        for slot, start, end in schedules:
            db.add(models.BellSchedule(slot_number=slot, start_time=start, end_time=end))
        db.commit()

    # 2. Setup Admin
    admin = db.query(models.Admin).filter_by(username="admin").first()
    if not admin:
        admin = models.Admin(username="admin", password_hash=get_password_hash("pass"))
        db.add(admin)
        print("Created Admin")
    else:
        # Enforce password 'pass'
        admin.password_hash = get_password_hash("pass")
        db.add(admin)
        print("Updated Admin password to 'pass'")
    
    db.commit()

    # 3. Setup Professors
    print("Seeding Professors...")
    prof_email_to_id = {}
    prof_id_counter = 100001
    
    for prof_name, email in FACULTY_EMAILS.items():
        prof = db.query(models.Professor).filter_by(email=email).first()
        if not prof:
            prof = models.Professor(
                id=prof_id_counter,
                name=prof_name,
                email=email,
                department="CSE",
                password_hash=get_password_hash("pass")
            )
            db.add(prof)
            db.commit() # Commit to get ID
            prof_id_counter += 1
        prof_email_to_id[email] = prof.id
    
    # 4. Setup ClassGroups, Courses, Assignments, TimeTables
    print("Seeding Classes and TimeTables...")
    
    for class_data in SCHEDULE_DATA:
        c_info = class_data["class_info"]
        c_name = c_info["class name"].replace("class ", "") # Handle potential "class CSE A" vs "CSE A"
        if "section" in c_info: c_name = c_info["section"] # Handle "section": "CSE_B"
        c_name = c_name.replace("_", " ") # CSE_A -> CSE A
        
        classroom = c_info["classroom"]
        
        # Create ClassGroup
        cg = db.query(models.ClassGroup).filter_by(name=c_name).first()
        if not cg:
            cg = models.ClassGroup(name=c_name, department=c_info.get("department", "CSE"), year=2)
            db.add(cg)
            db.commit()
            print(f"Created ClassGroup: {c_name}")
            
        # Process TimeTable
        tt_data = class_data["timetable"]
        for day_name, slots in tt_data.items():
            day_idx = get_day_index(day_name)
            
            for time_range, details in slots.items():
                subject_str = details["subject"]
                faculty_name = details["faculty"]
                
                # Determine Slot
                start_str = time_range.split("-")[0].strip()
                slot_num = SLOT_MAPPING.get(start_str)
                if not slot_num:
                    print(f"Warning: Could not map time {start_str}, skipping.")
                    continue
                
                # Parse Course
                course_name, course_code = parse_course_string(subject_str)
                
                # Create Course if not exists
                course = db.query(models.Course).filter_by(code=course_code).first()
                if not course:
                    course = models.Course(code=course_code, name=course_name, department="CSE")
                    db.add(course)
                    db.commit()
                    
                # Identify Professor
                prof_id = None
                if faculty_name:
                     # Try to find email
                    prof_email = FACULTY_EMAILS.get(faculty_name)
                    if prof_email:
                        prof_id = prof_email_to_id.get(prof_email)
                
                # Create or Get TeachingAssignment
                # Logic: Check if assignment exists for (Course + Class + Prof). 
                # Note: Special courses like "Library" might have multiple slots, same assignment.
                # If Prof is None (Library), we still create an assignment with null professor? 
                # Model allows nullable professor in DB? Let's check model...
                # teaching_assignments.professor_id is ForeignKey("professors.id"). 
                # SQLAlchemy usually allows nullable ForeignKeys unless nullable=False.
                # In models/academic.py: professor_id = Column(Integer, ForeignKey("professors.id")) -> nullable by default.
                
                assignment = db.query(models.TeachingAssignment).filter_by(
                    course_id=course.id,
                    class_group_id=cg.id,
                    professor_id=prof_id
                ).first()
                
                if not assignment:
                    assignment = models.TeachingAssignment(
                        course_id=course.id,
                        class_group_id=cg.id,
                        professor_id=prof_id,
                        default_classroom=classroom
                    )
                    db.add(assignment)
                    db.commit()
                
                # Create TimeTable Entry
                tt_entry = db.query(models.TimeTable).filter_by(
                    assignment_id=assignment.id,
                    day_of_week=day_idx,
                    hour_slot=slot_num
                ).first()
                
                if not tt_entry:
                    tt_entry = models.TimeTable(
                        assignment_id=assignment.id,
                        day_of_week=day_idx,
                        hour_slot=slot_num
                    )
                    db.add(tt_entry)
        
        db.commit()

    # 5. Setup Students
    print("Seeding Students...")
    for class_name_key, students_list in STUDENTS_DATA.items():
        # Map "CSE A" key to DB ClassGroup
        real_class_name = class_name_key # "CSE A"
        cg = db.query(models.ClassGroup).filter_by(name=real_class_name).first()
        if not cg:
            print(f"Error: ClassGroup {real_class_name} not found for students. Skipping.")
            continue
            
        for s_data in students_list:
            student = db.query(models.Student).filter_by(email=s_data["email"]).first()
            if not student:
                student = models.Student(
                    id=s_data["id"],
                    digital_id=s_data["digital_id"],
                    name=s_data["name"],
                    email=s_data["email"],
                    password_hash=get_password_hash("pass"),
                    department="CSE",
                    year=2,
                    class_group_id=cg.id
                )
                db.add(student)
        db.commit()

    db.close()
    print("--- Seeding Complete ---")

if __name__ == "__main__":
    seed_data()