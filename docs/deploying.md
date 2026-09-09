<!-- Course: first needed for Stage 3 (alpha): a classmate has to reach your app
     without you in the room. See docs/course/DELIVERABLES.md -->

# Putting it online

Stage 3 requires a peer to set up and run your project on their own. Two ways to
pass that test: they run it locally from your README, or they open a URL. A URL
is better: fewer things go wrong, and you get feedback on the app instead of on
your install instructions.

Both options below are free.

---

## static-web track → GitHub Pages

Serves the files in your repo as a website. No server, no build step, no account
beyond GitHub.

1. Push your project to GitHub.
2. Repo → **Settings** → **Pages**.
3. Under **Source**, choose **Deploy from a branch**; pick `main` and `/ (root)`.
4. Save. A minute later your app is at
   `https://<your-username>.github.io/<your-repo>/`.

It redeploys itself every time you push to `main`.

**Requirements:** `index.html` must be in the repo root, and every path in it
must be relative (`src/app.js`, not `/src/app.js`; the leading slash breaks on
Pages). The repo must be public, unless you have GitHub Pro through the Student
Developer Pack.

---

## python-tool track → Streamlit Community Cloud

Runs an actual Python process, so your app can do things a static page can't,
including keeping a secret.

1. Your repo needs `requirements.txt` and a Streamlit entry point (`app.py`).
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub.
3. **New app**, pick your repo, branch, and the entry file.
4. Deploy. You get a URL you can hand to a tester.

It redeploys on every push.

**If your app is a command-line tool** with no web interface, it can't be
deployed this way; your peer will run it locally from your README instead. That
makes your setup instructions the *only* thing standing between them and a
working app, so test them on a real person early.

---

## other track

Whatever you use has to give a tester either a URL or a setup path they can
follow alone. Free options worth looking at: GitHub Pages, Streamlit Community
Cloud, Hugging Face Spaces, Netlify, Vercel, Render. Confirm the free tier is
genuinely free and doesn't ask a tester for a credit card.

Write down which one you chose and why in `docs/proposal.md` section 3.

---

## API keys, honestly

This is the part that goes wrong, so read it before your assistant writes code
that leaks a key into a public repo.

### Your assistant's key is not your app's key

The OpenRouter key you set up in week 1 belongs to **VS Code**, so that Kilo can
talk to a model while you work. It is not part of your project and never gets
committed. If an assistant proposes putting it in your repo, that's a bug.

### If your app itself calls an API

**On a server (Streamlit, python-tool):** a real secret is possible.
- Locally: put it in `.env`, already git-ignored.
- Deployed: paste it into Streamlit's **Secrets** panel in the dashboard. Never
  upload `.env`.

**On a static site: there is no such thing as a hidden key.** There is no server.
Every byte the page can read, a visitor can read: view-source, dev tools, done.
Nothing you can do in the code changes this. Minifying it doesn't. "Hiding" it in
a variable doesn't.

Two patterns that actually work:

1. **Use an API that doesn't need a key.** Plenty are free and open. This is the
   right answer most of the time.
2. **Ask the user for their own key** in the app, keep it in their browser's
   storage, and never send it anywhere but the API. Their key, their browser,
   their cost. Say clearly in your UI what you do with it.

If neither works for your idea, you need a server, which means the python-tool
track, not the static one. Better to find that out in week 5 than week 11.

### If you leak a key anyway

It happens. Do this immediately, in this order:

1. **Revoke the key** at the provider's dashboard. Do this first; it is the only
   step that actually stops the damage.
2. Issue a new one.
3. Remove it from the code and commit.

Deleting the commit is not sufficient. Git keeps history, GitHub keeps forks, and
scrapers find public keys within minutes. Assume any key that reached a public
repo is compromised forever. Revoke it.

GitHub scans public repos for known key formats and will usually block the push
before this can happen, but don't rely on it. It can't recognize every format.
