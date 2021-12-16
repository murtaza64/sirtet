from itertools import product
from lib import render_block
from tetrominoes import Tetromino, OrientedTetromino

HEIGHT = 20
WIDTH = 10

class GameOver(Exception):
    pass

class TetrisBoard:
    def __init__(self):
        self._board = [[0 for x in range(WIDTH)] for y in range(HEIGHT)]

    def __getitem__(self, slc) -> bool:
        try:
            ret = self._board[slc[1]][slc[0]]
        except IndexError:
            ret = 0
        return bool(ret)

    def __repr__(self):
        return 'TetrisBoard'

    def __str__(self):
        s = ''
        for row in reversed(self._board):
            for block in row:
                s += render_block(block)
            s += '\n'
        return s[:-1]

    def can_descend(self, ot : OrientedTetromino, bx, by):
        for x, y in product(range(4), repeat=2):
            # print(self[x, y], board[bx + x, by + y - 1])
            if ot[x, y] and self[bx + x, by + y - 1]:
                return False
        return True


    def place_tetromino(self, t : Tetromino, orientation, col):
        cur_y = HEIGHT
        ot = t[orientation]
        while cur_y > 0 and self.can_descend(ot, col, cur_y):
            cur_y -= 1
        if cur_y == HEIGHT:
            raise GameOver
        for x, y in product(range(4), repeat=2):
            if ot[x, y]:
                self._board[cur_y + y][col + x] = t.letter
        return cur_y
