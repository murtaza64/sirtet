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


class TetrisGameRunner:
    def __init__(self, board_win, cur_win, score_win, next_win, info_win):
        self.state = TetrisGameState()
        self.orient = 0
        self.col = 0
        self.info_queue = []

        if curses:
            self.board_win = board_win
            self.cur_win = cur_win
            self.score_win = score_win
            self.next_win = next_win
            self.info_win = info_win

    def split_into_lines(self, s, length):
        ret = []
        while s:
            ret.append(s[:length])
            s = s[length:]
        return ret

    def show_info(self, s):
        h, w = self.info_win.getmaxyx()
        lines = self.split_into_lines(s, w)
        n = len(lines)
        while len(self.info_queue) + n > h:
            self.info_queue.pop(0)
        self.info_queue += lines

        self.info_win.clear()
        for i, line in enumerate(self.info_queue):
            self.info_win.addstr(i, 0, line)
        self.info_win.refresh()

    
    def ai_run(self):
        agent = TetrisQLearningAgent()
        epochs = 5
        iters = 100
        t = threading.Thread(target=self.trainer, args=(agent, epochs, iters))
        t.start()
        high_score = 0
        while (t.is_alive()):
            # self.show_info(f'epoch {agent.n_epochs}')
            # agent.train(100)
            # self.show_info(f'training done: evaluating...')
            score, lines, moves = self.watch_ai_game(agent)
            if score > high_score:
                self.show_info(f'new high score: {score}, lines: {lines}, moves: {moves}')
                high_score = score
        self.show_info('training done')

    def trainer(self, agent, epochs, iters):
        self.show_info(f'running {epochs} epochs of {iters} iterations')
        for i in range(epochs):
            self.show_info(f'epoch {agent.n_epochs}...')
            agent.train(iters)

    def watch_ai_game(self, agent):
        self.state = TetrisGameState()
        lines = 0
        moves = 0


        while True:
            self.orient = 0
            self.col = 0
            self.state.board.draw(self.board_win)
            self.board_win.refresh()

            self.draw_score()
            self.draw_next_tet()

            ot : OrientedTetromino = self.state.tet[self.orient]
            self.cur_win.clear()
            ot.draw(self.cur_win, 4 - ot.height, self.col)
            self.cur_win.refresh()

            self.orient, self.col = agent.get_best_move(self.state)
            ot = self.state.tet[self.orient]

            self.state.board.preview(self.board_win, self.state.tet, self.orient, self.col)
            sleep(0.05)

            self.board_win.refresh()
            self.cur_win.clear()
            ot.draw(self.cur_win, 4 - ot.height, self.col)
            self.cur_win.refresh()
            sleep(0.05)

            moves += 1
            try:
                old_board, reward, cleared = self.state.make_move(self.orient, self.col)
                lines += len(cleared)
            except GameOver:
                break
            if cleared:
                self.celebrate(old_board, reward, cleared)
                self.state.score += reward
                lines += len(cleared)

        return self.state.score, lines, moves

    def play_ai_game(self, agent):
        state = TetrisGameState()
        score = 0
        lines = 0
        moves = 0
        while True:
            orient, col = agent.get_best_move(state)
            moves += 1
            try:
                _, reward, cleared = state.make_move(orient, col)
                score += reward
                lines += len(cleared)
            except GameOver:
                break
        return score, lines, moves

    def ai_menu(self):
        self.ai_run()
        return False

    def iteration(self):
        # self.board_win.clear()
        self.state.board.draw(self.board_win)
        self.board_win.refresh()

        self.draw_score()
        self.draw_next_tet()

        self.orient = 0
        self.col = 4
        while True:
            #draw cur tet
            ot : OrientedTetromino = self.state.tet[self.orient]
            self.cur_win.clear()
            ot.draw(self.cur_win, 4 - ot.height, self.col)
            self.cur_win.refresh()
            self.state.board.preview(self.board_win, self.state.tet, self.orient, self.col)
            self.board_win.refresh()
            k = self.process_keypress()
            if k == ' ':
                break
            elif k == 'q':
                if self.ai_menu():
                    break
                self.state.board.draw(self.board_win)
                self.board_win.refresh()

                self.draw_score()
                self.draw_next_tet()
                

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
        if k in 'rq ':
            return k
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
                self.col = WIDTH - self.state.tet[self.orient].width

        return False

    def celebrate(self, old_board, reward, cleared):
        self.board_win.clear()
        old_board.draw(self.board_win)
        scorestr = str(reward)
        rewardstr =  '+ ' + ' '*(4-len(scorestr)) + scorestr
        for _ in range(4):
            for idx in cleared:
                old_board.draw_line(self.board_win, idx, autocolor=False)
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

    def draw_controls(self, start_x=0):
        self.info_win.clear()
        self.info_win.addstr(0, start_x+5, ' ⭮')
        self.info_win.addstr(1, start_x+5, '[w]')
        self.info_win.addstr(2, start_x, '<           >')
        self.info_win.addstr(2, start_x+2, '[a]   [d]')
        self.info_win.addstr(2, start_x+5, '[s]', curses.A_DIM)
        self.info_win.addstr(3, start_x+3, '[space]')
        self.info_win.addstr(4, start_x+6, '⭳')

        self.info_win.addstr(1, start_x+20, 'instant column select')
        self.info_win.addstr(2, start_x+23, '[z][x] ... [/]')
        self.info_win.addstr(3, start_x+20, 'press again to rotate', curses.A_DIM)

        self.info_win.addstr(5, start_x+10, '[q] open AI menu', curses.A_BLINK)

        self.info_win.refresh()

    def game_over(self):
        self.state.board.draw(self.board_win)
        self.board_win.refresh()
        curses.init_pair(10, curses.COLOR_BLACK, COLOR_MAP[self.state.tet.letter])
        self.info_win.clear()
        self.info_win.addstr(1, 10, ' '*WIDTH*2, curses.color_pair(10))
        self.info_win.addstr(2, 10, '    game over :(    ', curses.color_pair(10))
        self.info_win.addstr(3, 10, f'    score {self.state.score:06d}    ', curses.color_pair(10))
        self.info_win.addstr(4, 10, ' '*WIDTH*2, curses.color_pair(10))
        self.info_win.addstr(6, 10, '  [r] play again  ')
        self.info_win.refresh()
        while True:
            if self.process_keypress() == 'r':
                self.state = TetrisGameState()
                self.info_win.clear()
                self.info_win.refresh()
                return

    def run(self):
        self.draw_controls()
        #one iteration after which we clear controls
        self.iteration()
        self.info_win.clear()
        self.info_win.refresh()
        while True:
            try:
                self.iteration()
            except GameOver:
                self.game_over()


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

    # logger.info("number of colors: %s", curses.COLORS)
    # curses.init_color(9, 200, 300, 800)
    # curses.init_pair(9, 9, curses.COLOR_BLACK)
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
COLOR_MAP = {
    'z': curses.COLOR_RED,
    'l': curses.COLOR_YELLOW,
    'o': curses.COLOR_YELLOW,
    's': curses.COLOR_GREEN,
    'j': curses.COLOR_BLUE,
    't': curses.COLOR_MAGENTA,
    'i': curses.COLOR_CYAN
}

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
    info_win =  curses.newwin(curses.LINES - info_begin_y - 1, int(2.5*width), info_begin_y, info_begin_x)
    bottom_row = curses.newwin(1, curses.COLS, curses.LINES-1, 0)
    bottom_row.addstr('[ctrl][c] exit   [q] AI menu', curses.A_DIM)
    bottom_row.refresh()

    runner = TetrisGameRunner(board_win, cur_win, score_win, next_win, info_win)
    runner.run()

if __name__ == '__main__':
    curses.wrapper(main)
