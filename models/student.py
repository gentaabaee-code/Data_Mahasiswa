"""
models/student.py
─────────────────────────────────────────────────────────────────────────────
Student data models demonstrating core OOP principles:
  • Encapsulation  – private attributes accessed via @property / setters
  • Inheritance    – Student extends Person
  • Polymorphism   – get_info() overridden in the subclass
  • Abstraction    – internal state hidden; only a clean public API is exposed
─────────────────────────────────────────────────────────────────────────────
"""

import random
from datetime import date, datetime, timezone


DEFAULT_EDUCATION_LEVELS: tuple[str, ...] = ("D3", "D4", "S1", "S2", "S3")


def _parse_birth_date(value: str) -> date:
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError as exc:
        raise ValueError("Birth date must use the YYYY-MM-DD format.") from exc


def _calculate_age_from_birth_date(value: str) -> int:
    birth_date = _parse_birth_date(value)
    today = datetime.now(timezone.utc).date()

    if birth_date > today:
        raise ValueError("Birth date cannot be in the future.")

    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if not (0 < age < 150):
        raise ValueError("Birth date must produce a valid age.")
    return age


def generate_default_student_profile(seed_value: str) -> tuple[str, str]:
    rng = random.Random(str(seed_value))
    year = rng.randint(2000, 2005)
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}", rng.choice(DEFAULT_EDUCATION_LEVELS)


# ═════════════════════════════════════════════════════════════════════════════
#  BASE CLASS – Person
# ═════════════════════════════════════════════════════════════════════════════

class Person:
    """
    Represents a generic person with basic personal attributes.

    Encapsulation is applied by prefixing every instance variable with '_'.
    External code should only access/mutate values through the declared
    @property / setter pairs.
    """

    def __init__(self, name: str, age: int, email: str) -> None:
        self._name: str = name
        self._age: int = age
        self._email: str = email
        # Stored as ISO-8601 string for easy JSON serialisation
        self._created_at: str = datetime.now(timezone.utc).isoformat()

    # ── name ──────────────────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Name cannot be empty.")
        self._name = value.strip()

    # ── age ───────────────────────────────────────────────────────────────
    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int) -> None:
        value = int(value)
        if not (0 < value < 150):
            raise ValueError("Age must be a positive integer less than 150.")
        self._age = value

    # ── email ─────────────────────────────────────────────────────────────
    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        self._email = value.strip()

    # ── created_at (read-only) ─────────────────────────────────────────────
    @property
    def created_at(self) -> str:
        return self._created_at

    # ── Polymorphic method ─────────────────────────────────────────────────
    def get_info(self) -> str:
        """Return a human-readable summary. Overridden by sub-classes."""
        return f"Person: {self._name} | Age: {self._age}"

    # ── Serialisation ─────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        """Serialize shared Person attributes to a plain dictionary."""
        return {
            "name":       self._name,
            "age":        self._age,
            "email":      self._email,
            "created_at": self._created_at,
        }

    def __repr__(self) -> str:
        return f"Person(name={self._name!r}, age={self._age})"


# ═════════════════════════════════════════════════════════════════════════════
#  SUB CLASS – Student  (Inheritance + Polymorphism)
# ═════════════════════════════════════════════════════════════════════════════

