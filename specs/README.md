# Feature specs

One file per feature. This folder is where your app's real rulebook lives, not
in your head, and not in a chat window you closed.

## Naming

```
specs/
├── README.md               ← this file
├── TEMPLATE.md             ← copy this to start a new spec
├── 00-example-feature.md   ← a complete worked example; read it first
├── 01-<short-name>.md      ← your feature #1
├── 02-<short-name>.md      ← your feature #2
└── ...
```

**The number matches [`docs/backlog.md`](../docs/backlog.md).** Backlog item #3
is `specs/03-*.md` is branch `feature/03-*` is the tests for feature 3. One
number, all the way through. Keep it that way and you will never lose track of
what belongs to what.

## Starting a new spec

```bash
cp specs/TEMPLATE.md specs/03-search-my-notes.md
```

Then have an AI expand your one-line backlog item into the spec. Then run the
question round on it. Only then write tests.

## Specs change: that's the point

A spec is not a promise you made in September. It is the current truth about
what the feature does. It grows in three ways:

1. **The question round** (Stage 2) adds answers to things you hadn't considered.
2. **User feedback** (Stage 3) adds amendments when a classmate finds something.
3. **You change your mind**, which is allowed and expected.

Never delete an answer to make the spec shorter. The whole value is that a
question answered once never has to be argued again: by you, by a classmate, or
by an AI that shows up next week with no memory of the last conversation.
