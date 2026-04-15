"""
matrix.py — Matrix Abstract Data Type (ADT) Implementation.

This module implements a Matrix data structure from scratch, demonstrating:
  - The ADT concept (a well-defined set of operations over encapsulated data)
  - Core matrix operations: addition, subtraction, scalar multiplication,
    matrix multiplication, transpose, determinant (2x2 / 3x3)
  - Real-world applications: image processing, graph adjacency, linear systems

Data Structure: Matrix
  A matrix is a two-dimensional array of numbers arranged in rows and columns.
  An m x n matrix has m rows and n columns.

ADT Operations:
  - create(rows, cols)      -> new zero matrix
  - from_list(data)         -> matrix from a 2-D list
  - get(i, j) / set(i, j)  -> element access
  - add(other)              -> element-wise addition
  - subtract(other)         -> element-wise subtraction
  - scalar_multiply(k)      -> multiply every element by k
  - multiply(other)         -> standard matrix multiplication
  - transpose()             -> flip rows and columns
  - determinant()           -> scalar (square matrices only)
  - identity(n)             -> n x n identity matrix
"""

from __future__ import annotations

from typing import Optional


class Matrix:
    """
    A two-dimensional matrix of real numbers.

    Internal representation: a flat list of floats stored in row-major order.
    This is more memory-efficient than a list-of-lists and mirrors how
    matrices are laid out in languages like C and NumPy.
    """

    # ---- Construction ------------------------------------------------------

    def __init__(self, rows: int, cols: int,
                 data: list[list[float]] | None = None) -> None:
        """
        Create a matrix of size rows x cols.
        If *data* is provided it must be a 2-D list matching the dimensions.
        """
        if rows <= 0 or cols <= 0:
            raise ValueError("Dimensions must be positive integers")
        self._rows = rows
        self._cols = cols

        if data is not None:
            if len(data) != rows or any(len(r) != cols for r in data):
                raise ValueError(
                    f"Data dimensions do not match {rows}x{cols}")
            # Flatten into row-major order
            self._data: list[float] = [
                float(data[i][j]) for i in range(rows) for j in range(cols)
            ]
        else:
            self._data = [0.0] * (rows * cols)

    @classmethod
    def from_list(cls, data: list[list[float]]) -> "Matrix":
        """Factory: build a Matrix from a 2-D Python list."""
        rows = len(data)
        cols = len(data[0]) if rows > 0 else 0
        return cls(rows, cols, data)

    @classmethod
    def identity(cls, n: int) -> "Matrix":
        """Return the n x n identity matrix."""
        m = cls(n, n)
        for i in range(n):
            m.set(i, i, 1.0)
        return m

    # ---- Properties --------------------------------------------------------

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def shape(self) -> tuple[int, int]:
        return (self._rows, self._cols)

    def is_square(self) -> bool:
        return self._rows == self._cols

    # ---- Element access ----------------------------------------------------

    def _index(self, i: int, j: int) -> int:
        """Convert 2-D index to flat index (row-major)."""
        if not (0 <= i < self._rows and 0 <= j < self._cols):
            raise IndexError(
                f"Index ({i}, {j}) out of range for "
                f"{self._rows}x{self._cols} matrix")
        return i * self._cols + j

    def get(self, i: int, j: int) -> float:
        """Return the element at row i, column j."""
        return self._data[self._index(i, j)]

    def set(self, i: int, j: int, value: float) -> None:
        """Set the element at row i, column j."""
        self._data[self._index(i, j)] = float(value)

    def get_row(self, i: int) -> list[float]:
        """Return row i as a list."""
        start = i * self._cols
        return self._data[start: start + self._cols]

    def get_col(self, j: int) -> list[float]:
        """Return column j as a list."""
        return [self._data[i * self._cols + j] for i in range(self._rows)]

    # ---- Arithmetic operations ---------------------------------------------

    def add(self, other: "Matrix") -> "Matrix":
        """
        Element-wise addition: C = A + B.
        Both matrices must have the same dimensions.

        Time complexity: O(m * n)
        """
        if self.shape != other.shape:
            raise ValueError(
                f"Cannot add {self.shape} and {other.shape} matrices")
        result = Matrix(self._rows, self._cols)
        result._data = [a + b for a, b in zip(self._data, other._data)]
        return result

    def subtract(self, other: "Matrix") -> "Matrix":
        """
        Element-wise subtraction: C = A - B.

        Time complexity: O(m * n)
        """
        if self.shape != other.shape:
            raise ValueError(
                f"Cannot subtract {other.shape} from {self.shape} matrix")
        result = Matrix(self._rows, self._cols)
        result._data = [a - b for a, b in zip(self._data, other._data)]
        return result

    def scalar_multiply(self, k: float) -> "Matrix":
        """
        Multiply every element by scalar k.

        Time complexity: O(m * n)
        """
        result = Matrix(self._rows, self._cols)
        result._data = [x * k for x in self._data]
        return result

    def multiply(self, other: "Matrix") -> "Matrix":
        """
        Standard matrix multiplication: C = A * B.
        A is m x n, B must be n x p.  Result is m x p.

        Algorithm:
          For each element C[i][j], compute the dot product of
          row i of A and column j of B.

        Time complexity: O(m * n * p)  — cubic in the common case of
        square matrices (O(n^3)).
        """
        if self._cols != other._rows:
            raise ValueError(
                f"Cannot multiply {self.shape} and {other.shape} matrices "
                f"(inner dimensions must match)")
        m, n, p = self._rows, self._cols, other._cols
        result = Matrix(m, p)
        for i in range(m):
            for j in range(p):
                dot = 0.0
                for k in range(n):
                    dot += self.get(i, k) * other.get(k, j)
                result.set(i, j, dot)
        return result

    def transpose(self) -> "Matrix":
        """
        Return the transpose A^T (rows become columns).

        Time complexity: O(m * n)
        """
        result = Matrix(self._cols, self._rows)
        for i in range(self._rows):
            for j in range(self._cols):
                result.set(j, i, self.get(i, j))
        return result

    def determinant(self) -> float:
        """
        Compute the determinant of a square matrix using cofactor expansion.

        Supported sizes:
          1x1 — trivial
          2x2 — ad - bc
          3x3 — Sarrus' rule / cofactor expansion
          nxn — recursive cofactor expansion (for demonstration; not efficient
                 for large n because it is O(n!)).

        Time complexity:
          O(1) for 1x1, O(1) for 2x2, O(n!) in general.
        """
        if not self.is_square():
            raise ValueError("Determinant is only defined for square matrices")
        n = self._rows

        if n == 1:
            return self.get(0, 0)

        if n == 2:
            return self.get(0, 0) * self.get(1, 1) - \
                   self.get(0, 1) * self.get(1, 0)

        # General case: cofactor expansion along the first row
        det = 0.0
        for j in range(n):
            cofactor = self._cofactor_matrix(0, j)
            sign = 1 if j % 2 == 0 else -1
            det += sign * self.get(0, j) * cofactor.determinant()
        return det

    def _cofactor_matrix(self, row: int, col: int) -> "Matrix":
        """Return the (n-1)x(n-1) matrix obtained by deleting *row* and *col*."""
        n = self._rows
        data: list[list[float]] = []
        for i in range(n):
            if i == row:
                continue
            r = []
            for j in range(n):
                if j == col:
                    continue
                r.append(self.get(i, j))
            data.append(r)
        return Matrix.from_list(data)

    # ---- Display -----------------------------------------------------------

    def __str__(self) -> str:
        lines = []
        for i in range(self._rows):
            row_str = "  ".join(f"{self.get(i, j):8.2f}"
                                for j in range(self._cols))
            lines.append(f"| {row_str} |")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Matrix({self._rows}x{self._cols})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        return self.shape == other.shape and self._data == other._data


