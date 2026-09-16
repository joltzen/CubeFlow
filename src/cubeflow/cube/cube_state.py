from cubeflow.cube.enums import Face, Turn
from cubeflow.cube.move import Move

Vector3 = tuple[int, int, int]

FACE_NORMALS: dict[Face, Vector3] = {
    Face.RIGHT: (1, 0, 0),
    Face.LEFT: (-1, 0, 0),
    Face.UP: (0, 1, 0),
    Face.DOWN: (0, -1, 0),
    Face.FRONT: (0, 0, 1),
    Face.BACK: (0, 0, -1),
}


def _turn_right(p: Vector3) -> Vector3:
    x, y, z = p
    return (x, z, -y)


def _turn_left(p: Vector3) -> Vector3:
    x, y, z = p
    return (x, -z, y)


def _turn_up(p: Vector3) -> Vector3:
    x, y, z = p
    return (-z, y, x)


def _turn_down(p: Vector3) -> Vector3:
    x, y, z = p
    return (z, y, -x)


def _turn_front(p: Vector3) -> Vector3:
    x, y, z = p
    return (y, -x, z)


def _turn_back(p: Vector3) -> Vector3:
    x, y, z = p
    return (-y, x, z)


_FACE_TURN_DATA = {
    Face.RIGHT: (0, 1, _turn_right),
    Face.LEFT: (0, -1, _turn_left),
    Face.UP: (1, 1, _turn_up),
    Face.DOWN: (1, -1, _turn_down),
    Face.FRONT: (2, 1, _turn_front),
    Face.BACK: (2, -1, _turn_back),
}

_TURN_REPEATS = {
    Turn.CLOCKWISE: 1,
    Turn.COUNTERCLOCKWISE: 3,
    Turn.DOUBLE: 2,
}


def _solved_cubies() -> dict[Vector3, dict[Vector3, Face]]:
    cubies: dict[Vector3, dict[Vector3, Face]] = {}

    for x in (-1, 0, 1):
        for y in (-1, 0, 1):
            for z in (-1, 0, 1):
                if x == 0 and y == 0 and z == 0:
                    continue

                position = (x, y, z)
                stickers: dict[Vector3, Face] = {}

                for face, normal in FACE_NORMALS.items():
                    if (
                        normal[0] * x > 0
                        or normal[1] * y > 0
                        or normal[2] * z > 0
                    ):
                        stickers[normal] = face

                cubies[position] = stickers

    return cubies


class CubeState:
    def __init__(self) -> None:
        self.cubies: dict[Vector3, dict[Vector3, Face]] = _solved_cubies()

    def get_sticker(self, position: Vector3, normal: Vector3) -> Face:
        return self.cubies[position][normal]

    def apply_move(self, move: Move) -> None:
        repeats = _TURN_REPEATS[move.turn]

        for _ in range(repeats):
            self._apply_quarter_turn(move.face)

    def _apply_quarter_turn(self, face: Face) -> None:
        axis_index, layer_value, transform = _FACE_TURN_DATA[face]

        affected = {
            position: stickers
            for position, stickers in self.cubies.items()
            if position[axis_index] == layer_value
        }

        for position in affected:
            del self.cubies[position]

        for position, stickers in affected.items():
            new_position = transform(position)

            new_stickers = {
                transform(normal): color
                for normal, color in stickers.items()
            }

            self.cubies[new_position] = new_stickers


def build_state(moves: list[Move]) -> CubeState:
    state = CubeState()

    for move in moves:
        state.apply_move(move)

    return state
