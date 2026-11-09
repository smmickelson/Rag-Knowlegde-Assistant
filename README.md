# Werk It Girls Networking Assessment — RAG Backend

A tool that reads answers to a 15-question networking quiz and writes
a personalized result in the Werk It Girls voice, grounded in a curated set
of coaching content — instead of matching to one of a handful of fixed
paragraphs.

## What it does

You answer 15 questions about how you network today. Instead of getting a
generic paragraph based on which bucket you land in, this app looks up the
coaching material that best matches your specific answers and writes a result
built for you. It's the engine behind the existing quiz at
tools.werkitgirls.com — this repo is the new part that writes the personalized
response; the quiz itself lives elsewhere and doesn't change.

## Screenshot

Coming with the alpha release.

<!-- Add one once you have something to show. -->

---

## Setup

**Everything a stranger needs, in order.** Test this by handing it to someone
and watching them. Every question they ask is a bug in this section.

### You will need

- Python 3.11 or newer
- A free GitHub account, to clone this repo

### Steps

```bash
# 1. Get the code
git clone https://github.com/smmickelson/Rag-Knowlegde-Assistant.git
cd Rag-Knowlegde-Assistant

# 2. Install what it needs
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Run it
streamlit run app.py
```

Your browser should open automatically to http://localhost:8501. If it doesn't, open that
address yourself.

### What you should see

- A page titled "What Kind of Networker Are You?" with 15 questions, each with four answer
  choices (Never, Occasionally, Frequently, Always).
- The Submit button stays greyed out until every question has an answer.
- After submitting, you'll see your networking style (e.g. "Connector") and tier (e.g. "Mid"),
  plus a line noting that personalized coaching text is coming soon.
- A Retake button that clears everything and lets you start over.

### If something doesn't work

- **"command not found: python3"** — try `python` instead of `python3`.
- **Nothing seems different after activating the virtual environment** — check that your
  terminal prompt now starts with `(.venv)`. If it doesn't, the activate command didn't run;
  try it again exactly as written above.
- **`pip install` fails or hangs** — check your Python version with `python3 --version`; it
  needs to be 3.11 or newer.
- **The browser says the page can't be reached** — check your terminal for an error message
  right after running `streamlit run app.py`; it usually explains what went wrong.
- **"Address already in use"** — you likely have another Streamlit app running already; close
  that terminal/tab first, or press Ctrl+C in it, then try again.

### Running the tests

```bash
pytest
```

Every test should pass. If one fails, that is the app telling you something is
broken. Read what it says before changing anything.

---

## Project status

**Current version:** alpha
**Working:** Answer all 15 questions and see your networking style and tier.
**Not working yet:** Personalized written coaching text based on your specific answers — see
[docs/backlog.md](docs/backlog.md) for what's planned next.

## How this project is organized

| Where | What's in it |
|---|---|
| [`docs/proposal.md`](docs/proposal.md) | The problem this solves and who it's for |
| [`docs/backlog.md`](docs/backlog.md) | Every feature, in build order, with its acceptance criteria |
| [`specs/`](specs/) | One page per feature: what it does, what it doesn't, what "done" means |
| [`AGENTS.md`](AGENTS.md) | The rules every AI assistant must follow in this repo |
| `src/` | The code |
| `tests/` | The automatic tests |
| [`CHANGELOG.md`](CHANGELOG.md) | What changed between versions |

## License

MIT. See [LICENSE](LICENSE).
