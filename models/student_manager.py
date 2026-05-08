"""
models/student_manager.py
─────────────────────────────────────────────────────────────────────────────
StudentManager – manages the in-memory collection of Students and handles
all File I/O (read/write JSON).

Design notes:
  • The internal _students list acts as the primary in-memory data structure.
    In lower-level terms this is analogous to an array of object pointers.
  • Every mutating operation (add / update / delete) immediately persists the
    state to the JSON file, guaranteeing durability.
  • File I/O is isolated in _load_from_file() / _save_to_file() so the rest
    of the code is free of I/O concerns.
─────────────────────────────────────────────────────────────────────────────
"""

import json
import os
from typing import List, Optional

from models.student import Student, generate_default_student_profile


class StudentManager:
    """
    Manages a collection of Student objects with full CRUD support and
    automatic JSON file persistence.

    Time-complexity notes are provided for each operation.
    """

    def __init__(self, data_file: str = "data/students.json") -> None:
        self._data_file: str         = data_file
        self._students: List[Student] = []   # In-memory array (pointer list)
        self._load_from_file()

    # ═════════════════════════════════ File I/O ══════════════════════════════

    def _load_from_file(self) -> None:
        """
        Read all students from the JSON file into memory.

        Time Complexity : O(n) – iterates over every stored record.
        Space Complexity: O(n) – holds all records in memory.

        Raises IOError if the file exists but cannot be parsed.
        """
        try:
            dir_name = os.path.dirname(self._data_file)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            if not os.path.exists(self._data_file):
                self._save_to_file()   # Create an empty file
                return

            with open(self._data_file, "r", encoding="utf-8") as fh:
                raw: list = json.load(fh)
                # Deserialise each dict → Student object
                self._students = [Student.from_dict(record) for record in raw]

        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
            raise IOError(f"Failed to load data from '{self._data_file}': {exc}") from exc

    def _save_to_file(self) -> None:
        """
        Persist the current in-memory list to the JSON file.

        Time Complexity : O(n) – serialises every Student.
        Space Complexity: O(n) – temporary serialised representation.

        Raises IOError on any filesystem error.
        """
        try:
            dir_name = os.path.dirname(self._data_file)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(self._data_file, "w", encoding="utf-8") as fh:
                json.dump(
                    [s.to_dict() for s in self._students],
                    fh,
                    indent=2,
                    ensure_ascii=False,
                )
        except OSError as exc:
            raise IOError(f"Failed to save data to '{self._data_file}': {exc}") from exc

    def reload(self) -> None:
        """
        Reload the student collection from the JSON file.

        Useful when the underlying file is modified externally while the
        application is still running.
        """
        self._load_from_file()

    # ═════════════════════════════════ READ ══════════════════════════════════

    def get_all(self) -> List[Student]:
        """
        Return a shallow copy of all students.
        Time Complexity: O(n) – copy of the list.
        """
        return list(self._students)

    def get_all_dicts(self) -> List[dict]:
        """
        Return every student serialised as a plain dict.
        Time Complexity: O(n).
        """
        return [s.to_dict() for s in self._students]

    def get_by_id(self, student_id: str) -> Optional[Student]:
        """
        Linear scan to find a student by ID.
        Time Complexity: O(n) worst case.
        Returns None if not found.
        """
        for student in self._students:
            if student.student_id == student_id:
                return student
        return None

    def count(self) -> int:
        """Return total number of students. O(1)."""
        return len(self._students)

    def backfill_missing_semesters(self, start: int = 3, end: int = 7) -> int:
        """Assign default semester values to students that do not have one yet."""
        if start > end:
            raise ValueError("Start semester cannot be greater than end semester.")

        updated = 0
        span = end - start + 1

        for index, student in enumerate(self._students):
            if student.semester is not None:
                continue

            student.semester = start + (index % span)
            updated += 1

        if updated:
            self._save_to_file()

        return updated

    def backfill_missing_profiles(self) -> int:
        """Assign default birth dates and education levels to incomplete records."""
        updated = 0

        for student in self._students:
            default_birth_date, default_education_level = generate_default_student_profile(student.student_id)
            changed = False

            if not student.birth_date:
                student.birth_date = default_birth_date
                changed = True

            if not student.education_level:
                student.education_level = default_education_level
                changed = True

            if changed:
                updated += 1

        if updated:
            self._save_to_file()

        return updated

    # ═════════════════════════════════ CREATE ════════════════════════════════

    def add_student(self, data: dict) -> Student:
        """
        Create and append a new Student.

        If 'student_id' is omitted or empty, one is auto-generated.

        Time Complexity: O(n) for duplicate-ID check; O(1) amortised append.
        Raises ValueError if the student_id already exists.
        """
        student_id = data.get("student_id", "").strip()
        if not student_id:
            student_id = self._generate_id()
            data = {**data, "student_id": student_id}

        if self.get_by_id(student_id) is not None:
            raise ValueError(f"Student ID '{student_id}' already exists.")

        student = Student.from_dict(data)
        self._students.append(student)      # O(1) amortised
        self._save_to_file()
        return student

    # ═════════════════════════════════ UPDATE ════════════════════════════════

    def update_student(self, student_id: str, data: dict) -> Optional[Student]:
        """
        Partially update an existing student's mutable attributes.

        Time Complexity: O(n) for the look-up; O(1) for the attribute update.
        Returns the updated Student, or None if not found.
        """
        student = self.get_by_id(student_id)
        if student is None:
            return None

        # Apply only the fields present in the incoming payload
        if "name"    in data: student.name    = data["name"]
        if "age"     in data: student.age     = int(data["age"])
        if "birth_date" in data: student.birth_date = data["birth_date"]
        if "email"   in data: student.email   = data["email"]
        if "phone"   in data: student.phone   = data["phone"]
        if "education_level" in data: student.education_level = data["education_level"]
        if "major"   in data: student.major   = data["major"]
        if "gpa"     in data: student.gpa     = float(data["gpa"])
        if "semester" in data: student.semester = data["semester"]

        self._save_to_file()
        return student

    # ═════════════════════════════════ DELETE ════════════════════════════════

    def delete_student(self, student_id: str) -> bool:
        """
        Remove a student by ID.

        Time Complexity: O(n) – list comprehension rebuilds the list.
        Returns True if a student was removed, False if not found.
        """
        original_len = len(self._students)
        self._students = [s for s in self._students if s.student_id != student_id]

        if len(self._students) == original_len:
            return False   # Nothing removed → student not found

        self._save_to_file()
        return True

    # ═════════════════════════════════ HELPERS ═══════════════════════════════

    def _generate_id(self) -> str:
        """
        Auto-generate a sequential student ID in the format STU-NNNN.

        Time Complexity: O(n) – scans existing IDs.
        """
        existing_nums: list[int] = []
        for s in self._students:
            parts = s.student_id.split("-")
            if len(parts) == 2 and parts[0] == "STU" and parts[1].isdigit():
                existing_nums.append(int(parts[1]))

        next_num = max(existing_nums, default=0) + 1
        return f"STU-{next_num:04d}"
