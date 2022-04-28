import curses
import random
import logging
from time import sleep
from sys import stderr
import threading

from board import GameOver, TetrisBoard, WIDTH, HEIGHT
from tetrominoes import tetrominoes as tets, tetlist, Tetromino, OrientedTetromino
from lib import fullwidth, color_attrs
from state import TetrisGameState
from learn import TetrisQLearningAgent
from ui import UserInterface, default_curses_window_init
from game_runner import TetrisGameRunner

def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)


COL_KEYS = 'zxcvbnm,./'
COLOR_MAP = {
    'z': curses.COLOR_RED,
    'l': curses.COLOR_YELLOW,
    'o': curses.COLOR_YELLOW,
    's': curses.COLOR_GREEN,
    'j': curses.COLOR_BLUE,
    't': curses.COLOR_MAGENTA,
    'i': curses.COLOR_CYAN
}


logger = logging.getLogger(__file__)
hdlr = logging.FileHandler(__file__ + ".log")
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.DEBUG)

def main(stdscr):
    ui = UserInterface(*default_curses_window_init(stdscr), TetrisGameRunner, logger=logger)
    # ui.push_text('hello world!')
    try:
        ui.loop()
    except KeyboardInterrupt:
        curses.endwin()
        print('thank you for using sirtet!')

if __name__ == '__main__':
    curses.wrapper(main)
