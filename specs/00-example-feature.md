<!-- A complete worked example. This is not part of your project. It is here to
     show you what a finished spec looks like after it has been through the
     question round and picked up one amendment from user testing.
     Read it, then delete it or leave it. It doesn't affect your app. -->

# 00 - Add an item to my list

**Story:** As a person keeping a list, I can add an item to it.
**Backlog item:** #00 (example)
**Status:** shipped

## What it does

There is a text box and an **Add** button at the top of the list. The user types
something, presses Add (or hits Enter), and the text appears at the bottom of the
list right away. The box clears itself and stays focused, so the user can type
the next item without reaching for the mouse. Items stay after the page is
closed and reopened.

## What it does NOT do

- No editing an item after it's added. That is feature #04.
- No deleting. That is feature #02.
- No categories, tags, due dates, or priorities. Not in this version.
- No syncing between devices. The list lives on the one device that made it.
- No undo.

## Acceptance criteria

- [x] Typing `Buy milk` and pressing **Add** makes `Buy milk` appear at the bottom of the list in under 1 second.
- [x] After adding, the text box is empty and still has the cursor in it.
- [x] Pressing **Enter** in the text box does the same thing as clicking **Add**.
- [x] Pressing **Add** with an empty box adds nothing and shows the message `Type something first`.
- [x] Pressing **Add** with only spaces in the box behaves exactly like an empty box.
- [x] An item 200 characters long is saved and displayed in full, wrapping onto more than one line.
- [x] Adding `Buy milk` twice results in two separate `Buy milk` lines.
- [x] Closing the page and reopening it shows every item that was added before.
- [x] Typing `<b>hi</b>` displays the literal text `<b>hi</b>`, not bold text.
- [x] After adding, the message `Saved` appears next to the box for 2 seconds. *(added by amendment, see below)*

## Question round

Questioner: second AI, 8 questions. Answered 2026-10-14.

| # | Question | Answer |
|---|---|---|
| 1 | What happens if the box is empty and they press Add? | Nothing is added; show `Type something first` next to the box. |
| 2 | What if the box contains only spaces or tabs? | Treat it exactly like empty: same message, nothing added. |
| 3 | Is there a maximum length for an item? | No hard limit. Long items wrap onto more lines. Don't truncate. |
| 4 | Are duplicate items allowed? | Yes. People really do need to buy milk twice. Don't warn, don't merge. |
| 5 | What if the user clicks Add twice very quickly? | Two clicks with text still in the box would add it twice, but the box clears on the first click, so the second click sees an empty box and does nothing. No extra work needed. |
| 6 | Do items survive closing the browser? | Yes. Save to the browser's own storage. No account, no server. |
| 7 | What if someone types HTML or a script tag? | Show it as plain text. Never run it. This is the one that becomes a security problem if we get it wrong. |
| 8 | Is there a maximum number of items? | No limit in this version. If storage ever fills up, that's a new backlog item. |

## Amendments

| Date | Change | Why |
|---|---|---|
| 2026-11-20 | Added acceptance criteria: `Saved` message appears for 2 seconds after adding. | Two of three user testers said they weren't sure the item had been saved, because the box clearing looked like the app had thrown their text away. Decision: build now. See `docs/feedback-log.md`, comments 4 and 9. |

## Notes

- Question 7 is the reason `tests/test_00_add_item.py` has a test about `<b>hi</b>`.
  Left alone, an AI will happily build a feature that runs whatever a user types.
- Question 5 is a good example of an answer that changed nothing. It still gets
  written down, so nobody spends twenty minutes on it again.
