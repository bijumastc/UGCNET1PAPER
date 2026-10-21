"""Developer tests for the parsers and solvers. Run: python -m pytest tests

The small text fixtures here only exercise the parsing code; the app itself never uses
anything but your own papers.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from p1.classify import classify  # noqa: E402
from p1.extract import answers_from_qid_tokens, page_lines, parse_generic, parse_key, parse_nta  # noqa: E402
from p1.solvers import solve_coding, solve_number_series  # noqa: E402


def _pages(text):
    return [{"lines": [[l, None, None] for l in text.splitlines()], "ocr": False}]


def test_generic_with_inline_answers():
    text = """Q1. Grounded theory methodology was developed by:
(a) Sigmund Freud and Carl Jung
(b) Barney Glaser and Anselm Strauss
(c) Carl Rogers and Abraham Maslow
(d) Kurt Lewin and Jean Piaget
Ans.(b)
Q2. Minamata disease is caused due to toxicity of which element?
(a) As
(b) Cd
(c) Pb
(d) Hg
Ans.(d)
Q3. The table below shows data.
P 42 58% 5 : 4
Q 28 46% 7 : 3
(a) 1
(b) 2
(c) 3
(d) 4
Ans.(c)"""
    qs, issues = parse_generic(page_lines(_pages(text)))
    assert [q.qno for q in qs] == [1, 2, 3]          # "Q 28 46%" is a table row, not question 28
    assert [q.inline_answer for q in qs] == [1, 3, 2]
    assert all(len(q.options) == 4 for q in qs)


def test_nta_english_copy_and_option_ids():
    text = """Question Number : 1 Question Id : 61198712911 Question Type : MCQ
Which of the following is the capital of the ozone treaty discussion?
1. Montreal
2. Kyoto
3. Paris
4. Rio
Options :
61198750301. 1
61198750302. 2
61198750303. 3
61198750304. 4
Question Number : 1 Question Id : 61198712911 Question Type : MCQ
Tusatar Me fo get SIAM Hal e?
1. SATS
2. ORG
3. Udita
4. TAU
Options :
61198750301. 1
61198750302. 2
61198750303. 3
61198750304. 4"""
    qs, issues = parse_nta(page_lines(_pages(text)), set(), {})
    assert len(qs) == 1 and qs[0].options[0] == "Montreal"
    assert qs[0].option_ids[2] == "61198750303"
    ans = answers_from_qid_tokens(["61198712911", "61198750303"], {"61198712911": qs[0].to_dict()})
    assert ans == {"61198712911": [2]}


def test_coaching_key_two_columns_with_dropped():
    text = "Answer Key June 2024\n1 1 26\n1\n2 4 27\n1\n3 Dropped 28\n2\n" + \
           "".join(f"{n} 3 {n + 25}\n4\n" for n in range(4, 26))
    key = parse_key(text)["by_qno"]
    assert key[1] == 0 and key[26] == 0 and key[2] == 3 and key[3] == "DROP" and key[28] == 1 and len(key) == 50


def test_solvers_only_confirm_the_key():
    t = "What number would replace question mark (?) in the series given below? 1, 7, 16, 28, 43, 61, 82 ?"
    assert solve_number_series(t, ["102", "143", "106", "110"], 2)
    assert solve_number_series(t, ["102", "143", "106", "110"], 0) is None    # disagrees with key -> nothing shown
    c = "In a certain code language A is coded as Z, B is coded as Y, C is coded as X. How 'PERFECT' will be coded?"
    assert solve_coding(c, ["KVIUVXG", "KVIVUXG", "KVIUVGX", "KVUIVXG"], 0)


def test_classify_units():
    assert classify("Montreal Protocol is related to protection of.")["unit"] == "U9"
    assert classify("Which informal fallacy is committed in the following statement?")["unit"] == "U6"
    assert classify("Qualitative research makes use of.")["unit"] == "U2"
    assert classify("Who was asked", group_text="Read the passage. Life is about attachment and calm.")["unit"] == "U3"


def test_block_units_follow_paper_order():
    from p1.classify import block_units
    order = ["U7", "U1", "U2", "U4", "U5", "U6", "U8", "U9", "U10", "U3"]
    qs = []
    for n in range(1, 51):
        u = order[(n - 1) // 5]
        guess = "U9" if n % 5 == 1 else u            # one wrong guess in every block
        qs.append({"qno": n, "unit": None, "unit_guess": guess})
    assert block_units(qs) == dict(enumerate(order))
    assert block_units([{"qno": n, "unit": "U1"} for n in range(1, 51)]) is None   # not a block layout


def test_failed_read_is_retried(tmp_path, monkeypatch):
    import json as _json

    from p1 import library as L

    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 not really")
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / f"{L._sha(pdf)}_v{L.PARSER_VERSION}.json").write_text(_json.dumps(
        {"file": "paper.pdf", "role": "error", "error": "ModuleNotFoundError: No module named 'pdfplumber'"}))
    calls = []

    def fake_read(*a, **k):
        calls.append(1)
        raise RuntimeError("still broken")
    monkeypatch.setattr(L, "read_pdf", fake_read)
    rec = L.extract_file(pdf, cache)
    assert calls and "still broken" in rec["error"]                      # tried again, not the old error
    assert not (cache / f"{L._sha(pdf)}_v{L.PARSER_VERSION}.json").exists()   # the old failure is forgotten


def _lines(text):
    return [(1, l) for l in text.strip().splitlines()]


def test_passage_with_answers_and_explanations():
    from p1.extract import parse_generic

    text = """Q25. Which of the following is a primary source of data?
