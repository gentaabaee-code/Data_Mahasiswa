"""
utils/sort.py
─────────────────────────────────────────────────────────────────────────────
Sorting algorithms for Student records.

Algorithms implemented
──────────────────────
1. Bubble Sort    – O(n²)       – adjacent swap with early-exit optimisation
2. Insertion Sort – O(n²)       – build sorted sub-array left-to-right
3. Selection Sort – O(n²)       – select minimum and place at front each pass
4. Merge Sort     – O(n log n)  – divide-and-conquer recursive sort
5. Shell Sort     – O(n log²n)  – gap-based generalised insertion sort
                                   (Knuth gap sequence: 1 → 4 → 13 → 40 …)

All functions are non-destructive: they return a NEW sorted list.
─────────────────────────────────────────────────────────────────────────────
"""

from typing import Callable, List
from models.student import Student


# ─────────────────────────── Key extractor ────────────────────────────────

def _make_key(field: str) -> Callable[[Student], object]:
    """
    Return a key function that extracts the comparison value for *field*.

    String fields are lower-cased so sorts are case-insensitive.
    Numeric fields (gpa, age) are returned as their native type.
    """
    def key(student: Student):
        mapping = {
            "name":       student.name.lower(),
            "student_id": student.student_id.lower(),
            "email":      student.email.lower(),
            "major":      student.major.lower(),
            "gpa":        student.gpa,
            "age":        student.age,
        }
        # Fall back to name sort for unknown fields
        return mapping.get(field, student.name.lower())

    return key


# ─────────────────────────── Sort Algorithms ──────────────────────────────

class SortAlgorithms:
    """
    Collection of classic sorting algorithms that operate on List[Student].

    All methods accept a *key* parameter specifying the Student attribute
    to sort by, and return a new sorted list without modifying the input.
    """

    # ── 1. Bubble Sort ────────────────────────────────────────────────────
    @staticmethod
    def bubble_sort(students: List[Student], key: str = "name") -> List[Student]:
        """
        Bubble Sort – repeatedly compare and swap adjacent elements that are
        out of order. Includes an early-exit optimisation: if no swap occurs
        during a full pass the list is already sorted.

        Time Complexity
        ───────────────
        Best  : O(n)   – already sorted (early exit triggers)
        Avg   : O(n²)
        Worst : O(n²)  – reverse-sorted input

        Space Complexity: O(1) in-place (on a copy)
        """
        arr = list(students)          # Work on a copy; non-destructive
        n = len(arr)
        kfn = _make_key(key)

        for i in range(n):
            swapped = False
            for j in range(0, n - i - 1):
                if kfn(arr[j]) > kfn(arr[j + 1]):
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]    # Swap
                    swapped = True
            if not swapped:
                break             # Early exit: no swap → already sorted

        return arr

    # ── 2. Insertion Sort ─────────────────────────────────────────────────
    @staticmethod
    def insertion_sort(students: List[Student], key: str = "name") -> List[Student]:
        """
        Insertion Sort – grows a sorted sub-array from the left one element
        at a time by shifting larger elements rightward.

        Time Complexity
        ───────────────
        Best  : O(n)   – already sorted
        Avg   : O(n²)
        Worst : O(n²)  – reverse-sorted input

        Space Complexity: O(1)
        """
        arr = list(students)
        kfn = _make_key(key)

        for i in range(1, len(arr)):
            current = arr[i]
            j = i - 1
            # Shift elements of the sorted portion that are > current to the right
            while j >= 0 and kfn(arr[j]) > kfn(current):
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = current     # Insert current into its correct position

        return arr

    # ── 3. Selection Sort ─────────────────────────────────────────────────
    @staticmethod
    def selection_sort(students: List[Student], key: str = "name") -> List[Student]:
        """
        Selection Sort – scans the unsorted portion of the array, finds the
        minimum element, then places it at the start of that portion.

        Time Complexity
        ───────────────
        Best  : O(n²)  – always performs n*(n-1)/2 comparisons
        Avg   : O(n²)
        Worst : O(n²)

        Space Complexity: O(1)
        """
        arr = list(students)
        n = len(arr)
        kfn = _make_key(key)

        for i in range(n):
            min_idx = i
            for j in range(i + 1, n):
                if kfn(arr[j]) < kfn(arr[min_idx]):
                    min_idx = j
            arr[i], arr[min_idx] = arr[min_idx], arr[i]    # Place minimum

        return arr

    # ── 4. Merge Sort ─────────────────────────────────────────────────────
    @staticmethod
    def merge_sort(students: List[Student], key: str = "name") -> List[Student]:
        """
        Merge Sort – divide-and-conquer algorithm that recursively splits the
        list in half and merges the sorted halves.

        Time Complexity
        ───────────────
        Best  : O(n log n)
        Avg   : O(n log n)
        Worst : O(n log n)  – consistent regardless of input order

        Space Complexity: O(n) – requires O(n) auxiliary space for merging
        """
        arr = list(students)
        kfn = _make_key(key)

        def _merge(
            left: List[Student],
            right: List[Student],
        ) -> List[Student]:
            """Merge two sorted lists into one sorted list."""
            merged: List[Student] = []
            i = j = 0
            while i < len(left) and j < len(right):
                if kfn(left[i]) <= kfn(right[j]):
                    merged.append(left[i])
                    i += 1
                else:
                    merged.append(right[j])
                    j += 1
            merged.extend(left[i:])    # Append remaining left elements
            merged.extend(right[j:])   # Append remaining right elements
            return merged

        def _sort(lst: List[Student]) -> List[Student]:
            """Recursively split and merge."""
            if len(lst) <= 1:
                return lst
            mid = len(lst) // 2
            return _merge(_sort(lst[:mid]), _sort(lst[mid:]))

        return _sort(arr)

    # ── 5. Shell Sort ─────────────────────────────────────────────────────
    @staticmethod
    def shell_sort(students: List[Student], key: str = "name") -> List[Student]:
        """
        Shell Sort – a generalised insertion sort that first sorts elements
        far apart (large gap), then progressively narrows the gap to 1.

        Uses Knuth's gap sequence: h = 3h + 1  →  1, 4, 13, 40, 121, …
        This sequence gives better practical performance than the naive h/2.

        Time Complexity
        ───────────────
        Best  : O(n log n)
        Avg   : O(n log²n)  – with Knuth's sequence
        Worst : O(n²)       – worst-case depends on gap sequence

        Space Complexity: O(1)
        """
        arr = list(students)
        n = len(arr)
        kfn = _make_key(key)

        # Compute the starting gap using Knuth's sequence
        gap = 1
        while gap < n // 3:
            gap = gap * 3 + 1      # 1 → 4 → 13 → 40 → 121 …

        while gap >= 1:
            # Perform insertion sort with the current gap
            for i in range(gap, n):
                current = arr[i]
                j = i
                while j >= gap and kfn(arr[j - gap]) > kfn(current):
                    arr[j] = arr[j - gap]
                    j -= gap
                arr[j] = current
            gap //= 3              # Reduce gap

        return arr
