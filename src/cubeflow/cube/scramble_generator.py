import random

from cubeflow.cube.enums import Face, Turn
from cubeflow.cube.move import Move


class ScrambleGenerator:

    def generate(self, length: int = 20) -> list[Move]:
        moves: list[Move] = []

        previous_face: Face | None = None

        for _ in range(length):
            available_faces = [
                face
                for face in Face
                if face != previous_face
            ]

            face = random.choice(available_faces)
            turn = random.choice(list(Turn))

            move = Move(
                face=face,
                turn=turn,
            )

            moves.append(move)

            previous_face = face

        return moves