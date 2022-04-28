import curses, logging
from time import sleep

from board import WIDTH, HEIGHT, TetrisBoard
from lib import color_attrs, brackethandler, split_into_lines
from tetrominoes import OrientedTetromino
from base_runner import Runner

class UserInterface:
    LEFT = 0
    MIDDLE = 1

    def __init__(self, board_win, cur_win, score_win, next_win, info_win, bottom_row, left_win, runner, logger=None):
        # self.state = TetrisGameState()
        # self.orient = 0
        # self.col = 0
        
        self.logger = logger

        self.info_queue = []
        self.left_queue = []
        self.high_score = 0

        #tetris windows
        self.board_win = board_win
        self.cur_win = cur_win
        self.score_win = score_win
        self.next_win = next_win

        #text windows
        self.left_win = left_win
        self.info_win = info_win
        self.bottom_row = bottom_row
        
        self.text_windows = [left_win, info_win]
        self.text_queues = [self.left_queue, self.info_queue]

        self.runner : Runner = runner(self)

    def push_text(self, s : str, win_idx : int = MIDDLE):
        win = self.text_windows[win_idx]
        q = self.text_queues[win_idx]

        h, w = win.getmaxyx()
        lines = split_into_lines(s, w)
        # n = len(lines)
        q += lines
        while len(q) > h:
            q.pop(0)

        if len(q) >= h:
            q = q[:h-1]

        win.clear()
        for i, line in enumerate(q):
            win.addstr(i, 0, line)
        win.refresh()

    def set_text(self, s : str, win_idx : int = MIDDLE):
        win = self.text_windows[win_idx]
        self.clear_text(win_idx)
        q = self.text_queues[win_idx]

        h, w = win.getmaxyx()
        lines = split_into_lines(s, w)
        q += lines

        if len(q) >= h:
            q = q[:h-1]

        for i, line in enumerate(q):
            win.addstr(i, 0, line)
        win.refresh()

    def clear_text(self, win_idx : int):
        self.text_queues[win_idx] = []
        self.text_windows[win_idx].clear()
        self.text_windows[win_idx].refresh()

    def draw_board(self, board : TetrisBoard):
        board.draw(self.board_win)
        self.board_win.refresh()

    def draw_cur_tet(self, ot : OrientedTetromino, col):
        self.cur_win.clear()
        if ot is not None:
            ot.draw(self.cur_win, 4 - ot.height, col)
        self.cur_win.refresh()

    def draw_next_tet(self, ot : OrientedTetromino):
        self.next_win.clear()
        self.next_win.addstr('next:')
        if ot is not None:
            ot.draw(self.next_win, 1, 0)
        self.next_win.refresh()


    def remove_placement_preview(self, board, tet, orient, col, refresh=False):
        board.preview(self.board_win, tet, orient, col, remove=True)
        if refresh:
            self.board_win.refresh()

    def draw_placement_preview(self, board, tet, orient, col):
        board.preview(self.board_win, tet, orient, col)
        self.board_win.refresh()

    def celebrate(self, board, reward, cleared):
        self.board_win.clear()
        board.draw(self.board_win)
        scorestr = str(reward)
        rewardstr =  '+ ' + ' '*(4-len(scorestr)) + scorestr
        for _ in range(4):
            for idx in cleared:
                board.draw_line(self.board_win, idx, autocolor=False)
                self.board_win.refresh()
            self.score_win.addstr(2, 0, rewardstr, curses.color_pair(6))
            self.score_win.refresh()
            sleep(0.1)
            for idx in cleared:
                board.draw_line(self.board_win, idx, 0)
                self.board_win.refresh()
            self.score_win.addstr(2, 0, rewardstr)
            self.score_win.refresh()
            sleep(0.1)
    
    def set_score(self, score):
        self.score_win.clear()
        self.score_win.addstr('score:')
        self.score_win.addstr(1, 0, f'{score:06d}')
        self.score_win.refresh()

    def loop(self):
        # state = TetrisGameState()
        # state.make_move(0, 0)
        # state.make_move(0, 0)
        # self.draw_board(state.board)
        # self.draw_cur_tet(state.tet[0], 0)
        # self.draw_next_tet(state.next_tet[0])
        # self.set_score(24000)
        # self.celebrate(state.board, 10000, [0, 1, 2, 3])

        while True:
            k = self.cur_win.get_wch()
            k = brackethandler(k, self.cur_win)
            self.runner.handle_keypress(k)


def curses_init():
    if not curses.has_colors():
        raise Exception('curses does not support colors')
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


def default_curses_window_init(stdscr):
    curses_init()
    # Clear screen
    stdscr.clear()

    # set up curses windows
    height = HEIGHT
    width = WIDTH * 2 + 1 #need one extra for newline i think
    # pylint: disable=no-member
    begin_x = (curses.COLS - width) // 2
    board_win = curses.newwin(height, width, 4,     begin_x)
    cur_win =   curses.newwin(4,      width, 0,     begin_x)
    next_win =  curses.newwin(5,      9,     4,     begin_x + width + 2)
    score_win = curses.newwin(6,      7,     4 + 5, begin_x + width + 2)
    
    info_begin_y = height + 4 + 1
    left_width = min(begin_x - 2, 48)
    # old info layout
    info_begin_x = max((curses.COLS - int(4*width)) // 2, left_width + 2)
    info_width = min(int(4*width), curses.COLS - 1)
    info_begin_y = height + 4 + 1
    info_win =  curses.newwin(curses.LINES - info_begin_y - 1, info_width, info_begin_y, info_begin_x)
    # info_begin_x = 2
    # info_width = curses.COLS - info_begin_x - 2
    # info_height = curses.LINES - info_begin_y - 1
    # info_win =  curses.newwin(info_height, info_width, info_begin_y, info_begin_x)
    left_win = curses.newwin(curses.LINES - 2, left_width, 1, 1)

    bottom_row = curses.newwin(1, curses.COLS, curses.LINES-1, 0)
    bottom_row.addstr('[ctrl][c] exit   [q] run AI', curses.A_DIM)
    bottom_row.refresh()

    # board_win.bkgdset('b')
    # info_win.bkgdset('i')
    # left_win.bkgdset('l')
    # board_win.clear()
    # info_win.clear()
    # left_win.clear()
    # board_win.addstr('board')
    # left_win.addstr('left')
    # info_win.addstr('info')
    # board_win.refresh()
    # info_win.refresh()
    # left_win.refresh()

    return board_win, cur_win, score_win, next_win, info_win, bottom_row, left_win