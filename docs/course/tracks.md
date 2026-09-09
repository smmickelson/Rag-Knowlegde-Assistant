# Pick a track

This decides your language, how your tests run, and where your app is hosted.
Pick in week 3 and write it into `AGENTS.md` section 1 and `docs/proposal.md` section 3.

Switching later is possible but costs you a week. The specs, backlog, routine,
and every graded document are identical across all three; only `src/`, `tests/`,
and hosting differ.

---

## static-web: the default

**A website. No server. Works on a phone. Free to host.**

Choose this if your project is something a person opens and uses: a tracker, a
tool, a game, a visualizer, a quiz, a calculator.

| | |
|---|---|
| Language | HTML, CSS, JavaScript; no framework, no build step |
| Entry point | `index.html` in the repo root |
| Code | `src/app.js`, `src/styles.css` |
| Tests | [Playwright](https://playwright.dev/python/), drives a real browser |
| Run the app | Open `index.html`, or `python3 -m http.server` then visit `localhost:8000` |
| Run the tests | `pytest` |
| Hosting | GitHub Pages |
| Storage | The browser's own storage. No account, no database. |

Setup:

```bash
pip install pytest pytest-playwright
playwright install chromium
```

**Why no framework.** React and friends need a build step, a package manager, and
a folder of configuration, all of which break in ways a beginner can't diagnose,
none of which your project needs. Plain files load in a browser directly, and
every assistant on earth knows how to write them.

**The catch:** a static site cannot keep a secret. If your idea needs a hidden API
key, you need python-tool instead. See [`../deploying.md`](../deploying.md).

---

## python-tool

**A Python program. Real server-side code. Can keep a secret.**

Choose this if your project analyzes data, calls an API that requires a key, or
does real work on a file.

| | |
|---|---|
| Language | Python |
| Entry point | `app.py` (Streamlit) or `main.py` (command line) |
| Code | `src/*.py` |
| Tests | `pytest` |
| Run the app | `streamlit run app.py`, or `python main.py` |
| Run the tests | `pytest` |
| Hosting | Streamlit Community Cloud, or run locally |
| Storage | Files in `data/`, or SQLite |

Setup:

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Keep `requirements.txt` honest. Every package you install goes in it:

```bash
pip freeze > requirements.txt
```

An incomplete `requirements.txt` is the single most common reason a classmate
can't run your project in Stage 3. It works on your machine because you installed
something in September and forgot.

**Delete** `index.html`, `src/app.js`, and `src/styles.css` on this track.

**If your app has no web interface,** a tester runs it locally from your README.
That makes your setup steps the only thing between them and a working app. Test
them on a real person early.

---

## other

Anything else: a desktop app, a browser extension, a phone app, a different
language. Talk to the instructor first, not for permission, but so you don't
discover a wall in week 11.

Whatever you choose must supply four things, because the grading depends on them:

| | Why |
|---|---|
| **One command that runs the app** | Goes in your README. A stranger types it. |
| **One command that runs every test** | The routine and the sabotage demo both need it. |
| **Tests that can fail out loud** | If a break can't turn something red, it isn't a test. |
| **A way a peer can try it in Stage 3** | A URL, or setup steps they follow alone. |

Write all four into `AGENTS.md` section 5 so every assistant knows them.

---

## Not sure?

| If your project... | Track |
|---|---|
| is something people click around in | **static-web** |
| needs to work on a phone | **static-web** |
| crunches a spreadsheet or dataset | **python-tool** |
| calls an API that needs a secret key | **python-tool** |
| has no screen at all | **python-tool** (command line) |
| is none of the above | **other**: talk to the instructor |

When it's genuinely a toss-up, take **static-web**. Testers can open a link on
their phone, which means you get feedback on your app instead of on your install
instructions.
