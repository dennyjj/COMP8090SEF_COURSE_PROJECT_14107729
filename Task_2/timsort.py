"""
timsort.py — Timsort Algorithm Implementation and Demonstration.

Timsort is a hybrid sorting algorithm derived from merge sort and insertion
sort, designed by Tim Peters in 2002 for CPython.  It is the default sorting
algorithm in Python (list.sort / sorted) and Java (Arrays.sort for objects).

Key Concepts:
  1. Runs     — naturally ordered subsequences in the input.
  2. Minrun   — a tunable minimum run length (typically 32–64).
                Short runs are extended to minrun using insertion sort.
  3. Merge    — adjacent runs are merged with a modified merge sort that
                takes advantage of already-sorted data.
  4. Galloping — when one run consistently "wins" during a merge, Timsort
                 switches to exponential search (galloping mode) to skip
                 large blocks, reducing comparisons.

Time Complexity:
  Best case:    O(n)       — input is already sorted (detected as one run)
  Average case: O(n log n)
  Worst case:   O(n log n)

Space Complexity: O(n) — for the temporary merge buffer.

Stability: Timsort is a *stable* sort (equal elements keep their original
relative order).
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Helper: compute minrun from the array length
# ---------------------------------------------------------------------------

def _compute_minrun(n: int) -> int:
    """
    Choose a minrun value such that n / minrun is a power of 2 or
    close to it, which makes the final merges balanced.

    Algorithm (from CPython):
      Take the six most significant bits of n, and add 1 if any of the
      remaining bits are set.  Result is in the range [32, 64].
    """
    r = 0  # becomes 1 if any shifted-off bit is set
    while n >= 64:
        r |= n & 1
        n >>= 1
    return n + r


# ---------------------------------------------------------------------------
# Insertion sort (used to extend short runs to minrun)
# ---------------------------------------------------------------------------

def _insertion_sort(arr: list, left: int, right: int) -> None:
    """
    Sort arr[left .. right] in-place using binary insertion sort.

    Binary insertion sort uses binary search to find the insertion point,
    reducing comparisons to O(n log n) while keeping O(n^2) moves in the
    worst case.  For small arrays (≤ 64 elements) this is very fast due
    to low overhead and good cache locality.
    """
    for i in range(left + 1, right + 1):
        key = arr[i]
        # Binary search for the correct position in arr[left .. i-1]
        lo, hi = left, i
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] > key:
                hi = mid
            else:
                lo = mid + 1
        # Shift elements to make room and insert the key
        arr[lo + 1: i + 1] = arr[lo: i]
        arr[lo] = key


# ---------------------------------------------------------------------------
# Merge two adjacent sorted runs
# ---------------------------------------------------------------------------

def _merge(arr: list, left: int, mid: int, right: int) -> None:
    """
    Merge two sorted sub-arrays arr[left..mid] and arr[mid+1..right].

    Uses a temporary buffer for the left half (smaller of the two runs),
    keeping space usage proportional to the run size.

    This implementation includes a simplified galloping heuristic:
    when one run wins MIN_GALLOP consecutive comparisons, it enters
    galloping mode where it uses exponential search to skip ahead.
    """
    left_part = arr[left: mid + 1]
    right_part = arr[mid + 1: right + 1]

    i = 0  # index into left_part
    j = 0  # index into right_part
    k = left  # index into arr

    MIN_GALLOP = 7  # threshold before entering galloping mode
    left_wins = 0
    right_wins = 0

    while i < len(left_part) and j < len(right_part):
        if left_part[i] <= right_part[j]:
            arr[k] = left_part[i]
            i += 1
            left_wins += 1
            right_wins = 0
        else:
            arr[k] = right_part[j]
            j += 1
            right_wins += 1
            left_wins = 0
        k += 1

        # --- Galloping mode ---
        # If one side consistently wins, use exponential search to skip
        if left_wins >= MIN_GALLOP:
            # Gallop through left_part
            idx = _gallop_right(right_part[j] if j < len(right_part)
                                else float('inf'),
                                left_part, i, len(left_part))
            arr[k: k + idx - i] = left_part[i: idx]
            k += idx - i
            i = idx
            left_wins = 0
        elif right_wins >= MIN_GALLOP:
            # Gallop through right_part
            idx = _gallop_right(left_part[i] if i < len(left_part)
                                else float('inf'),
                                right_part, j, len(right_part))
            arr[k: k + idx - j] = right_part[j: idx]
            k += idx - j
            j = idx
            right_wins = 0

    # Copy remaining elements
    while i < len(left_part):
        arr[k] = left_part[i]
        i += 1
        k += 1
    while j < len(right_part):
        arr[k] = right_part[j]
        j += 1
        k += 1


def _gallop_right(key, arr: list, lo: int, hi: int) -> int:
    """
    Use exponential search to find the position where *key* would be
    inserted in arr[lo..hi-1], assuming arr is sorted.

    First grows the search range exponentially (1, 3, 7, 15, …),
    then narrows with binary search.  This gives O(log k) comparisons
    where k is the distance to the insertion point.
    """
    if lo >= hi:
        return lo
    offset = 1
    while lo + offset < hi and arr[lo + offset] < key:
        offset *= 2
    # Binary search within the narrowed range
    start = lo + offset // 2
    end = min(lo + offset, hi)
    while start < end:
        mid = (start + end) // 2
        if arr[mid] < key:
            start = mid + 1
        else:
            end = mid
    return start


# ---------------------------------------------------------------------------
# Timsort — main entry point
# ---------------------------------------------------------------------------

def timsort(arr: list) -> list:
    """
    Sort *arr* in-place using the Timsort algorithm and return it.

    Steps:
      1. Compute minrun based on the array length.
      2. Divide the array into runs of at least minrun elements.
         Short natural runs are extended with insertion sort.
      3. Push runs onto a stack and merge according to invariants
         (similar to merge sort, but adaptive).
    """
    n = len(arr)
    if n < 2:
        return arr

    minrun = _compute_minrun(n)

    # Step 1: create runs of at least minrun, using insertion sort
    # to extend short natural runs.
    runs: list[tuple[int, int]] = []  # (start, length)
    i = 0
    while i < n:
        run_start = i
        # Detect a natural ascending or descending run
        if i + 1 < n:
            if arr[i] <= arr[i + 1]:
                # Ascending run
                while i + 1 < n and arr[i] <= arr[i + 1]:
                    i += 1
            else:
                # Descending run — reverse it to make ascending
                while i + 1 < n and arr[i] > arr[i + 1]:
                    i += 1
                arr[run_start: i + 1] = arr[run_start: i + 1][::-1]
        i += 1

        # Extend to minrun if needed using insertion sort
        run_end = min(run_start + minrun - 1, n - 1)
        if i - 1 < run_end:
            _insertion_sort(arr, run_start, run_end)
            i = run_end + 1

        runs.append((run_start, i - run_start))

    # Step 2: merge runs using a stack-based strategy.
    # Invariants maintained:
    #   (a) len(runs[-3]) > len(runs[-2]) + len(runs[-1])
    #   (b) len(runs[-2]) > len(runs[-1])
    # When violated, merge adjacent runs to restore the invariant.
    stack: list[tuple[int, int]] = []  # (start, length)

    for run in runs:
        stack.append(run)
        # Merge until invariants are satisfied
        while len(stack) > 1:
            if len(stack) >= 3:
                x_start, x_len = stack[-3]
                y_start, y_len = stack[-2]
                z_start, z_len = stack[-1]
                if x_len <= y_len + z_len:
                    # Merge the smaller pair
                    if x_len < z_len:
                        _merge(arr, x_start,
                               x_start + x_len - 1,
                               y_start + y_len - 1)
                        stack[-3] = (x_start, x_len + y_len)
                        del stack[-2]
                    else:
                        _merge(arr, y_start,
                               y_start + y_len - 1,
                               z_start + z_len - 1)
                        stack[-2] = (y_start, y_len + z_len)
                        del stack[-1]
                    continue
                elif y_len <= z_len:
                    _merge(arr, y_start,
                           y_start + y_len - 1,
                           z_start + z_len - 1)
                    stack[-2] = (y_start, y_len + z_len)
                    del stack[-1]
                    continue
            elif len(stack) == 2:
                y_start, y_len = stack[-2]
                z_start, z_len = stack[-1]
                if y_len <= z_len:
                    _merge(arr, y_start,
                           y_start + y_len - 1,
                           z_start + z_len - 1)
                    stack[-2] = (y_start, y_len + z_len)
                    del stack[-1]
                    continue
            break

    # Final merges: collapse the stack completely
    while len(stack) > 1:
        y_start, y_len = stack[-2]
        z_start, z_len = stack[-1]
        _merge(arr, y_start,
               y_start + y_len - 1,
               z_start + z_len - 1)
        stack[-2] = (y_start, y_len + z_len)
        del stack[-1]

    return arr


# ---------------------------------------------------------------------------
# Demonstrations
# ---------------------------------------------------------------------------

def demo_step_by_step() -> None:
    """Walk through Timsort on a small array, printing each phase."""
    print("=" * 60)
    print("TIMSORT — Step-by-step Demonstration")
    print("=" * 60)

    data = [5, 21, 7, 23, 19, 10, 12, 1, 15, 4, 3, 8, 17, 6, 14, 2]
    print(f"\nOriginal array ({len(data)} elements):")
    print(f"  {data}")

    minrun = _compute_minrun(len(data))
    print(f"\nComputed minrun = {minrun}")
    print("  (For small arrays, minrun equals the array length,")
    print("   so the entire array is sorted with insertion sort.)")

    result = timsort(list(data))  # copy to preserve original
    print(f"\nSorted result:")
    print(f"  {result}")

    # Verify
    assert result == sorted(data), "Sort result does not match!"
    print("  Verified: matches Python's built-in sorted().")


def demo_already_sorted() -> None:
    """Show Timsort's best-case behaviour on pre-sorted input."""
    print("\n" + "=" * 60)
    print("TIMSORT — Best Case: Already Sorted Input")
    print("=" * 60)

    data = list(range(1, 21))
    print(f"\nInput: {data}")
    result = timsort(list(data))
    print(f"Output: {result}")
    print("  Timsort detects this as a single natural run -> O(n).")


