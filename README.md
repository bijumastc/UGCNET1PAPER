# UGC NET Paper 1 Trainer

A Streamlit app for UGC NET Paper 1 that learns from **your own** past papers and answer keys, and that
you can run for a whole class online.

**For students:** Learn cards for all 10 units (from zero → method → traps → scale up), practice from real NTA
questions, ♾️ unlimited generated practice with worked solutions (maths, logic, data interpretation, ICT),
teacher-approved AI questions for the theory units, diagnostic and full mock tests (5 questions per unit,
as in the syllabus), 🧪 simulators (Type I/II errors with a live power graph, a syllogism tester with Venn
diagrams, the square of opposition), a 🤖 AI tutor on free AI services (Groq, NVIDIA, Cerebras, OpenRouter, Mistral, with Gemini as backup) that checks facts on trusted websites (Tavily) and shows its sources, a "next focus" report, and a game layer: points, ranks, combos, daily missions, a ⚡ Speed round, a 🏆 Daily class challenge
(same 10 questions for everyone) and a weekly leaderboard, plus smiley encouragement, streaks and badges.

**For you (teacher):** student logins (ID + PIN), a class dashboard (status, projected scores, unit map,
"teach next" topics, one-student drill-down), every answer and a progress summary in a **Google Sheet**,
problem reports from students, and an AI question writer (paid Gemini or the free services) with a review queue.

- English only. No made-up past-paper answers: a question enters practice only when its answer is verified.
- Generated questions are calculated by the app, so their answers are always right.
- AI-written questions reach students only after you approve them.

**To put it online for students, follow [DEPLOY.md](DEPLOY.md).** The rest of this page covers using it
on your own computer.

**AI tutor on your computer:** open **⚙️ Class settings → AI tutor**, paste one or more free keys
(Groq, NVIDIA, Cerebras, OpenRouter, Mistral; see DEPLOY.md Part 3b), **Save**, then **🔌 Test every service**.

## 1. Install (once)

1. **Python 3.10 or newer**: https://www.python.org/downloads/ (on Windows, tick "Add Python to PATH").
2. **Tesseract OCR**: needed because NTA papers print questions as pictures.
   - Windows: install from https://github.com/UB-Mannheim/tesseract/wiki (default folder is fine; the app finds it).
   - macOS: `brew install tesseract`
   - Ubuntu: `sudo apt install tesseract-ocr`
3. In this folder, run:
   ```
   pip install -r requirements.txt
   ```

## 2. Put your papers in a folder

Put question papers and answer keys (PDF; keys can also be CSV/TXT) in one folder; subfolders are fine.

| You have | How answers are matched |
|---|---|
| NTA question paper + NTA final answer key | By **Question ID** (10–11 digit number). File names don't matter. |
| Paper + a coaching key listed by question number (1–50) | By **file name**: give the key the paper's name plus `Answer-Key`, e.g. `02-Sep-2024-Morning-Paper-1.pdf` and `02-Sep-2024-Morning-Paper-1-Answer-Key.pdf` |
| Paper with answers printed inside ("Ans.(b)") | Read from the paper itself. Memory-based papers are labelled as such and can be switched off in Settings. |

## 3. Run

Open Command Prompt in the app folder (in File Explorer, click the address bar, type `cmd`, press Enter).

**Read your papers once** (recommended; shows progress, can be stopped with Ctrl+C and resumed):
```
python scan_papers.py ..
```
`..` means the folder above the app, i.e. your papers folder if you extracted the app inside it.
Each NTA picture-paper takes about 1–3 minutes. Papers are read only once; later only new papers are read.

**Open the app** (any time, even before scanning; **Learn** works without any papers):
```
streamlit run app.py -- --folder ..
```
If you ran the scan while the app was open, click **↻ Reload** in the app.

## 4. What's inside

| Page | What it does |
|---|---|
| 🏠 Home | Projected Paper 1 score, what to do next, reviews due |
| 📂 Papers & checks | What each file is, how keys were matched, skipped questions with reasons, questions that need you to pick a unit, and a **spot-check** that shows a question beside its original page so you can confirm the answer yourself |
| 🔍 Patterns | Questions per unit and format, unit × format map, most-asked topics, a question bank by unit → topic → format, and questions **asked again in another session** |
| 📖 Learn | Each unit: overview, what your papers ask, a card per topic (**from zero → method → traps → scale up**) for maths, logic and DI, real example questions, and further resources |
| ✍️ Practice | Adaptive, by topic, by format, repeated questions, or review mistakes. Help comes in steps (strategy → concept → remove two options → show answer); each step lowers the credit. Instant feedback with the answer's source, worked solutions for series and coding questions, and the method to use next time |
| 📝 Tests | Diagnostic (2 per unit) and full 50-question mocks with 5 per unit, like the real paper |
| 📈 My gaps | Weak topics, weak question formats, speed, careless slips, help-dependence, untried topics, mastery by unit, all ranked by how often they appear in the exam |

**How questions are sorted.** The official syllabus sets **5 questions from each of the 10 units**,
and NTA prints Paper 1 as ten blocks of five in a fixed order. When a paper shows that layout,
each question's unit is taken from its block; keywords then choose the topic inside the unit. Other
papers (e.g. memory-based) are sorted by keywords, and anything unclear goes to *Needs review*. The
projected score and the mock test use the official 5-questions-per-unit weighting.

**How "verified" works.** A question enters practice only if: its English text was read; four options
were read, or the original image is shown; exactly one answer comes from a key or the paper; any
two sources agree; and the key didn't drop it. Scanned NTA questions are shown as the **original image**
from the paper, so OCR mistakes never reach you; OCR is used only for sorting.

**How scaffolding works.** Questions have three levels: recall → judging statements/relations →
multi-part (matching, sequencing, passages, data). In each topic you move up a level after about 70%
unaided accuracy. Mistakes come back after 10 minutes, then 1, 3 and 7 days.

**Corrections.** If a question is in the wrong unit or looks wrong, fix it or leave it out from the app.
Corrections are saved in `.p1_trainer/overrides.json` and survive re-scans.

## Excel export without the app

```
python sort_papers.py "C:\Users\you\Documents\NET Paper 1"
```
writes `paper1_sorted.xlsx` with every question sorted by unit and topic, a topic × format table,
repeated questions, and the skipped list.

## Putting it on GitHub

The `.gitignore` keeps your PDFs, progress and cache out of the repository. NTA and coaching papers
are copyrighted, so share the code, not the papers.
```
git init
git add .
git commit -m "Paper 1 trainer"
git branch -M main
git remote add origin https://github.com/<you>/ugc-net-paper1-trainer.git
git push -u origin main
```

## Tuning

- Topic keywords live in `p1/syllabus.py`; add words that your papers use often.
- Learn-card text is in `p1/learn.py`.
- Run the tests with `python -m pytest tests`.