class Student(Person):
    """
    Represents a university student.

    Inherits common attributes from Person and adds academic-specific ones.
    Polymorphism: get_info() is overridden to provide richer output.
    """

    # Class-level constant – GPA thresholds mapped to letter grades
    _GPA_GRADE_MAP: list[tuple[float, str]] = [
        (3.7, "A"),  (3.3, "A-"), (3.0, "B+"), (2.7, "B"),
        (2.3, "B-"), (2.0, "C+"), (1.7, "C"),  (1.3, "C-"),
        (1.0, "D+"), (0.7, "D"),  (0.0, "D-"),
    ]

    def __init__(
        self,
        student_id: str,
        name: str,
        age: int | None,
        email: str,
        phone: str,
        major: str,
        gpa: float,
        semester: int | None = None,
        birth_date: str | None = None,
        education_level: str | None = None,
    ) -> None:
        resolved_age: int | None = None
        if birth_date is not None and str(birth_date).strip():
            resolved_age = _calculate_age_from_birth_date(birth_date)
        elif age is not None and str(age).strip() != "":
            resolved_age = int(age)

        if resolved_age is None:
            raise ValueError("Student requires either an age or a birth date.")

        super().__init__(name, resolved_age, email)       # Invoke parent __init__
        self._student_id: str   = student_id
        self._phone: str        = phone
        self._major: str        = major
        self._gpa: float        = round(float(gpa), 2)
        self._semester: int | None = None
        self._birth_date: str | None = None
        self._education_level: str | None = None
        self.semester = semester
        self.birth_date = birth_date
        self.education_level = education_level

    # ── student_id (read-only after creation) ─────────────────────────────
    @property
    def student_id(self) -> str:
        return self._student_id

    # ── phone ─────────────────────────────────────────────────────────────
    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value: str) -> None:
        self._phone = value.strip()

    # ── major ─────────────────────────────────────────────────────────────
    @property
    def major(self) -> str:
        return self._major

    @major.setter
    def major(self, value: str) -> None:
        self._major = value.strip()

    # ── gpa ───────────────────────────────────────────────────────────────
    @property
    def gpa(self) -> float:
        return self._gpa

    @gpa.setter
    def gpa(self, value: float) -> None:
        value = round(float(value), 2)
        if not (0.0 <= value <= 4.0):
            raise ValueError("GPA must be between 0.0 and 4.0.")
        self._gpa = value

    # ── semester ──────────────────────────────────────────────────────────
    @property
    def semester(self) -> int | None:
        return self._semester

    @semester.setter
    def semester(self, value: int | None) -> None:
        if value is None or str(value).strip() == "":
            self._semester = None
            return

        semester = int(value)
        if not (1 <= semester <= 14):
            raise ValueError("Semester must be between 1 and 14.")
        self._semester = semester

    # ── birth_date ────────────────────────────────────────────────────────
    @property
    def birth_date(self) -> str | None:
        return self._birth_date

    @birth_date.setter
    def birth_date(self, value: str | None) -> None:
        if value is None or not str(value).strip():
            self._birth_date = None
            return

        normalized = _parse_birth_date(value).isoformat()
        Person.age.fset(self, _calculate_age_from_birth_date(normalized))
        self._birth_date = normalized

    # ── education_level ───────────────────────────────────────────────────
    @property
    def education_level(self) -> str | None:
        return self._education_level

    @education_level.setter
    def education_level(self, value: str | None) -> None:
        if value is None or not str(value).strip():
            self._education_level = None
            return

        normalized = str(value).strip().upper()
        if normalized not in DEFAULT_EDUCATION_LEVELS:
            raise ValueError(
                "Education level must be one of D3, D4, S1, S2, or S3."
            )
        self._education_level = normalized

    # ── Computed / derived properties ─────────────────────────────────────
    def get_grade_letter(self) -> str:
        """Map GPA to a letter grade using the class-level threshold table."""
        for threshold, letter in self._GPA_GRADE_MAP:
            if self._gpa >= threshold:
                return letter
        return "F"

    def get_status(self) -> str:
        """Return academic standing based on current GPA."""
        if self._gpa >= 3.5:
            return "Dean's List"
        if self._gpa >= 2.0:
            return "Good Standing"
        if self._gpa >= 1.0:
            return "Academic Probation"
        return "Academic Suspension"

    # ── Polymorphic override ───────────────────────────────────────────────
    def get_info(self) -> str:
        """
        Override Person.get_info() with richer student information.
        Demonstrates polymorphism: the same method name returns different
        output depending on the concrete type at runtime.
        """
        return (
            f"Student [{self._student_id}]: {self._name} | "
            f"Major: {self._major} | "
            f"GPA: {self._gpa:.2f} ({self.get_grade_letter()}) | "
            f"Status: {self.get_status()}"
        )

    # ── Serialisation ─────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        """Serialize the complete Student (including inherited Person fields)."""
        data = super().to_dict()          # Inherit Person fields
        data.update({
            "student_id":   self._student_id,
            "birth_date":   self._birth_date,
            "phone":        self._phone,
            "education_level": self._education_level,
            "major":        self._major,
            "gpa":          self._gpa,
            "semester":     self._semester,
            "grade_letter": self.get_grade_letter(),   # Computed field
            "status":       self.get_status(),         # Computed field
        })
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        """
        Deserialize a Student from a plain dictionary (e.g. from JSON file).
        Computed fields (grade_letter, status) are intentionally ignored;
        they are recalculated on every call to to_dict().
        """
        student = cls(
            student_id = data["student_id"],
            name       = data["name"],
            age        = int(data["age"]) if data.get("age") not in (None, "") else None,
            email      = data["email"],
            phone      = data["phone"],
            major      = data["major"],
            gpa        = float(data["gpa"]),
            semester   = data.get("semester"),
            birth_date = data.get("birth_date"),
            education_level = data.get("education_level"),
        )
        # Preserve the original creation timestamp if available
        if "created_at" in data:
            student._created_at = data["created_at"]
        return student

    def __repr__(self) -> str:
        return (
            f"Student(id={self._student_id!r}, name={self._name!r}, "
            f"major={self._major!r}, gpa={self._gpa})"
        )
