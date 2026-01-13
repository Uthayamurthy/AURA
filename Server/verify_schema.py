
from app.schemas.academic import TeachingAssignment
from app.schemas.user import Professor

def verify():
    prof_data = {"id": 123, "name": "Dr. Verification", "email": "verify@aura.com"}
    prof = Professor(**prof_data)
    
    assign_data = {
        "id": 1,
        "course_id": 10,
        "professor_id": 123,
        "class_group_id": 5,
        "professor": prof
    }
    
    assignment = TeachingAssignment(**assign_data)
    print("Serialization Successful!")
    print(assignment.model_dump())
    
    if assignment.professor and assignment.professor.name == "Dr. Verification":
        print("Professor field is present and correct.")
    else:
        print("Professor field missing or incorrect!")

if __name__ == "__main__":
    verify()
