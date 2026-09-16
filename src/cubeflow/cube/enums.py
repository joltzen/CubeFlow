from enum import Enum


class Face(Enum):
    UP = "U"
    DOWN = "D"
    LEFT = "L"
    RIGHT = "R"
    FRONT = "F"
    BACK = "B"


class Turn(Enum):
    CLOCKWISE = ""
    COUNTERCLOCKWISE = "'"
    DOUBLE = "2"