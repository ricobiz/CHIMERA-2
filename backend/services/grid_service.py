from dataclasses import dataclass
from typing import Tuple, Dict

@dataclass
class GridConfig:
    rows: int = 12
    cols: int = 8

    def cell_size(self, viewport_w: int, viewport_h: int) -> Tuple[float, float]:
        return viewport_w / self.cols, viewport_h / self.rows

    def cell_to_xy(self, cell: str, viewport_w: int, viewport_h: int) -> Tuple[int, int]:
        # Cell like "A1" (col letter, row number)
        col_letter = cell[0].upper()
        row_num = int(cell[1:])
        col_index = ord(col_letter) - ord('A')  # 0-based
        row_index = row_num - 1
        cw, ch = self.cell_size(viewport_w, viewport_h)
        x = int((col_index + 0.5) * cw)
        y = int((row_index + 0.5) * ch)
        return x, y

    def xy_to_cell(self, x: int, y: int, viewport_w: int, viewport_h: int) -> str:
        cw, ch = self.cell_size(viewport_w, viewport_h)
        col_index = min(max(int(x // cw), 0), self.cols - 1)
        row_index = min(max(int(y // ch), 0), self.rows - 1)
        col_letter = chr(ord('A') + col_index)
        return f"{col_letter}{row_index + 1}"

    def bbox_to_cell(self, bbox: Dict, viewport_w: int, viewport_h: int) -> str:
        x = bbox.get('x', 0) + bbox.get('w', 0) / 2
        y = bbox.get('y', 0) + bbox.get('h', 0) / 2
        return self.xy_to_cell(x, y, viewport_w, viewport_h)
