from enum import Enum
import random
from typing import Any

import customtkinter as ctk


class SolveType(Enum):
    COMPLETE = "Completely"
    NEXT_DIGIT = "Until next digit"
    NEXT_REDUCTION = "Until next reduction"


class Difficulty(Enum):
    EASY = 0
    MEDIUM = 1
    HARD = 2
    EXTREME = 3


def get_difficulty_range(diff: Difficulty):
    match diff:
        case Difficulty.EASY:
            return random.randrange(39, 43)
        case Difficulty.MEDIUM:
            return random.randrange(34, 38)
        case Difficulty.HARD:
            return random.randrange(29, 33)
        case Difficulty.EXTREME:
            return random.randrange(19, 23)


class Algorithm:
    class GENERATING(Enum):
        FILLING = "Filling"
        REDUCING = "Reducing"

    class CLEARING(Enum):
        RESETTING = "Resetting"
        CLEARING = "Clearing"

    class SOLVING(Enum):
        ELIMINATION_BY_CONSTELLATION = "Elimination by constellation"
        ELIMINATION_BY_SUDOKU = "Elimination by sudoku"


class ValueLabel(ctk.CTkLabel):

    def __init__(self, init_text, master: Any, **kwargs):
        super().__init__(master, **kwargs)
        self._value = 0
        self.init_text = init_text
        self.configure(text=f"{init_text}: ")

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self.configure(text=f"{self.init_text}: {self.value}")
