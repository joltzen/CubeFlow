from dataclasses import dataclass

from cubeflow.cube.enums import Face, Turn


@dataclass(frozen=True)
class Move:
    face: Face
    turn: Turn

    def __str__(self) -> str:
        return f"{self.face.value}{self.turn.value}"