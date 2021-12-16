#pylint: disable=unused-import
import random
from board import GameOver, TetrisBoard, WIDTH, HEIGHT
from tetrominoes import tetrominoes as tets, tetlist, Tetromino, OrientedTetromino

class TetrisGameState:
    def __init__(self):
        self.score = 0
        self.board = TetrisBoard()
        self.tet_iq = list(range(7))
        random.shuffle(self.tet_iq)
        self.next_tet = tetlist[self.tet_iq.pop()]
        self.tet = tetlist[self.tet_iq.pop()]

    def next_tetromino(self):
        self.tet = self.next_tet
        try:
            self.next_tet = tetlist[self.tet_iq.pop()]
        except IndexError:
            self.tet_iq = list(range(7))
            random.shuffle(self.tet_iq)
            self.next_tet = tetlist[self.tet_iq.pop()]

    def make_move(self, orient, col) -> 'tuple[TetrisBoard, int, list[int]]':
        self.board.place_tetromino(self.tet, orient, col)
        cleared = self.board.get_cleared_lines()
        old_board = self.board.copy()
        if cleared:
            reward = self.board.score(cleared)
            self.board.remove_cleared_lines(cleared)
        else:
            reward = 0
        self.next_tetromino()
        return old_board, reward, cleared

    def get_moves(self):
        for orient in range(self.tet.n_orientations()):
            for col in range(WIDTH):
                if col + self.tet[orient].width <= WIDTH:
                    yield orient, col