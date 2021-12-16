import curses
import random
import logging
from time import sleep
from sys import stderr
from board import GameOver, TetrisBoard, WIDTH, HEIGHT
from tetrominoes import tetrominoes as tets, tetlist, Tetromino, OrientedTetromino
from lib import fullwidth, color_attrs
class TetrisGameState:
    def __init__(self):
        self.score = 0
        self.board = TetrisBoard()
        self.next_tet = random.choice(tetlist)
        self.tet = random.choice(tetlist)
    
    def make_move(self, orient, col) -> 'tuple[TetrisBoard, int, list[int]]':
        self.board.place_tetromino(self.tet, orient, col)
        cleared = self.board.get_cleared_lines()
        old_board = self.board.copy()
        if cleared:
            reward = self.board.score(cleared)
            self.board.remove_cleared_lines(cleared)
        else:
            reward = 0
        self.tet = self.next_tet
        self.next_tet = random.choice(tetlist)
        return old_board, reward, cleared
        

class TetrisGameRunner:
    def __init__(self, board_win, cur_win, score_win, next_win, info_win, curses=True):
        self.state = TetrisGameState()
        self.orient = 0
        self.col = 0
        
        self.curses = curses
        if curses:
            self.board_win = board_win
            self.cur_win = cur_win
            self.score_win = score_win
            self.next_win = next_win
            self.info_win = info_win

    def iteration(self):
        self.board_win.clear()
        self.state.board.draw(self.board_win)
        self.board_win.refresh()
        
        self.draw_score()
        self.draw_next_tet()
        
        self.orient = 0
        self.col = 4
        while True:
            #draw cur self.state.tet
            ot : OrientedTetromino = self.state.tet[self.orient]
            self.cur_win.clear()
            ot.draw(self.cur_win, 4 - ot.height, self.col)
            self.cur_win.refresh()
            self.state.board.preview(self.board_win, self.state.tet, self.orient, self.col)
            self.board_win.refresh()

            if self.process_keypress():
                break
        
        old_board, reward, cleared = self.state.make_move(self.orient, self.col)
        if cleared:
            self.celebrate(old_board, reward, cleared)
            self.state.score += reward


    def clear_board_preview(self):
        self.state.board.preview(self.board_win, self.state.tet, self.orient, self.col, remove=True)

    def rotate(self):
        self.orient = (self.orient + 1) % self.state.tet.n_orientations()

    def process_keypress(self):
        k = self.cur_win.get_wch()
        k = brackethandler(k, self.cur_win)
        ot = self.state.tet[self.orient]
        # logger.info(k)
        if k == ' ':
            return True
        if k in ['a', 'LEFT'] and self.col > 0:
            self.clear_board_preview()
            self.col -= 1
        elif k in ['d', 'RIGHT'] and self.col < WIDTH - ot.width:
            self.clear_board_preview()
            self.col += 1
        elif k in ['w', 'UP']:
            self.clear_board_preview()
            self.rotate()
            while self.col + ot.width >= WIDTH:
                self.col -= 1

        #column controls:
        elif k in COL_KEYS:
            #repress
            self.clear_board_preview()
            if self.col == COL_KEYS.index(k):
                if self.col <= WIDTH - ot.height:
                    self.rotate()
                return False
            #new col
            self.col = COL_KEYS.index(k)
            if self.col > WIDTH - ot.width:
                #check rotation
                if ot.height < ot.width:
                    self.rotate()
                self.col = WIDTH - ot.width

        return False

    def celebrate(self, old_board, reward, cleared):
        self.board_win.clear()
        old_board.draw(self.board_win)
        scorestr = str(reward)
        rewardstr =  '+ ' + ' '*(4-len(scorestr)) + scorestr
        for _ in range(4):
            for idx in cleared:
                old_board.draw_line(self.board_win, idx, curses.A_STANDOUT)
                self.board_win.refresh()
            self.score_win.addstr(2, 0, rewardstr, curses.color_pair(6))
            self.score_win.refresh()
            sleep(0.1)
            for idx in cleared:
                old_board.draw_line(self.board_win, idx, 0)
                self.board_win.refresh()
            self.score_win.addstr(2, 0, rewardstr)
            self.score_win.refresh()
            sleep(0.1)

    def draw_score(self):
        self.score_win.clear()
        self.score_win.addstr('score:')
        self.score_win.addstr(1, 0, f'{self.state.score:06d}')
        self.score_win.refresh()

    def draw_next_tet(self):
        self.next_win.clear()
        self.next_win.addstr('next:')
        self.state.next_tet[0].draw(self.next_win, 1, 0)
        self.next_win.refresh()

    def game_over(self):
        self.info_win.clear()
        self.info_win.addstr(1, 10, ' '*WIDTH*2, curses.color_pair(10))
        self.info_win.addstr(2, 10, '    game over :(    ', curses.color_pair(10))
        self.info_win.addstr(3, 10, f'    score: {self.state.score:06d}   ', curses.color_pair(10))
        self.info_win.addstr(4, 10, ' '*WIDTH*2, curses.color_pair(10))
        self.info_win.refresh()

    def run(self):
        draw_controls(self.info_win)
        #one iteration after which we clear controls
        self.iteration()
        self.info_win.clear()
        self.info_win.refresh()
        while True:
            try:
                self.iteration()
            except GameOver:
                self.game_over()
                self.cur_win.getkey()
                return


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

    logger.info("number of colors: %s", curses.COLORS)
    curses.init_color(9, 200, 300, 800)
    curses.init_pair(9, 9, curses.COLOR_BLACK)
    curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_BLUE)

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
COL_KEYS = 'zxcvbnm,./'

def draw_controls(win, start_x=0):
    win.clear()
    win.addstr(0, start_x+5, ' ⭮')
    win.addstr(1, start_x+5, '[w]')
    win.addstr(2, start_x, '<           >')
    win.addstr(2, start_x+2, '[a]   [d]')
    win.addstr(2, start_x+5, '[s]', curses.A_DIM)
    win.addstr(3, start_x+3, '[space]')
    win.addstr(4, start_x+6, '⭳')

    win.addstr(1, start_x+20, 'instant self.column select')
    win.addstr(2, start_x+23, '[z][x] ... [/]')
    win.addstr(3, start_x+20, 'press again to rotate', curses.A_DIM)
    
    win.addstr(5, start_x+10, '[q] open AI menu', curses.A_BLINK)

    win.refresh()


def brackethandler(k, win):
    if k != '[':
        return k
    try:
        return BRACKET_MAP[win.getkey()]
    except KeyError:
        return '['



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

    # set up curses windows
    height = HEIGHT
    width = WIDTH * 2 + 1 #need one extra for newline i think
    # pylint: disable=no-member
    begin_x = (curses.COLS - width) // 2
    info_begin_x = (curses.COLS - 2*width) // 2
    info_begin_y = height + 4 + 1
    board_win = curses.newwin(height, width, 4,     begin_x)
    cur_win =   curses.newwin(4,      width, 0,     begin_x)
    next_win =  curses.newwin(5,      9,     4,     begin_x + width + 2)
    score_win = curses.newwin(3,      7,     4 + 5, begin_x + width + 2)
    logger.info("%d %d", info_begin_y, curses.LINES)
    info_win =  curses.newwin(curses.LINES - info_begin_y, int(2.5*width), info_begin_y, info_begin_x)

    runner = TetrisGameRunner(board_win, cur_win, score_win, next_win, info_win)
    runner.run()

if __name__ == '__main__':
    curses.wrapper(main)
