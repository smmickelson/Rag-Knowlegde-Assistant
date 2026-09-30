# Werk It Girls Networking Assessment — RAG Backend

A tool that reads a woman's answers to a 15-question networking quiz and writes
her a personalized result in the Werk It Girls voice, grounded in a curated set
of coaching content — instead of matching her to one of a handful of fixed
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
- A TensorX API key — sign up at [app.tensorx.ai](https://app.tensorx.ai). A
  payment method is required at sign-up, but usage for this app is
  negligible — a few cents per test run. Generate a key under **API Keys**.

### Steps

```bash
# 1. Get the code
git clone https://github.com/smmickelson/Rag-Knowlegde-Assistant.git
cd Rag-Knowlegde-Assistant

# 2. Install what it needs
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Set your API key
cp .env.example .env
# then open .env and paste in your TensorX key — never commit this file

# 4. Run it
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

### Running the tests

```bash
pytest
```

Every test should pass. If one fails, that is the app telling you something is
broken. Read what it says before changing anything.

---

## Project status

**Current version:** pre-alpha
**Working:** nothing yet
**Not working yet:** see [docs/backlog.md](docs/backlog.md)

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
