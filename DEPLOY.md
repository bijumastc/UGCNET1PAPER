# Putting the Paper 1 Trainer online for your students

Allow about an hour the first time. You do everything once; afterwards, updating takes a few clicks.

```
Your computer                     GitHub (private)            Streamlit Cloud              Google Sheet
scan papers → make bundle  ──►    app code + bundle   ──►    the app students open  ◄──►  scores, progress,
                                                                                            students, AI questions
```

What you need: a **Google account** (Gmail), a **GitHub account** (free), and your scanned papers.

---

## Part 1: Prepare the questions on your computer

You have already scanned your papers. In Command Prompt, in the app folder:

```
python make_bundle.py ..
```

This creates a `bundle` folder inside the app folder: every question, its verified answer, and each scanned
NTA question as a small picture. Students never need the PDFs. Re-run it whenever you add papers.

> Before bundling, use **📂 Papers & checks** in the app on your computer to fix any question that needs a
> unit, or to leave out doubtful ones. Your corrections go into the bundle.

---

## Part 2: The Google Sheet (where all scores are saved)

### 2a. Create the sheet
1. Go to <https://sheets.google.com> and create a blank spreadsheet. Name it e.g. **Paper 1 Trainer – Class**.
2. Copy its address from the browser bar (it looks like `https://docs.google.com/spreadsheets/d/…/edit`).

The app creates the tabs itself. If your sheet was made by an older version, new tabs and columns are added
automatically and nothing is lost.

| Tab | What's in it |
|---|---|
| **Students** | The roster: ID, name, PIN, email, batch, active, joined, phone, notes (add phone/notes yourself) |
| **Attempts** | Every answer: time, student, the question text, their answer, the correct answer, right/wrong, help used, seconds taken, points, mode (practice / test / speed / challenge) |
| **Tests** | Every diagnostic, mock, speed round and daily challenge: marks, %, minutes, points, score per unit |
| **Activity** | Every login, logout and page visited, with time (used to work out time spent) |
| **AI_Chats** | Every AI tutor question and the full reply, with which AI answered |
| **AI_Questions** | Questions written by the AI, with your review status (pending / approved / rejected) |
| **Progress** | One row per student: status, logins, days active, minutes (total and this week), study sessions, answers, accuracy, tests, projected score, streak, points, rank, weakest unit, **top deficits**, help use, AI questions |
| **Unit_Scores** | Each student's mastery in all 10 units |
| Corrections, Reports, Settings | Your fixes to questions, students' problem reports, class settings |

Progress and Unit_Scores update by themselves: after every 10 answers, each test or round, each logout, and
whenever you open the Class dashboard. Don't type into those two tabs (the app rewrites them); add your own
notes in the Students tab or a new tab.

### 2b. Create a "robot" account that is allowed to write to the sheet
Google calls this a *service account*.
1. Open <https://console.cloud.google.com> and sign in with the same Google account.
2. At the top, click the project picker → **New project** → name it `paper1-trainer` → **Create**. Make sure
   it's selected.
3. Search for **Google Sheets API** in the top search bar → open it → **Enable**.
   Do the same for **Google Drive API**.
4. Menu ☰ → **IAM & Admin** → **Service accounts** → **Create service account**. Name: `trainer-bot` →
   **Create and continue** → **Done** (no roles needed).
5. Click the new service account → tab **Keys** → **Add key** → **Create new key** → **JSON** → **Create**.
   A `.json` file downloads. **Keep it private**; it is the robot's password.
6. Open that JSON file in Notepad and copy the `client_email` value (like
   `trainer-bot@paper1-trainer.iam.gserviceaccount.com`).
7. Back in your Google Sheet: **Share** → paste that email → give **Editor** → untick "Notify" → **Share**.

---

## Part 3: Gemini key (for AI-written questions)

1. Go to <https://aistudio.google.com> → **Get API key** → create a key (use your paid project).
2. Copy the key. Check the model names your account offers (a "flash" model is cheaper and enough);
   you can set the model name later in **⚙️ Class settings**.

## Part 3b: Free AI keys for the 🤖 AI tutor (all optional, more = smoother)

The tutor tries the services in this order. If one is busy, the next one answers automatically:
**Groq → NVIDIA → Cerebras → OpenRouter → Mistral → Groq (small model) → Gemini (your paid key, last resort)**.
You don't need all of them: two or three free keys are plenty for a class.
Each key takes about 2 minutes. None of the free ones asks for a card.

