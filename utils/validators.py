"""
utils/validators.py
─────────────────────────────────────────────────────────────────────────────
Input validation using Regular Expressions (Regex).

All patterns are compiled once at module level for performance.
The StudentValidator class exposes static validators for each field and a
composite validate() method that returns a list of error messages.
─────────────────────────────────────────────────────────────────────────────
"""

import re
from datetime import date
from typing import Dict, List, Optional

from models.student import DEFAULT_EDUCATION_LEVELS


# ═════════════════════════════════════════════════════════════════════════════
#  Compiled Regex Patterns
# ═════════════════════════════════════════════════════════════════════════════

_PATTERNS: Dict[str, re.Pattern] = {
    # Numeric student ID only: 8–12 digits
    "student_id": re.compile(r"^\d{8,12}$"),

    # Full name: letters (incl. accented), spaces, hyphens, apostrophes; 2–100 chars
    "name": re.compile(r"^[A-Za-zÀ-ÿ\s'\-]{2,100}$"),

    # Standard email (RFC-ish); local@domain.tld
    "email": re.compile(
        r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    ),

    # Phone: optional leading +, then digits/spaces/hyphens/parens; 7–15 chars
    "phone": re.compile(r"^\+?[\d\s\-\(\)]{7,15}$"),

    # Major: letters, digits, spaces, &, /, ', -; 2–100 chars
    "major": re.compile(r"^[A-Za-z0-9\s&'\-/]{2,100}$"),
}


# ═════════════════════════════════════════════════════════════════════════════
#  Validator Class
# ═════════════════════════════════════════════════════════════════════════════

class StudentValidator:
    """
    Static validation helpers for Student input fields.

    Each field-level method returns a human-readable error string on failure,
    or None when the value is valid.

    The composite validate() method runs all applicable checks and returns
    a list of error messages (empty list = all inputs are valid).
    """

    @staticmethod
    def validate_student_id(value) -> Optional[str]:
        """Validate student ID format: numeric 8-12 digit NIM."""
        if not value or not str(value).strip():
            return "Student ID is required."
        if not _PATTERNS["student_id"].match(str(value).strip()):
            return (
                "NIM harus berupa angka dengan panjang 8 sampai 12 digit."
            )
        return None

    @staticmethod
    def validate_name(value) -> Optional[str]:
        """Validate full name: 2–100 letters, spaces, hyphens, apostrophes."""
        if not value or not str(value).strip():
            return "Full name is required."
        if not _PATTERNS["name"].match(str(value).strip()):
            return (
                "Name must be 2–100 characters and may only contain letters, "
                "spaces, hyphens, or apostrophes."
            )
        return None

    @staticmethod
    def validate_age(value) -> Optional[str]:
        """Validate age: integer between 16 and 100."""
        try:
            age = int(value)
        except (TypeError, ValueError):
            return "Age must be a whole number."
        if not (16 <= age <= 100):
            return "Age must be between 16 and 100."
        return None

    @staticmethod
    def validate_birth_date(value) -> Optional[str]:
        """Validate birth date: ISO date and age between 16 and 100."""
        if value is None or not str(value).strip():
            return "Birth date is required."

        try:
            birth_date = date.fromisoformat(str(value).strip())
        except ValueError:
            return "Birth date must use the YYYY-MM-DD format."

        today = date.today()
        if birth_date > today:
            return "Birth date cannot be in the future."

        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        if not (16 <= age <= 100):
            return "Birth date must produce an age between 16 and 100 years."

        return None

    @staticmethod
    def validate_email(value) -> Optional[str]:
        """Validate email address format."""
        if not value or not str(value).strip():
            return "Email address is required."
        if not _PATTERNS["email"].match(str(value).strip()):
            return "Please enter a valid email address (e.g. user@university.edu)."
        return None

    @staticmethod
    def validate_phone(value) -> Optional[str]:
        """Validate phone number: 7–15 digits, optional +, spaces, hyphens."""
        if not value or not str(value).strip():
            return "Phone number is required."
        if not _PATTERNS["phone"].match(str(value).strip()):
            return (
                "Phone must be 7–15 characters and may contain digits, "
                "spaces, hyphens, parentheses, or a leading '+'."
            )
        return None

    @staticmethod
    def validate_major(value) -> Optional[str]:
        """Validate academic major name: 2–100 alphanumeric / symbol chars."""
        if not value or not str(value).strip():
            return "Major is required."
        if not _PATTERNS["major"].match(str(value).strip()):
            return (
                "Major must be 2–100 characters (letters, digits, spaces, "
                "&, /, -, or apostrophe)."
            )
        return None

    @staticmethod
    def validate_gpa(value) -> Optional[str]:
        """Validate GPA: decimal number in the range [0.0, 4.0]."""
        try:
            gpa = float(value)
        except (TypeError, ValueError):
            return "GPA must be a decimal number (e.g. 3.50)."
        if not (0.0 <= gpa <= 4.0):
            return "GPA must be between 0.0 and 4.0."
        return None

    @staticmethod
    def validate_semester(value) -> Optional[str]:
        """Validate semester: integer between 1 and 14."""
        if value is None or not str(value).strip():
            return "Semester is required."
        try:
            semester = int(value)
        except (TypeError, ValueError):
            return "Semester harus berupa angka bulat."
        if not (1 <= semester <= 14):
            return "Semester harus berada di antara 1 sampai 14."
        return None

    @staticmethod
    def validate_education_level(value) -> Optional[str]:
        """Validate education level: D3, D4, S1, S2, or S3."""
        if value is None or not str(value).strip():
            return "Education level is required."

        normalized = str(value).strip().upper()
        if normalized not in DEFAULT_EDUCATION_LEVELS:
            return "Education level must be one of D3, D4, S1, S2, or S3."

        return None

    # ── Composite validator ────────────────────────────────────────────────

    @classmethod
    def validate(cls, data: dict, is_update: bool = False) -> List[str]:
        """
        Run all applicable validators on *data* and return a list of errors.

        Parameters
        ----------
        data : dict
            Input payload (typically parsed from JSON request body).
        is_update : bool
            When True, student_id is NOT validated (it comes from the URL),
            and missing optional fields are silently skipped.

        Returns
        -------
        List[str]
            Empty list  →  all inputs are valid.
            Non-empty   →  each string is one human-readable error message.

        Time Complexity: O(F) where F = number of fields to validate (constant).
        """
        errors: List[str] = []

        # Map field names to their validator functions
        field_validators = {
            "student_id": cls.validate_student_id,
            "name":       cls.validate_name,
            "age":        cls.validate_age,
            "birth_date": cls.validate_birth_date,
            "email":      cls.validate_email,
            "phone":      cls.validate_phone,
            "education_level": cls.validate_education_level,
            "major":      cls.validate_major,
            "gpa":        cls.validate_gpa,
            "semester":   cls.validate_semester,
        }

        # Which fields are required for a CREATE operation
        required_on_create = [
            "student_id", "name", "birth_date", "email", "phone", "education_level", "major", "gpa", "semester"
        ]

        for field, validator_fn in field_validators.items():
            if field not in data:
                # On CREATE → missing required field is an error
                if not is_update and field in required_on_create:
                    errors.append(f"Field '{field}' is required.")
                continue   # Skip validation if field absent on UPDATE

            error = validator_fn(data[field])
            if error:
                errors.append(error)

        return errors
