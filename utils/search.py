"""
utils/search.py
─────────────────────────────────────────────────────────────────────────────
Search algorithms for Student records.

Algorithms implemented
──────────────────────
1. Linear Search    – O(n)     – full scan, returns all partial matches
2. Sequential Search – O(n)    – stops at the FIRST match (early-exit)
3. Binary Search    – O(log n) – prefix match on a pre-sorted list

All functions are pure: they do NOT mutate the input list.
─────────────────────────────────────────────────────────────────────────────
"""

from typing import List
from models.student import Student


# ─────────────────────────── Helper ───────────────────────────────────────

def _get_field_str(student: Student, field: str) -> str:
    """Extract a lower-cased string value from a Student for comparison."""
    mapping = {
        "name":       student.name,
        "student_id": student.student_id,
        "birth_date": student.birth_date,
        "email":      student.email,
        "major":      student.major,
        "phone":      student.phone,
        "education_level": student.education_level,
    }
    return str(mapping.get(field, student.name)).lower()


# ─────────────────────────── Search Algorithms ────────────────────────────

class SearchAlgorithms:
    """Collection of search algorithms that operate on a List[Student]."""

    # ── 1. Linear Search ──────────────────────────────────────────────────
    @staticmethod
    def linear_search(
        students: List[Student],
        query: str,
        field: str = "name",
    ) -> List[Student]:
        """
        Linear Search – scans every element for a partial, case-insensitive
        substring match and returns ALL matching students.

        Time Complexity
        ───────────────
        Best  : O(1)  – first element matches and we still scan all (collects all)
        Avg   : O(n)
        Worst : O(n)  – no match / match at the very end

        Space Complexity: O(k) where k = number of matches
        """
        q = query.lower()
        results: List[Student] = []

        for student in students:                             # Traverse array
            if q in _get_field_str(student, field):         # Substring match
                results.append(student)

        return results

    # ── 2. Sequential Search ──────────────────────────────────────────────
    @staticmethod
    def sequential_search(
        students: List[Student],
        query: str,
        field: str = "name",
    ) -> List[Student]:
        """
        Sequential Search – identical to linear but stops at the FIRST match.
        Useful when only one result is needed (e.g. look-up by unique ID).

        Time Complexity
        ───────────────
        Best  : O(1)  – match at index 0
        Avg   : O(n/2) ≈ O(n)
        Worst : O(n)  – match at the last index or no match

        Space Complexity: O(1)
        """
        q = query.lower()

        for student in students:
            if q in _get_field_str(student, field):
                return [student]      # Early exit – return on first hit

        return []

    # ── 3. Binary Search ──────────────────────────────────────────────────
    @staticmethod
    def binary_search(
        sorted_students: List[Student],
        query: str,
        field: str = "name",
    ) -> List[Student]:
        """
        Binary Search – requires the input list to be sorted ascending by
        *field*. Finds all students whose field value starts with *query*.

        Algorithm
        ─────────
        Phase 1 – Use binary search to locate the leftmost index where the
                   field value begins with the query string.
        Phase 2 – Expand left and right from that index to collect all
                   adjacent prefix matches (contiguous in a sorted list).

        Time Complexity
        ───────────────
        Best  : O(1)  – single-element list
        Avg   : O(log n)  – binary search phase
        Worst : O(log n + k) where k = number of prefix matches

        Space Complexity: O(k)

        Note: Requires sorted data. The caller (app.py) must sort first.
        """
        q = query.lower()
        n = len(sorted_students)

        if n == 0:
            return []

        # ── Phase 1: find the leftmost matching index ──────────────────────
        lo, hi, match_index = 0, n - 1, -1

        while lo <= hi:
            mid = (lo + hi) // 2
            val = _get_field_str(sorted_students[mid], field)

            if val.startswith(q):
                match_index = mid
                hi = mid - 1            # Keep searching left for earlier matches
            elif val < q:
                lo = mid + 1
            else:
                hi = mid - 1

        if match_index == -1:
            return []                   # No prefix match found

        # ── Phase 2: expand to collect all adjacent prefix matches ─────────
        results: List[Student] = []

        i = match_index
        while i >= 0 and _get_field_str(sorted_students[i], field).startswith(q):
            results.insert(0, sorted_students[i])   # Prepend to preserve order
            i -= 1

        i = match_index + 1
        while i < n and _get_field_str(sorted_students[i], field).startswith(q):
            results.append(sorted_students[i])
            i += 1

        return results
