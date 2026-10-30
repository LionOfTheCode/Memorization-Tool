# Memorization Tool

A command-line flashcard application built with Python and SQLAlchemy. It uses a simplified [Leitner system](https://en.wikipedia.org/wiki/Leitner_system) for spaced repetition and stores flashcards in a local SQLite database.

## Features

- **Add flashcards**: create cards with a question and an answer. Empty input is ignored.
- **Practice flashcards**: go through all saved cards one at a time.
  - Reveal the answer (`y`), skip the card (`n`), or update it (`u`).
- **Update flashcards**: edit a card's question and answer, or delete the card. Leaving an input empty keeps the current value.
- **Leitner system**: each card has a class (box) that changes with your answers.
  - New cards start in class 1.
  - A correct answer moves the card up one class.
  - A wrong answer moves the card down one class, to a minimum of 1.
  - A card that moves above class 3 counts as learned and is deleted.
- **Persistent storage**: cards are saved in a SQLite database (`flashcard.db`) through SQLAlchemy.

## Requirements

- Python 3.10 or newer, because the code uses `match`/`case`.
- [SQLAlchemy](https://www.sqlalchemy.org/) 1.4 or newer

Install the dependency in your virtual environment:

```bash
pip install sqlalchemy
```

## Usage

Run the tool from the project root:

```bash
python task/tool.py
```

The database file `flashcard.db` is created in the current working directory on first launch.

### Main menu

```
1. Add flashcards
2. Practice flashcards
3. Exit
```

### Adding flashcards

```
1. Add a new flashcard
2. Exit
```

After choosing `1`, you are prompted for a `Question:` and then an `Answer:`.

### Practicing flashcards

For each card you see:

```
Question: <question>:
press "y" to see the answer:
press "n" to skip:
press "u" to update:
```

| Key | Action                                         |
|-----|------------------------------------------------|
| `y` | Show the answer, then rate yourself            |
| `n` | Skip to the next card                          |
| `u` | Open the update menu (delete or edit the card) |

After the answer is shown, rate yourself:

```
press "y" if your answer is correct:
press "n" if your answer is wrong:
```

In the update menu:

| Key | Action                                             |
|-----|----------------------------------------------------|
| `d` | Delete the flashcard                               |
| `e` | Edit the flashcard (new question, then new answer) |

## Project Structure

```
Memorization Tool
├── task
│   ├── tool.py          # Application source code
│   └── flashcard.db     # SQLite database
```

## How It Works

The application is built around two classes:

- **`FlashCard`** is the SQLAlchemy model for the `flashcard` table. It has the columns `id`, `question`, `answer` and `leitner_class`.
- **`FlashCards`** is a state machine that drives the CLI. Its `State` enum holds these states:
  `MAIN_MENU`, `ADD_FLASHCARD_MENU`, `ENTER_QUESTION`, `ENTER_ANSWER`, `PRACTISE_FLASHCARDS`, `UPDATE_FLASHCARD`, `UPDATE_QUESTION`, `UPDATE_ANSWER`, `RATE_ANSWER` and `EXIT`.

  Two methods drive the loop:
  - `user_prompt()` returns the text to show for the current state.
  - `process_input(input)` handles the user's input and moves to the next state.

## License

This project was created for educational purposes.
```