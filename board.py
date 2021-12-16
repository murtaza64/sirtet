import curses
from copy import deepcopy
from lib import render_block, render_block_curses, color_attrs
from tetrominoes import Tetromino, OrientedTetromino

HEIGHT = 20
WIDTH = 10
SCORE_MAP = [0, 40, 100, 300, 1200]

class GameOver(Exception):
    pass

class IllegalMove(Exception):
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

    def draw(self, scr, attrs=0):
        for i in range(HEIGHT):
            self.draw_line(scr, i, attrs)

    def copy(self):
        ret = TetrisBoard()
        ret._board = deepcopy(self._board)
        return ret


    def draw_line(self, scr, idx, attrs=0, autocolor=True):
        yi = HEIGHT - idx - 1
        x = 0
        row = self._board[idx]
        for block in row:
            render_block_curses(block, scr, y=yi, x=x, 
                    attrs=attrs, empty=not block, autocolor=autocolor)
            x += 2

    def preview(self, scr, tet : Tetromino, orient, col, remove=False):
        yi = HEIGHT - tet[orient].height - self.place_tetromino(tet, orient, col, dry_run=True)
        # self.draw(scr)
        if remove:
            tet[orient].draw(scr, yi, col, color_attrs[0], empty=True)
        else:
            tet[orient].draw(scr, yi, col, empty=True)
    
    def get_cleared_lines(self):
        clear_indexes = []
        for i, line in enumerate(self._board):
            if all(line):
                clear_indexes.append(i)
        return clear_indexes

    def remove_cleared_lines(self, clear_indexes):
        #start clearing from the top so that indexes don't get messed up
        for idx in reversed(clear_indexes):
            del self._board[idx]
            self._board.append([0 for x in range(WIDTH)])

    @staticmethod 
    def score(clear_indexes):
        return SCORE_MAP[len(clear_indexes)]
        
    def can_descend(self, ot : OrientedTetromino, bx, by):
        for x, y in ot.offsets():
            # print(self[x, y], board[bx + x, by + y - 1])
            if ot[x, y] and self[bx + x, by + y - 1]:
                return False
        return True

    def place_tetromino(self, t : Tetromino, orientation, col, dry_run=False):
        cur_y = HEIGHT
        ot = t[orientation]
        while cur_y > 0 and self.can_descend(ot, col, cur_y):
            cur_y -= 1
        if dry_run:
            return cur_y
        for x, y in ot.offsets():
            if ot[x, y]:
                if col + x >= WIDTH:
                    raise IllegalMove
                if cur_y + y >= HEIGHT:
                    raise GameOver
                self._board[cur_y + y][col + x] = t.letter
        return cur_y