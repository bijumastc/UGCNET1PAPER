"""A tiny in-memory stand-in for gspread, so the Google Sheet code can be tested offline."""
import re


def _a1(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return int(m.group(2)), col


class FakeWorksheet:
    def __init__(self, title):
        self.title = title
        self.cells = []          # list of rows (lists of str)
        self.calls = 0
        self.col_count = 26

    def add_cols(self, n):
        self.col_count += n

    def _ensure(self, r):
        while len(self.cells) < r:
            self.cells.append([])

    def row_values(self, i):
        self.calls += 1
        return list(self.cells[i - 1]) if i <= len(self.cells) else []

    def get_all_values(self):
        self.calls += 1
        return [list(r) for r in self.cells]

    def update(self, values, rng, value_input_option=None):
        self.calls += 1
        r0, c0 = _a1(rng.split(":")[0])
        for dr, row in enumerate(values):
            self._ensure(r0 + dr)
            line = self.cells[r0 + dr - 1]
            while len(line) < c0 - 1 + len(row):
                line.append("")
            for dc, v in enumerate(row):
                line[c0 - 1 + dc] = "" if v is None else str(v)

    def append_rows(self, rows, value_input_option=None):
        self.calls += 1
        for row in rows:
            self.cells.append(["" if v is None else str(v) for v in row])

    def batch_clear(self, ranges):
        self.calls += 1
        self.cells = self.cells[:1]


class FakeSpreadsheet:
    def __init__(self):
        self.sheets = {}

    def worksheets(self):
        return list(self.sheets.values())

    def add_worksheet(self, title, rows, cols):
        self.sheets[title] = FakeWorksheet(title)
        self.sheets[title].col_count = cols
        return self.sheets[title]


class FakeClient:
    def __init__(self):
        self.book = FakeSpreadsheet()

    def open_by_url(self, url):
        return self.book
