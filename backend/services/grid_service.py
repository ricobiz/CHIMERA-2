from dataclasses import dataclass
from typing import Tuple, Dict
import re

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def index_to_col_letters(index: int) -> str:
    """0-based index -> letters (A..Z, AA..AZ, BA.. etc.)"""
    if index < 0:
        index = 0
    s = ""
    n = index
    while True:
        n, r = divmod(n, 26)
        s = LETTERS[r] + s
        if n == 0:
            break
        n -= 1  # excel-style
    return s

def col_letters_to_index(s: str) -> int:
    """letters -> 0-based index"""
    s = s.strip().upper()
    n = 0
    for ch in s:
        n = n * 26 + (ord(ch) - ord('A') + 1)
    return n - 1

CELL_RE = re.compile(r"^[A-Z]{1,2}[0-9]{1,2}$")

@dataclass
class GridConfig:
    rows: int = 12
    cols: int = 8

    def cell_size(self, viewport_w: int, viewport_h: int) -> Tuple[float, float]:
        return viewport_w / self.cols, viewport_h / self.rows

    def cell_to_xy(self, cell: str, viewport_w: int, viewport_h: int) -> Tuple[int, int]:
        # Cell like "A1" or "AA12"
        cell = cell.strip().upper()
        # split letters and numbers
        i = 0
        while i < len(cell) and cell[i].isalpha():
            i += 1
        letters = cell[:i]
        row_part = cell[i:]
        try:
            row_num = int(row_part)
        except Exception:
            row_num = 1
        col_index = col_letters_to_index(letters)
        row_index = row_num - 1
        cw, ch = self.cell_size(viewport_w, viewport_h)
        x = int((col_index + 0.5) * cw)
        y = int((row_index + 0.5) * ch)
        return x, y

    def xy_to_cell(self, x: int, y: int, viewport_w: int, viewport_h: int) -> str:
        cw, ch = self.cell_size(viewport_w, viewport_h)
        col_index = min(max(int(x // cw), 0), self.cols - 1)
        row_index = min(max(int(y // ch), 0), self.rows - 1)
        col_letters = index_to_col_letters(col_index)
        return f"{col_letters}{row_index + 1}"

    def bbox_to_cell(self, bbox: Dict, viewport_w: int, viewport_h: int) -> str:
        x = bbox.get('x', 0) + bbox.get('w', 0) / 2
        y = bbox.get('y', 0) + bbox.get('h', 0) / 2
        return self.xy_to_cell(x, y, viewport_w, viewport_h)
