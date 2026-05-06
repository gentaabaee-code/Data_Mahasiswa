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

from datetime import datetime, timezone


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
        age: int,
        email: str,
        phone: str,
        major: str,
        gpa: float,
        address: str = "",
    ) -> None:
        super().__init__(name, age, email)       # Invoke parent __init__
        self._student_id: str   = student_id
        self._phone: str        = phone
        self._major: str        = major
        self._gpa: float        = round(float(gpa), 2)
        self._address: str      = address

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

    # ── address ───────────────────────────────────────────────────────────
    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str) -> None:
        self._address = value.strip()

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
            "phone":        self._phone,
            "major":        self._major,
            "gpa":          self._gpa,
            "address":      self._address,
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
            age        = int(data["age"]),
            email      = data["email"],
            phone      = data["phone"],
            major      = data["major"],
            gpa        = float(data["gpa"]),
            address    = data.get("address", ""),
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