**1. Groq** (fastest, start here)
1. Open <https://console.groq.com> → **Sign in with Google**.
2. Left menu → **API Keys** (or <https://console.groq.com/keys>) → **Create API Key** → name it `paper1` → **Submit**.
3. Copy the key now (starts with `gsk_`; it is shown only once) and paste it into Notepad.

**2. Cerebras**
1. Open <https://cloud.cerebras.ai> → sign up with Google.
2. Left menu → **API Keys** → **Generate API key** → copy it (starts with `csk-`).

**2b. NVIDIA** (may offer Llama)
1. Open <https://build.nvidia.com> → **Login** → create a free NVIDIA Developer account with your email.
2. Open any model page (e.g. search "llama") → **Get API Key** → **Generate Key** → copy it (starts with `nvapi-`).
3. NVIDIA has been withdrawing free models (Oct 2026: Llama 3.3 70B shows "Free Endpoint: Deprecated").
   The app skips a withdrawn model automatically; if 🔌 Test says "no longer offered", pick a model marked
   **Free Endpoint** on build.nvidia.com and paste its name (e.g. `meta/...`) under ⚙️ Class settings → NVIDIA → Models.

**3. OpenRouter** (still lists a free Llama 3.3 70B)
1. Open <https://openrouter.ai> → **Sign in** with Google.
2. Top-right menu → **Keys** (or <https://openrouter.ai/keys>) → **Create Key** → name `paper1`, leave the
   credit limit empty → **Create** → copy it (starts with `sk-or-`).
3. Free models allow only about 50 requests a day on an account that has never bought credits. A one-time
   US$10 top-up raises this to about 1,000 a day (optional).

**3b. Mistral**
1. Open <https://console.mistral.ai> → sign up → choose the free **Experiment** plan (no card; a phone number
   is needed to verify).
2. **API Keys** → **Create new key** → copy it.
3. On the free plan Mistral may use requests to train its models. Students' tutor questions carry no names, but
   you can switch Mistral off in Class settings if you prefer.

**3c. Tavily (fact-checking web search, recommended)**
1. Open <https://app.tavily.com> → sign up (Google works). No card needed; the free plan gives 1,000 searches
   a month.
2. Your API key is shown on the dashboard (starts with `tvly-`). Copy it.
3. Add `tavily_api_key = "tvly-..."` to your secrets.
For fact-based topics (teaching, research, communication, ICT, environment, higher education, Indian logic) the
tutor first searches trusted sites (UGC, NTA, Ministry of Education, UNESCO, UN, Wikipedia…), answers from what
it finds and shows the links under its answer. Maths and logic questions are not searched. A class-wide daily
limit (default 30, in ⚙️ Class settings) keeps you inside the free plan; repeated questions cost nothing.
The AI question writer uses the same facts when it writes theory questions.

**4. Gemini (paid, already have it)**: the same `gemini_api_key` as Part 3. It is used only when all
the free ones are busy. Turn it off in **⚙️ Class settings → AI tutor → Gemini → Use** if you prefer.

Add the keys to your secrets (Part 4):

```toml
groq_api_key = "gsk_..."
nvidia_api_key = "nvapi-..."
cerebras_api_key = "csk-..."
openrouter_api_key = "sk-or-..."
mistral_api_key = "..."
```

Then in the app, open **⚙️ Class settings → 🔌 Test every service**. You want at least one ✅.

Good to know:
- Free limits (check each site; they change): Groq and Cerebras are about 30 requests a minute; Groq is about
  1,000 a day per model. The **questions per student per day** slider (default 30) keeps the class within them.
- Groq and Cerebras **no longer offer Llama free** (Groq withdrew it on 16 Aug 2026). They now run OpenAI's free
  open-weight model **gpt-oss-120b**, a strong free model for explanations. OpenRouter still lists free Llama.
- If a service renames a model, change it in **⚙️ Class settings → (service) → Models**; no new code needed.
- The AI can make mistakes. The official answer key is always in charge: the tutor is told to explain the
  official answer, and every question students ask is listed under **🏫 Class dashboard → 🤖 AI tutor use**.
- Ollama (AI on your own PC) is not used: it can't serve students online.

---

## Part 4: Your secrets file

In the app folder, `.streamlit/secrets.toml.example` shows the format. Fill it in (in Notepad) like this.
**Order matters: the Google key goes last.**

```toml
sheet_url = "https://docs.google.com/spreadsheets/d/XXXXXXXX/edit"
teacher_password = "choose-a-strong-password"
teacher_email = "you@gmail.com"          # optional: logs you in automatically online
gemini_api_key = "AIza..."              # optional
groq_api_key = "gsk_..."                # optional: free AI tutor keys (Part 3b)
nvidia_api_key = "nvapi-..."
openrouter_api_key = "sk-or-..."
mistral_api_key = "..."
tavily_api_key = "tvly-..."             # optional: fact-checking web search (Part 3c)

gcp_service_account_json = '''
{
  "type": "service_account",
  "project_id": "paper1-trainer",
  ... the whole downloaded JSON file, pasted exactly as it is ...
}
'''
```

Open the downloaded `.json` key file in Notepad, select everything (Ctrl+A), copy, and paste it between the two
`'''` lines (three **single** quotes). Nothing in it needs changing.

(The older way also works: a `[gcp_service_account]` heading followed by lines like `type = "service_account"`,
one per JSON field, without colons, commas or braces. Use one way, not both.)

**Never upload this file to GitHub.** The `.gitignore` already blocks `secrets.toml`; you will paste it into
Streamlit instead (Part 6).

---

## Part 5: Put the app on GitHub (private)

Easiest without commands: **GitHub Desktop** (<https://desktop.github.com>).

1. Sign in to <https://github.com> → **New repository** → name `paper1-trainer` → choose **Private** →
   **Create repository**.
2. Install GitHub Desktop, sign in, **File → Clone repository** → pick `paper1-trainer` → choose a location
   (e.g. `D:\GitHub`).
3. Copy **everything inside** the `p1_trainer` app folder (including the `bundle` folder and the hidden-looking
   `.gitignore` and `.streamlit` items) into that cloned folder. Your PDFs and the `.p1_trainer` scan folder are
   not inside the app folder, and `.gitignore` blocks PDFs, `secrets.toml` and key files anyway.
4. In GitHub Desktop: write a summary like "First upload" → **Commit to main** → **Push origin**.

Check on github.com that you see `app.py`, the `p1` folder and the `bundle` folder, and **no** `secrets.toml`.
The `bundle` folder holds only 2–3 files (`library.json` and `images_1.zip`, maybe `images_2.zip`), so it also
uploads fine through the GitHub website (**Add file → Upload files**, drag the `bundle` folder in).

---

## Part 6: Start the app on Streamlit Community Cloud

1. Go to <https://share.streamlit.io> → **Continue with GitHub** → allow access (including private repos).
2. **Create app** → **Deploy a public app from GitHub** (it will be private because the repository is private).
   - Repository: `your-name/paper1-trainer`, Branch: `main`, Main file: `app.py`
   - Pick an app address, e.g. `paper1-yourname`.
3. **Advanced settings** → choose **Python 3.12** if asked → paste your whole `secrets.toml` into **Secrets**
   → **Save** → **Deploy**. The first start takes a few minutes.
4. Open the app → **🧑‍🏫 Teacher** tab → your teacher password.

Your free plan allows one private app. If the app sleeps after a quiet spell, the first visitor clicks
the button to wake it (about a minute).

---

## Part 7: Add students and invite them

1. In the app: **👥 Students** → paste one per line `Name, email` → **Add**. Each student gets an ID and a PIN.
2. In Streamlit (share.streamlit.io): open your app's **⋮ → Settings → Sharing** (or the **Share** button on
   the app) → invite each student's **email** as a viewer. They receive an email link and sign in with Google.
3. Send each student their **Student ID and PIN** (the Students page shows a ready message to copy).
   If the email you invited matches the email in the Students list, they may be logged in automatically.

---

## Part 8: Daily use

- **🏫 Class dashboard**: each student's status (🟢 on track · 🟡 working · 🔴 inactive 3+ days), projected
  score, weakest unit, a class unit map, "teach next" topics, and one-student drill-down.
  Click **Update the Progress tab** to refresh the summary in your Google Sheet.
- **Google Sheet**: *Attempts* has every answer (time, student, unit, topic, right/wrong, help used, seconds);
  *Progress* has one row per student. Filter and chart them as you like.
- **📮 Reports** (in the dashboard): questions students flagged. Leave one out with one click.
- **🤖 AI questions**: choose unit, topic and format → **Write questions** → review each in **Review**
  → edit if needed → **Approve**. Only approved questions reach students.

## Updating

Added papers or corrected questions? On your computer: `python scan_papers.py .. --light`, then
`python make_bundle.py ..`, then copy the new `bundle` folder into the GitHub folder, then GitHub Desktop
**Commit** → **Push**. The online app updates itself within a minute or two. Students' scores are safe in
the Google Sheet.

## If something goes wrong

| What you see | What to do |
|---|---|
| "Could not open the Google Sheet" (teacher sidebar) | Check `sheet_url`, that the sheet is shared with the robot email as **Editor**, and that both APIs are enabled. |
| App says "Using local storage" online | The secrets weren't read. Recheck the Secrets box (TOML format, `[gcp_service_account]` section). |
| 🔌 Test shows ❌ key rejected | Check that key in Secrets (no spaces, inside quotes), or make a new one on that site. |
| "All the AI services are busy" | Every service hit its free limit. Add another key (Part 3b), or lower the daily limit per student. |
| Gemini error when writing questions | Check the key, and that the model name in Class settings exists in your AI Studio account. |
| A student can't log in | Check their ID/PIN in 👥 Students (🔑 New PIN), that they're Active, and that their email is invited in Streamlit Sharing. |
