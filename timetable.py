from sqlalchemy import Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base
from main import db
import enum

# Define an enumeration for the days of the week
class DayEnum(enum.Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"

class Timetable(db.Model):
    __tablename__ = 'timetable'  # Specify the table name

    id = db.Column(Integer, primary_key=True)
    day = db.Column(Enum(DayEnum), nullable=False)  # Using Enum for day
    subject = db.Column(String(100), nullable=False)  # Limit length for subject
    lecture = db.Column(String(100), nullable=False)  # Limit length for lecture
    room = db.Column(String(50), nullable=False)  # Limit length for room
    time = db.Column(String(50), nullable=False)  # Limit length for time
    batch = db.Column(String(50), nullable=False)  # New field for batch

    def __repr__(self):
        return f'<Timetable {self.day.value}, {self.lecture}>'

# Create all tables
db.create_all()