# ---------------------------------------------------------------------------
# Demonstration / Application Examples
# ---------------------------------------------------------------------------

def demo_basic_operations() -> None:
    """Demonstrate core matrix operations with output."""
    print("=" * 60)
    print("MATRIX ADT — Demonstration")
    print("=" * 60)

    # --- Creation ---
    A = Matrix.from_list([
        [1, 2, 3],
        [4, 5, 6],
    ])
    B = Matrix.from_list([
        [7,  8,  9],
        [10, 11, 12],
    ])
    print("\nMatrix A (2x3):")
    print(A)
    print("\nMatrix B (2x3):")
    print(B)

    # --- Addition ---
    C = A.add(B)
    print("\nA + B =")
    print(C)

    # --- Scalar multiplication ---
    D = A.scalar_multiply(3)
    print("\n3 * A =")
    print(D)

    # --- Transpose ---
    AT = A.transpose()
    print("\nTranspose of A (3x2):")
    print(AT)

    # --- Matrix multiplication ---
    # A is 2x3, AT is 3x2 -> result is 2x2
    E = A.multiply(AT)
    print("\nA * A^T (2x2):")
    print(E)

    # --- Determinant ---
    S = Matrix.from_list([
        [6, 1, 1],
        [4, -2, 5],
        [2, 8, 7],
    ])
    print(f"\nSquare matrix S (3x3):\n{S}")
    print(f"det(S) = {S.determinant():.2f}")

    # --- Identity ---
    I = Matrix.identity(3)
    print(f"\nIdentity matrix I (3x3):\n{I}")
    product = S.multiply(I)
    print(f"\nS * I = S (verify):\n{product}")


def demo_graph_adjacency() -> None:
    """
    Application: represent a directed graph as an adjacency matrix.

    Nodes: 0, 1, 2, 3
    Edges: 0->1, 0->2, 1->2, 2->0, 2->3, 3->3
    """
    print("\n" + "=" * 60)
    print("APPLICATION — Graph Adjacency Matrix")
    print("=" * 60)

    adj = Matrix(4, 4)
    edges = [(0, 1), (0, 2), (1, 2), (2, 0), (2, 3), (3, 3)]
    for u, v in edges:
        adj.set(u, v, 1)

    print("\nAdjacency matrix:")
    print(adj)
    print(f"\nNode 0 connects to: "
          f"{[j for j in range(4) if adj.get(0, j) == 1]}")
    print(f"Node 2 connects to: "
          f"{[j for j in range(4) if adj.get(2, j) == 1]}")

    # Reachability in 2 steps = adj * adj
    two_step = adj.multiply(adj)
    print("\n2-step reachability matrix (adj^2):")
    print(two_step)


def demo_image_transform() -> None:
    """
    Application: simple 2-D image transformation using matrices.

    A 2-D rotation by angle theta is represented as:
      | cos(theta)  -sin(theta) |
      | sin(theta)   cos(theta) |
    """
    import math

    print("\n" + "=" * 60)
    print("APPLICATION — 2-D Image Rotation")
    print("=" * 60)

    theta = math.radians(90)  # 90-degree rotation
    R = Matrix.from_list([
        [math.cos(theta), -math.sin(theta)],
        [math.sin(theta),  math.cos(theta)],
    ])
    print(f"\nRotation matrix (90 degrees):\n{R}")

    # Rotate the point (3, 4)
    point = Matrix.from_list([[3], [4]])
    rotated = R.multiply(point)
    print(f"\nOriginal point: (3, 4)")
    print(f"After 90° rotation: ({rotated.get(0, 0):.2f}, "
          f"{rotated.get(1, 0):.2f})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_basic_operations()
    demo_graph_adjacency()
    demo_image_transform()
