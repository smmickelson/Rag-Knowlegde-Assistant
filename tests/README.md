# tests/

The automatic tests. One file per feature, named for the spec it tests:

```
specs/03-search-notes.md   →   tests/test_03_search_notes.py
```

**Every test traces back to a line in a spec's acceptance criteria.** If you can't point
at the line a test came from, either the spec is missing something or the test
is testing something nobody asked for.

Two rules that matter more than anything else in this folder:

1. Tests get written **before** the code they test, and they must fail first.
   A test that passes before the feature exists is testing nothing.
2. Once a test exists, **it does not get edited to make code pass.** If a test
   is genuinely wrong, change it deliberately, on purpose, and say why in the
   pull request.

Run them with the one command in your README. Delete this README once there are
real tests here.
