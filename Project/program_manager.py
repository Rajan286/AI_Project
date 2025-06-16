# program_manager.py
import json
import os

PROGRAMS_FILE = "programs.json"

# Load existing or default program data
def load_programs():
    if not os.path.exists(PROGRAMS_FILE):
        return {
            "Wirtschaftsinformatik B.Sc.": {"max_credits": 180, "start_semester": "WS"},
            "Informatik B.Sc.": {"max_credits": 180, "start_semester": "WS"},
            "Bauingeneurwesen B.Sc": {"max_credits": 210, "start_semester": "SS"},
            "Architektur B.A.": {"max_credits": 240, "start_semester": "WS"}
        }
    with open(PROGRAMS_FILE, 'r') as f:
        return json.load(f)

# Save program data to file
def save_programs(programs):
    with open(PROGRAMS_FILE, 'w') as f:
        json.dump(programs, f, indent=2)

# Add a new study program
def add_program(name, max_credits, start_semester):
    programs = load_programs()
    if name in programs:
        raise ValueError("Study program already exists.")
    programs[name] = {
        "max_credits": max_credits,
        "start_semester": start_semester
    }
    save_programs(programs)

# Validate student credits against allowed max
# Returns a list of (program, cp, max_cp) tuples for invalid ones
def validate_student_credits(study_programs, credits):
    programs = load_programs()
    invalid = []
    for prog, cp in zip(study_programs, credits):
        if prog in programs:
            if cp > programs[prog]["max_credits"]:
                invalid.append((prog, cp, programs[prog]["max_credits"]))
    return invalid

# Identify programs that do not exist in the database
def find_unknown_programs(study_programs):
    programs = load_programs()
    return [prog for prog in study_programs if prog not in programs]
