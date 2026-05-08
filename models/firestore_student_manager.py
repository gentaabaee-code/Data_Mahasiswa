"""
models/firestore_student_manager.py
──────────────────────────────────────────────────────────────────────────────
FirestoreStudentManager – Firebase Firestore-backed implementation of the
same public API as StudentManager.

Drop-in replacement: swap StudentManager for FirestoreStudentManager in
app.py to persist all student data in Cloud Firestore instead of a local
JSON file.

Firestore collection used: "students"
Each document key is the student's student_id field.

Usage in app.py:
    from models.firestore_student_manager import FirestoreStudentManager
    manager = FirestoreStudentManager()
──────────────────────────────────────────────────────────────────────────────
"""

import os
from typing import List, Optional

from firebase_config import db          # Firestore client singleton
from models.student import Student, generate_default_student_profile

_COLLECTION = "students"


class FirestoreStudentManager:
    """
    Manages Student documents in Cloud Firestore.

    All reads go directly to Firestore (no in-memory cache) so that multiple
    app instances always see consistent data.
    """

    def __init__(self, seed_file: Optional[str] = None, collection: str = _COLLECTION) -> None:
        self._seed_file = seed_file
        self._collection = db.collection(collection)
        self._bootstrap_from_file()

    def _bootstrap_from_file(self) -> None:
        if not self._seed_file or not os.path.exists(self._seed_file):
            return

        if next(self._collection.limit(1).stream(), None) is not None:
            return

        from models.student_manager import StudentManager

        legacy_manager = StudentManager(data_file=self._seed_file)
        for student in legacy_manager.get_all():
            self._collection.document(student.student_id).set(student.to_dict())

    # ═══════════════════════════════ READ ════════════════════════════════════

    def get_all(self) -> List[Student]:
        """Return all students from Firestore."""
        students = [Student.from_dict(doc.to_dict()) for doc in self._collection.stream()]
        return sorted(students, key=lambda student: student.student_id)

    def get_all_dicts(self) -> List[dict]:
        """Return all students as plain dicts."""
        return [s.to_dict() for s in self.get_all()]

    def get_by_id(self, student_id: str) -> Optional[Student]:
        """Fetch a single student by ID. Returns None if not found."""
        doc = self._collection.document(student_id).get()
        if doc.exists:
            return Student.from_dict(doc.to_dict())
        return None

    def count(self) -> int:
        return len(self.get_all())

    def backfill_missing_semesters(self, start: int = 3, end: int = 7) -> int:
        """Assign default semester values to students that do not have one yet."""
        if start > end:
            raise ValueError("Start semester cannot be greater than end semester.")

        students = self.get_all()
        updated = 0
        span = end - start + 1
        batch = db.batch()

        for index, student in enumerate(students):
            if student.semester is not None:
                continue

            student.semester = start + (index % span)
            batch.set(self._collection.document(student.student_id), student.to_dict())
            updated += 1

        if updated:
            batch.commit()

        return updated

    def backfill_missing_profiles(self) -> int:
        """Assign default birth dates and education levels to incomplete records."""
        students = self.get_all()
        updated = 0
        batch = db.batch()

        for student in students:
            default_birth_date, default_education_level = generate_default_student_profile(student.student_id)
            changed = False

            if not student.birth_date:
                student.birth_date = default_birth_date
                changed = True

            if not student.education_level:
                student.education_level = default_education_level
                changed = True

            if not changed:
                continue

            batch.set(self._collection.document(student.student_id), student.to_dict())
            updated += 1

        if updated:
            batch.commit()

        return updated

    # ═══════════════════════════════ CREATE ══════════════════════════════════

    def add_student(self, data: dict) -> Student:
        """
        Persist a new student to Firestore.

        Raises ValueError if a student with the same ID already exists.
        """
        student_id = data.get("student_id", "").strip()
        if not student_id:
            student_id = self._generate_id()
            data = {**data, "student_id": student_id}

        ref = self._collection.document(student_id)
        if ref.get().exists:
            raise ValueError(
                f"Student ID '{student_id}' already exists."
            )

        student = Student.from_dict(data)
        ref.set(student.to_dict())
        return student

    # ═══════════════════════════════ UPDATE ══════════════════════════════════

    def update_student(self, student_id: str, data: dict) -> Optional[Student]:
        """
        Update fields of an existing student document.

                Allowed keyword arguments match the Student attributes:
                    name, age, email, major, gpa, semester

        Returns the updated Student, or None if not found.
        """
        ref = self._collection.document(student_id)
        doc = ref.get()
        if not doc.exists:
            return None

        student = Student.from_dict(doc.to_dict())

        if "name" in data:
            student.name = data["name"]
        if "age" in data:
            student.age = int(data["age"])
        if "birth_date" in data:
            student.birth_date = data["birth_date"]
        if "email" in data:
            student.email = data["email"]
        if "phone" in data:
            student.phone = data["phone"]
        if "education_level" in data:
            student.education_level = data["education_level"]
        if "major" in data:
            student.major = data["major"]
        if "gpa" in data:
            student.gpa = float(data["gpa"])
        if "semester" in data:
            student.semester = data["semester"]

        ref.set(student.to_dict())
        return student

    # ═══════════════════════════════ DELETE ══════════════════════════════════

    def delete_student(self, student_id: str) -> bool:
        """
        Delete a student document by ID.

        Returns True if deleted, False if the document did not exist.
        """
        ref = self._collection.document(student_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True

    def _generate_id(self) -> str:
        existing_nums: list[int] = []
        for student in self.get_all():
            parts = student.student_id.split("-")
            if len(parts) == 2 and parts[0] == "STU" and parts[1].isdigit():
                existing_nums.append(int(parts[1]))

        next_num = max(existing_nums, default=0) + 1
        return f"STU-{next_num:04d}"

    # ═══════════════════════════ COMPATIBILITY ════════════════════════════════

    def reload(self) -> None:
        """No-op: Firestore reads are always live."""

    @property
    def students(self) -> List[Student]:
        """Convenience property – returns all students."""
        return self.get_all()
