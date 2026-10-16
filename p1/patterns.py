"""Question formats used by NTA, their solving strategies, and scaffold levels.

Level 1 = recall a single fact; Level 2 = judge several statements or a relationship;
Level 3 = multi-part matching/ordering or reading a passage/data set.
"""
import re

PATTERNS = [
    {"id": "assertion_reason", "name": "Assertion & Reason", "level": 2,
     "regex": [r"assertion\s*\(?\s*a\s*\)?", r"\breason\s*\(?\s*r\s*\)?\s*:"],
     "strategy": "Judge A alone (true/false), then R alone. Only if both are true, test the link: say "
                 "'A is true BECAUSE R'. If the sentence makes sense, R explains A; otherwise it does not."},
    {"id": "statement_i_ii", "name": "Statement I & Statement II", "level": 2,
     "regex": [r"statement\s*[-–]?\s*(i|1)\b\s*[:\-]?.*statement\s*[-–]?\s*(ii|2)\b"],
     "strategy": "Mark each statement True or False on its own, then pick the option with exactly that pair. "
                 "Do not look for a link between them: NTA asks only about truth here."},
    {"id": "match_list", "name": "Match List I with List II", "level": 3,
     "regex": [r"list\s*[-–]?\s*i\b.*list\s*[-–]?\s*ii\b", r"\bmatch\b.*\bwith\b", r"match the following"],
     "strategy": "Fix the one pair you are surest of and strike out every option that disagrees. A second "
                 "certain pair usually leaves one option. You rarely need all four pairs."},
    {"id": "sequence", "name": "Arrange in correct sequence", "level": 3,
     "regex": [r"chronolog", r"correct sequence", r"\barrange\b", r"correct order", r"\bsequence of\b",
               r"(ascending|descending) order"],
     "strategy": "Find the item that must come first and the one that must come last. Check which options "
                 "have both in place; the middle order is often decided already."},
    {"id": "multi_statement", "name": "Which statements are correct (A, B, C...)", "level": 2,
     "regex": [r"which of the (above|following|given) statements?", r"choose the (most )?(correct|appropriate) "
               r"answer from the options given below", r"\b[a-e]\s*,\s*[b-e]\s+and\s+[c-e]\s+only\b",
               r"\b[a-e]\s+and\s+[b-e]\s+only\b", r"\bidentify the correct\b.*\bstatements?\b"],
     "strategy": "Go through A, B, C... marking each True/False. Start with the statement you are surest of "
                 "and eliminate options right away. One sure 'False' removes about half the options."},
    {"id": "passage", "name": "Passage-based comprehension", "level": 3,
     "regex": [r"read the (following |given )?passage", r"according to the passage", r"based on the passage",
               r"the passage (suggests|implies|states|says)", r"according to the author", r"in the passage"],
     "strategy": "Read the question first, then find the lines that answer it. Answer only from the passage, "
                 "not from your own knowledge. Watch for options that are true in life but not stated."},
    {"id": "data_interpretation", "name": "Data interpretation (table/chart)", "level": 3,
     "regex": [r"the following table", r"given table", r"table (below|given)", r"(bar|line) (graph|chart|diagram)",
               r"pie (chart|diagram)", r"study the (table|chart|graph|data|following)", r"the following data"],
     "strategy": "Write down exactly which rows/columns the question needs before calculating. Estimate first "
                 "(round numbers) to drop impossible options; calculate exactly only to split close ones."},
    {"id": "numerical", "name": "Calculation / series problem", "level": 2,
     "regex": [r"\bseries\b", r"next (number|term)", r"missing (number|term)", r"\binterest\b", r"\bspeed\b",
               r"\bratio\b", r"\bper\s*cent", r"%", r"years (ago|hence)", r"\d+\s*,\s*\d+\s*,\s*\d+", r"\baverage\b",
               r"\bprofit\b", r"\bcoded as\b", r"\bvalue of\b", r"=\s*\d", r"\bequation"],
     "strategy": "Write the information as numbers before doing anything. For series: check differences, then "
                 "differences of differences, then ratios, then squares/cubes. You can also test each option "
                 "against the pattern instead of solving from scratch."},
    {"id": "negative", "name": "NOT / EXCEPT / incorrect", "level": 2,
     "regex": [r"\bnot\b[^.]*\?", r"\bnot\b[^.]*:\s*$", r"\bexcept\b", r"\bincorrect(ly)?\b", r"\bodd one\b",
               r"\bfalse\b", r"\bwrong(ly)?\b", r"\bnot (true|correct|a|an)\b"],
     "strategy": "Circle the NOT. Then go through the options and mark each one 'fits' or 'doesn't fit'. "
                 "The single misfit is the answer. Most mistakes here come from missing the NOT."},
    {"id": "concept_origin", "name": "Who proposed / associated with", "level": 2,
     "regex": [r"\bcoined\b", r"\bproposed by\b", r"\bassociated with\b", r"\bpropounded\b", r"\bgiven by\b",
               r"\bdeveloped by\b", r"\bwho (proposed|gave|introduced|developed)\b"],
     "strategy": "Link the idea to its field or school first (e.g. levels of teaching → Herbart, Morrison, Hunt). "
                 "That narrows the options to the right group of names."},
    {"id": "definition", "name": "Definition / identification", "level": 1,
     "regex": [r"\brefers to\b", r"\bis called\b", r"\bis known as\b", r"\bis termed\b", r"\bdefined as\b",
               r"\bfull form\b", r"\bstands for\b", r"\bexpansion of\b", r"\bis an example of\b", r"\bmeans\b",
               r"\bwhat is\b"],
     "strategy": "Say the definition to yourself before reading the options, then pick the closest match. "
                 "Distractors are usually near-synonyms or related terms from the same unit."},
    {"id": "direct_fact", "name": "Direct factual recall", "level": 1, "regex": [],
     "strategy": "Recall-based. If unsure, remove options from the wrong time, place or field, then decide "
                 "between the rest."},
]

PATTERN_BY_ID = {p["id"]: p for p in PATTERNS}
_COMPILED = [(p["id"], [re.compile(r, re.I | re.S | re.M) for r in p["regex"]]) for p in PATTERNS]


def detect_pattern(text: str) -> str:
    for pid, regs in _COMPILED:
        if any(r.search(text) for r in regs):
            return pid
    return "direct_fact"


def pattern_name(pid: str | None) -> str:
    return PATTERN_BY_ID.get(pid or "", {"name": pid or "—"})["name"]


def pattern_strategy(pid: str | None) -> str:
    return PATTERN_BY_ID.get(pid or "", PATTERN_BY_ID["direct_fact"])["strategy"]


def pattern_level(pid: str | None) -> int:
    return PATTERN_BY_ID.get(pid or "", PATTERN_BY_ID["direct_fact"])["level"]


LEVEL_NAMES = {1: "Level 1 · Recall", 2: "Level 2 · Judge & relate", 3: "Level 3 · Multi-part / data"}
