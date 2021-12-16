import curses
import random
import logging
from sys import stderr
from board import TetrisBoard, HEIGHT, WIDTH
from tetrominoes import tetrominoes as tets, Tetromino, OrientedTetromino
from lib import fullwidth, horizontal_str, color_attrs

def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def curses_init():
    if not curses.has_colors():
        raise Exception
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(7, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_BLACK)

    color_attrs[0] =  curses.color_pair(8) | curses.A_BOLD
    color_attrs['z'] = curses.color_pair(1)
    color_attrs['l'] = curses.color_pair(3) | curses.A_BOLD
    color_attrs['o'] = curses.color_pair(3)
    color_attrs['s'] = curses.color_pair(2)
    color_attrs['j'] = curses.color_pair(4)
    color_attrs['t'] = curses.color_pair(5)
    color_attrs['i'] = curses.color_pair(6)

BRACKET_MAP = {
    'A': 'UP',
    'B': 'DOWN',
    'C': 'RIGHT',
    'D': 'LEFT'
}

def brackethandler(k, win):
    if k != '[':
        return k
    try:
        return BRACKET_MAP[win.getkey()]
    except KeyError:
        return '['


def game_iteration(b : TetrisBoard, score, tet : Tetromino, next_tet, board_win, cur_win,
        next_scr=None, kb_scr=None, info_scr=None):
    board_win.clear()
    b.draw(board_win)
    board_win.refresh()
    orient = 0
    col = 0

    while True:
        cur_win.clear()
        tet[orient].draw(cur_win, 0, col)
        cur_win.refresh()
        k = cur_win.get_wch()
        k = brackethandler(k, cur_win)
        logger.info(k)
        if k == ' ':
            break
        if k in ['a', 'LEFT'] and col > 0:
            col -= 1
        elif k in ['d', 'RIGHT'] and col < WIDTH - tet[orient].width:
            col += 1
        elif k in ['w', 'UP']:
            orient = (orient + 1) % tet.n_orientations()
            while col + tet[orient].width >= WIDTH:
                col -= 1
        logger.info('%s %s', col, orient)


    b.place_tetromino(tet, orient, col)
    board_win.clear()



logger = logging.getLogger(__file__)
hdlr = logging.FileHandler(__file__ + ".log")
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

def main(stdscr):
    

    curses_init()
    # Clear screen
    stdscr.clear()

    # board window
    height = HEIGHT * 2 + 1
    width = WIDTH * 2 + 1 #need one extra for newline i think
    # pylint: disable=no-member
    begin_x = (curses.COLS - width) // 2
    begin_y = 4
    board_win = curses.newwin(height, width, begin_y, begin_x)
    cur_win = curses.newwin(4, width, begin_y - 4, begin_x)

    b = TetrisBoard()
    b.draw(board_win)
    while True:
        tet = random.choice(list(tets.values()))
        game_iteration(b, 0, tet, None, board_win, cur_win)

    # b.draw(board_win)

    # board_win.refresh()
    # board_win.getkey()

    # board_win.clear()

    # b.place_tetromino(tets['s'], 0, 0)
    # b.place_tetromino(tets['t'], 1, 4)
    # b.draw(board_win)

    # board_win.refresh()
    # board_win.getkey()

    # stdscr.refresh()
    # stdscr.getkey()

if __name__ == '__main__':
    curses.wrapper(main)