(1) Census report (2) Textbook (3) Encyclopaedia (4) Review article
Answer: (1)
Explanation: A census report is collected first-hand.
Read the following passage and answer the questions 26-28:
The river had always shaped the town. Farmers depended on its floods,
and traders on its calm months. When the dam came, both changed.
Q26. What shaped the town?
(1) The river (2) The dam (3) Traders (4) Farmers
Answer: (1)
Explanation: Stated in line one.
Q27. Who depended on the floods?
(1) Traders (2) Farmers (3) Engineers (4) Teachers
Answer: (2)
Q28. What changed both groups?
(1) Rain (2) Floods (3) The dam (4) Trade
Answer: (3)
Q29. Which of these is an input device?
(1) Monitor (2) Printer (3) Keyboard (4) Speaker
Answer: (3)"""
    qs, _ = parse_generic(_lines(text))
    by = {q.qno: q for q in qs}
    assert [q.qno for q in qs] == [25, 26, 27, 28, 29]
    assert "river had always shaped" in by[26].group_text and by[26].group_id == by[28].group_id
    assert by[27].group_text == by[26].group_text
    assert not by[29].group_text and not by[25].group_text
    assert "river" not in (by[25].explanation or "") and "river" not in by[25].options[3]
    assert by[27].inline_answer == 1


def test_passage_without_range_and_no_answers():
    from p1.extract import parse_generic

    text = """24. Which is NOT a feature of action research?
(1) Cyclic (2) Participative (3) Context-bound (4) Universal laws
Passage
Values education aims to build character. Schools play a central role,
but families and communities matter just as much.
25. What does values education aim to build?
(1) Wealth (2) Character (3) Speed (4) Memory
26. According to the passage, which of the following plays a central role in it?
(1) Schools (2) Banks (3) Courts (4) Markets"""
    qs, _ = parse_generic(_lines(text))
    by = {q.qno: q for q in qs}
    assert "Values education" in by[25].group_text and by[26].group_text == by[25].group_text
    assert "Values" not in by[24].options[3] and not by[24].group_text


def test_explanation_mentioning_a_table_is_not_a_passage():
    from p1.extract import parse_generic

    text = """Q5. The median of 2, 4, 6, 8, 10 is:
(1) 4 (2) 6 (3) 8 (4) 5
Answer: (2)
Explanation: Arrange the data in order.
Refer to the values: the middle one is 6.
Q6. What is 3 x 4?
(1) 7 (2) 12 (3) 34 (4) 1
Answer: (2)"""
    qs, _ = parse_generic(_lines(text))
    assert [q.qno for q in qs] == [5, 6] and not qs[1].group_text
