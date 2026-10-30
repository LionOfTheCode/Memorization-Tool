from enum import Enum, auto
from typing import Iterator, Optional

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class FlashCard(Base):
    """
    Represents a flashcard entity for storing learning material in a database.

    This class is used to define the structure and behavior of a flashcard object. 
    It includes attributes for the flashcard's unique identifier, question, answer, 
    and its associated Leitner system class. Flashcards are commonly used in spaced 
    repetition systems to aid in learning and memory retention.

    :ivar id: Unique identifier for the flashcard.
    :type id: int
    :ivar question: The question or prompt associated with the flashcard.
    :type question: str
    :ivar answer: The answer or response associated with the flashcard.
    :type answer: str
    :ivar leitner_class: The flashcard's class in the Leitner system, 
        used to manage spaced repetition intervals.
    :type leitner_class: int
    """
    __tablename__ = 'flashcard'
    id = Column(Integer, primary_key=True)
    question = Column(String)
    answer = Column(String)
    leitner_class = Column(Integer)


class FlashCards:
    """
    Manages the functionality of a flashcard application.

    This class provides methods for managing different states of the application,
    handling user inputs, and interacting with the SQLite database to persist
    flashcards. It allows adding, updating, practicing, and rating flashcards
    through a state-driven workflow.

    :ivar state: Current state of the application. Represents different stages
        or menus in the flashcard application workflow.
    :type state: FlashCards.State

    :ivar engine: SQLAlchemy database engine for the flashcard database.
    :type engine: sqlalchemy.engine.base.Engine

    :ivar session: Active SQLAlchemy session for database operations.
    :type session: sqlalchemy.orm.session.Session

    :ivar flashcard_iterator: Iterator for cycling through loaded flashcards
        during the practice session.
    :type flashcard_iterator: Optional[Iterator[FlashCard]]

    :ivar current_flashcard: The currently selected flashcard during practice
        or editing modes.
    :type current_flashcard: Optional[FlashCard]

    :ivar flashcards: List of loaded flashcards available for practice.
    :type flashcards: Optional[list[FlashCard]]

    :cvar QUESTION_ANSWER_PROMPT: Standard prompt text for showing question-answer
        options during a practice session.
    :type QUESTION_ANSWER_PROMPT: str
    """

    class State(Enum):
        """
        Represents the various states used in the application.

        This Enum class defines all possible states that the application can transition
        through during its lifecycle. Each state corresponds to a specific operation or
        phase in the application workflow.

        :ivar MAIN_MENU: Represents the main menu state of the application.
        :ivar ADD_FLASHCARD_MENU: Represents the add flashcard menu state.
        :ivar PRACTISE_FLASHCARDS: Represents the state for practising flashcards.
        :ivar EXIT: Represents the exit state of the application.
        :ivar ENTER_QUESTION: Represents the state for entering a question during flashcard creation.
        :ivar ENTER_ANSWER: Represents the state for entering an answer during flashcard creation.
        :ivar UPDATE_QUESTION: Represents the state for updating the question in an existing flashcard.
        :ivar UPDATE_ANSWER: Represents the state for updating the answer in an existing flashcard.
        :ivar UPDATE_FLASHCARD: Represents the state for updating an entire flashcard (both question and answer).
        :ivar RATE_ANSWER: Represents the state for rating an answer during flashcard practice.
        """
        MAIN_MENU = auto()
        ADD_FLASHCARD_MENU = auto()
        PRACTISE_FLASHCARDS = auto()
        EXIT = auto()
        ENTER_QUESTION = auto()
        ENTER_ANSWER = auto()
        UPDATE_QUESTION = auto()
        UPDATE_ANSWER = auto()
        UPDATE_FLASHCARD = auto()
        RATE_ANSWER = auto()

    QUESTION_ANSWER_PROMPT = """press "y" to see the answer:\npress "n" to skip:\npress "u" to update:"""

    def __init__(self) -> None:
        self.state = self.State.MAIN_MENU

        self.pending_question = None

        self.flashcard_iterator = None
        self.current_flashcard = None

        self.engine = create_engine('sqlite:///flashcard.db?check_same_thread=False')
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

        self.flashcards = None

    def __del__(self) -> None:
        self.close()

    def close(self) -> None:
        """
        Closes the active session if it exists.

        This method checks for the presence of an active session attribute and
        closes it to release associated resources. It ensures that session
        resources are properly cleaned up.

        :return: None
        """
        session = getattr(self, "session", None)
        if session is not None:
            session.close()

    def _load_flashcards(self) -> list[FlashCard]:

        """
        Retrieves and loads all flashcards from the database.

        This method queries the `FlashCard` table in the database using the current 
        session and retrieves all available flashcards. If there are no flashcards in 
        the database, an empty list is returned.

        :return: A list of all flashcards retrieved from the database. If no 
            flashcards exist, returns an empty list.
        :rtype: list
        """
        card_list = self.session.query(FlashCard).all()
        if len(card_list) == 0:
            return list()
        return card_list

    def user_prompt(self) -> str:
        """
        Provides user prompts based on the current application state.

        The method evaluates the current state of the application and returns 
        a corresponding string prompt to guide the user interaction. Each application 
        state has a specific prompt to communicate the next expected action.

        :return: A string prompt corresponding to the current application state.
        :rtype: str
        """
        match self.state:
            case self.State.MAIN_MENU:
                return "1. Add flashcards\n2. Practice flashcards\n3. Exit"
            case self.State.ADD_FLASHCARD_MENU:
                return "1. Add a new flashcard\n2. Exit"
            case self.State.PRACTISE_FLASHCARDS:
                return f"Question: {self.current_flashcard.question}:\n{self.QUESTION_ANSWER_PROMPT}"
            case self.State.ENTER_QUESTION:
                return "Question:"
            case self.State.ENTER_ANSWER:
                return "Answer:"
            case self.State.UPDATE_FLASHCARD:
                return """press "d" to delete the flashcard:\npress "e" to edit the flashcard:"""
            case self.State.UPDATE_QUESTION:
                return f"current question: {self.current_flashcard.question}\nplease write a new question:"
            case self.State.UPDATE_ANSWER:
                return f"current answer: {self.current_flashcard.answer}\nplease write a new answer:"
            case self.State.RATE_ANSWER:
                return """press "y" if your answer is correct:\npress "n" if your answer is wrong:"""

    def process_input(self, user_input: str) -> Optional[str]:
        """
        Processes the user's input based on the current state of the application.

        This method evaluates the current state of the application and delegates
        the handling of the input to the appropriate method corresponding to
        the specific state. Depending on the state, the method may return a result,
        modify internal data, or perform certain application-specific operations.

        :param user_input: The user input to be processed.
        :return: The processed result or None, depending on the state and handler execution.
        :rtype: Any
        """
        match self.state:
            case self.State.MAIN_MENU:
                return self._handle_main_menu(user_input)
            case self.State.ADD_FLASHCARD_MENU:
                return self._handle_add_flashcard_menu(user_input)
            case self.State.PRACTISE_FLASHCARDS:
                return self._handle_practise_flashcards(user_input)
            case self.State.ENTER_QUESTION:
                self._handle_enter_question(user_input)
            case self.State.ENTER_ANSWER:
                self._handle_enter_answer(user_input)
            case self.State.UPDATE_FLASHCARD:
                self._handle_update_flashcard(user_input)
            case self.State.UPDATE_QUESTION:
                self._update_current_flashcard_question(user_input)
            case self.State.UPDATE_ANSWER:
                self._update_current_flashcard_answer(user_input)
            case self.State.RATE_ANSWER:
                self._rate_current_flashcard_answer(user_input)

            case self.State.EXIT:
                pass

    def _handle_main_menu(self, user_input: str) -> Optional[str]:
        """
        Handles input for the main menu and transitions the application to the appropriate
        state or returns messages based on user input.

        :param user_input: Input string provided by the user from the main menu options
        :return: A message to be displayed to the user when there is no flashcard to 
                 practice or when the input is invalid. None is returned for valid 
                 transitions without any message.
        """
        match user_input:
            case "1":
                self.state = self.State.ADD_FLASHCARD_MENU
            case "2":
                self.flashcards = self._load_flashcards()
                if len(self.flashcards) == 0:
                    return "There is no flashcard to practice!"  # stays in MAIN_MENU

                self.flashcard_iterator = iter(self.flashcards)  # iterates over the questions
                self._next_flashcard()  # loads the FIRST question
                self.state = self.State.PRACTISE_FLASHCARDS
            case "3":
                self.state = self.State.EXIT
            case _:
                return self._invalid_input(user_input)

    def _handle_add_flashcard_menu(self, user_input: str) -> Optional[str]:
        """
        Handles user input for the "Add Flashcard" menu. Depending on the input,
        updates the current state of the application or returns a response for 
        invalid input.

        :param user_input: The user's input as a string. Possible values are "1", "2", 
            or any other value considered invalid.
        :type user_input: str
        :return: A string indicating an error message for invalid input, or None 
            if the state is successfully updated.
        :rtype: Optional[str]
        """
        match user_input:
            case "1":
                self.state = self.State.ENTER_QUESTION
            case "2":
                self.state = self.State.MAIN_MENU
            case _:
                return self._invalid_input(user_input)

    def _handle_practise_flashcards(self, input: str) -> Optional[str]:
        match input:
            case "y":
                answer = f"Answer: {self.current_flashcard.answer}"
                self.state = self.State.RATE_ANSWER
                return answer
            case "n":
                self._next_flashcard()
            case "u":
                self.state = self.State.UPDATE_FLASHCARD
            case _:
                return self._invalid_input(input)

    def _handle_update_flashcard(self, user_input: str) -> Optional[str]:
        """
        Handles the user input for updating flashcards.

        This method processes the user input to determine the appropriate 
        action such as deleting the current flashcard, updating its question, 
        or handling invalid input.

        :param user_input: The input provided by the user to indicate the desired 
            operation on the flashcard.
        :return: Returns an optional string indicating invalid input if the input 
            does not match any expected case. Otherwise, returns None.
        """
        match user_input:
            case "d":
                self._delete_current_flashcard()
                self._next_flashcard()

            case "e":
                self.state = self.State.UPDATE_QUESTION

            case _:
                return self._invalid_input(user_input)

    def _next_flashcard(self) -> None:
        """
        Advances the flashcard iterator to the next flashcard or switches to the 
        main menu state if there are no more flashcards.

        This method attempts to fetch the next flashcard from the iterator and 
        updates the current flashcard and application state accordingly. If the
        iterator reaches the end, it sets the current flashcard to None and 
        changes the application state to MAIN_MENU.

        :return: None
        """
        try:
            self.current_flashcard = next(self.flashcard_iterator)
            self.state = self.State.PRACTISE_FLASHCARDS
        except StopIteration:
            self.current_flashcard = None
            self.state = self.State.MAIN_MENU

    def _handle_enter_question(self, user_input: str) -> None:
        """
        Handles the processing of user input when entering a question. 

        This function verifies if the provided user input is not empty, updates the 
        `pending_question` attribute with the input, and transitions the state 
        to `ENTER_ANSWER` if applicable.

        :param user_input: The input string provided by the user.
        :type user_input: str
        :return: None
        :rtype: None
        """
        if user_input.strip() == "":
            return None
        self.pending_question = user_input
        self.state = self.State.ENTER_ANSWER

    def _handle_enter_answer(self, user_input: str) -> None:
        """
        Processes the user input for the pending question, creates a new flashcard, and updates
        the system state accordingly. If the input is an empty string, the function exits without 
        making changes.

        :param user_input: The user's answer to the pending question. Must be a non-empty string.
        :type user_input: str
        :return: None
        """
        if user_input.strip() == "":
            return None

        new_flashcard = FlashCard(question=self.pending_question, answer=user_input, leitner_class=1)
        self.session.add(new_flashcard)
        self.session.commit()
        self.pending_question = None
        self.state = self.State.ADD_FLASHCARD_MENU

    def _invalid_input(self, user_input: str) -> str:
        """
        Constructs a formatted message indicating that the provided input is not 
        a valid option.

        :param user_input: The input provided by the user.
        :type user_input: str
        :return: A formatted string indicating the input is invalid.
        :rtype: str
        """
        return f"{user_input} is not an option"

    def _delete_current_flashcard(self) -> None:
        """
        Deletes the currently selected flashcard from the database and commits the 
        transaction.

        :raises OperationalError: If there is an issue with the database connection 
                                  or the commit operation.
        :return: None
        """
        self.session.delete(self.current_flashcard)
        self.session.commit()

    def _update_current_flashcard_question(self, user_input: str) -> None:
        """
        Updates the current flashcard's question if the input is provided and changes
        the state to UPDATE_ANSWER.

        :param user_input: The new question for the current flashcard. Must be a non-empty string.
        :type user_input: str
        """
        if user_input:
            self.current_flashcard.question = user_input
        self.state = self.State.UPDATE_ANSWER

    def _update_current_flashcard_answer(self, user_input: str) -> None:
        """
        Updates the answer for the current flashcard and progresses to the next flashcard 
        in the session.

        :param user_input: The answer to be updated for the current flashcard.
        :type user_input: str
        :return: None
        """
        if user_input:
            self.current_flashcard.answer = user_input
        self.session.commit()
        self._next_flashcard()

    def _rate_current_flashcard_answer(self, user_input: str) -> Optional[str]:
        """
        Processes the user's input to rate the correctness of the current flashcard's answer and updates
        its Leitner class accordingly. Handles moving the flashcard to the next class, demoting it, or
        removing it if it exceeds the maximum class.

        :param user_input: User input indicating whether the current flashcard's answer was correct ('y')
                      or incorrect ('n').
        :returns: A message indicating invalid input if the input is not 'y' or 'n', or None
                  upon successful processing.
        """
        if user_input.strip() not in ["y", "n"]:
            return self._invalid_input(user_input)
        if user_input == "y":
            self.current_flashcard.leitner_class += 1
        elif user_input == "n":
            if self.current_flashcard.leitner_class > 1:
                self.current_flashcard.leitner_class -= 1

        if self.current_flashcard.leitner_class > 3:
            self._delete_current_flashcard()
        else:
            self.session.commit()
        self.state = self.State.PRACTISE_FLASHCARDS
        self._next_flashcard()


if __name__ == "__main__":
    flashcards = FlashCards()
    while flashcards.state != FlashCards.State.EXIT:
        print(flashcards.user_prompt())
        response = flashcards.process_input(input())
        if response is not None:
            print(response)
    print("Bye!")
