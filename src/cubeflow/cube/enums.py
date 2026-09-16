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


INVERSE_TURN: dict[Turn, Turn] = {
    Turn.CLOCKWISE: Turn.COUNTERCLOCKWISE,
    Turn.COUNTERCLOCKWISE: Turn.CLOCKWISE,
    Turn.DOUBLE: Turn.DOUBLE,
}