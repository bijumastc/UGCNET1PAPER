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