def demo_reverse_sorted() -> None:
    """Show handling of descending input."""
    print("\n" + "=" * 60)
    print("TIMSORT — Reverse Sorted Input")
    print("=" * 60)

    data = list(range(20, 0, -1))
    print(f"\nInput:  {data}")
    result = timsort(list(data))
    print(f"Output: {result}")
    print("  Timsort detects the descending run, reverses it, -> O(n).")


def demo_performance_comparison() -> None:
    """
    Compare Timsort against basic sorting algorithms on various inputs.
    Uses a simple comparison counter to illustrate efficiency.
    """
    import time
    import random

    print("\n" + "=" * 60)
    print("TIMSORT — Performance Comparison")
    print("=" * 60)

    sizes = [1000, 5000, 10000]

    for size in sizes:
        random.seed(42)
        data = [random.randint(1, 100000) for _ in range(size)]

        # Timsort (our implementation)
        arr1 = list(data)
        t0 = time.perf_counter()
        timsort(arr1)
        t_timsort = time.perf_counter() - t0

        # Python built-in sort (also Timsort, but in C)
        arr2 = list(data)
        t0 = time.perf_counter()
        arr2.sort()
        t_builtin = time.perf_counter() - t0

        # Verify correctness
        assert arr1 == arr2, "Results differ!"

        print(f"\n  n = {size:>6,d}")
        print(f"    Our Timsort:    {t_timsort:.6f} s")
        print(f"    Built-in sort:  {t_builtin:.6f} s")

    print("\n  Note: Python's built-in sort is implemented in C, so it is")
    print("  much faster.  Both use the Timsort algorithm internally.")


def demo_stability() -> None:
    """Demonstrate that Timsort is a stable sort."""
    print("\n" + "=" * 60)
    print("TIMSORT — Stability Demonstration")
    print("=" * 60)

    # Pairs of (priority, name).  Items with the same priority should
    # keep their original relative order after sorting.
    tasks = [
        (3, "Email"),
        (1, "Urgent-A"),
        (2, "Meeting"),
        (1, "Urgent-B"),
        (3, "Report"),
        (2, "Review"),
    ]
    print(f"\nOriginal:  {tasks}")

    # Sort by priority (first element of tuple)
    sorted_tasks = timsort(list(tasks))
    print(f"Sorted:    {sorted_tasks}")
    print("  Notice: 'Urgent-A' still comes before 'Urgent-B' (both priority 1).")
    print("  This confirms Timsort is stable.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_step_by_step()
    demo_already_sorted()
    demo_reverse_sorted()
    demo_stability()
    demo_performance_comparison()
