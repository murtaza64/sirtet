import curses
from datetime import datetime
import json
from pathlib import Path

from state import TetrisGameState
from board import WIDTH, HEIGHT, GameOver
from ui import UserInterface
from base_runner import Runner
    
class RunState:
    PLAYING = 0
    GAME_OVER = 1

class RecordDemonstrationsRunner(Runner):

    def __init__(self, ui : UserInterface):
        self.ui = ui
        self.state = TetrisGameState()

        self.runstate = RunState.PLAYING

        self.col = 4
        self.orient = 0
        self.high_score = 0
        self.draw_controls(self.ui.info_win)
        self.ui.draw_board(self.state.board)
        self.ui.draw_cur_tet(self.state.tet[self.orient], self.col)
        self.ui.draw_next_tet(self.state.next_tet[0])
        self.ui.set_score(0, 0)
        self.ui.draw_placement_preview(self.state.board, self.state.tet, self.orient, self.col)
        self.demonstrations = []

    def move_cur_tet(self, delta):
        ot = self.state.tet[self.orient]
        if 0 <= self.col + delta <= WIDTH - ot.width:
            self.ui.remove_placement_preview(self.state.board, self.state.tet, self.orient, self.col)
            self.col += delta
            self.ui.draw_placement_preview(self.state.board, self.state.tet, self.orient, self.col)
            self.ui.draw_cur_tet(self.state.tet[self.orient], self.col)

    def rotate_cur_tet(self):
        self.ui.remove_placement_preview(self.state.board, self.state.tet, self.orient, self.col)
        self.orient = (self.orient + 1) % self.state.tet.n_orientations()
        ot = self.state.tet[self.orient]
        while self.col + ot.width > WIDTH:
            # logger.log(logging.DEBUG, f'{ot=} {ot.width=} {self.col=} {WIDTH=}')
            self.col -= 1
        self.ui.draw_placement_preview(self.state.board, self.state.tet, self.orient, self.col)
        self.ui.draw_cur_tet(self.state.tet[self.orient], self.col)

    def place_cur_tet(self):
        # eroded = cumulative_wells(self.state, self.orient, self.col)
        # self.ui.push_text(f'{eroded} {self.col}')
        self.demonstrations.append((self.state.board.copy(), self.state.tet, self.state.next_tet, self.orient, self.col))
        self.ui.set_text(f'recorded demonstrations: {len(self.demonstrations)}', self.ui.LEFT)
        old_board, reward, cleared = self.state.make_move(self.orient, self.col)
        if cleared:
            self.ui.celebrate(old_board, reward, cleared)
            self.state.score += reward
        self.orient = 0
        self.col = 4
        self.ui.draw_board(self.state.board)
        self.ui.draw_cur_tet(self.state.tet[self.orient], self.col)
        self.ui.draw_placement_preview(self.state.board, self.state.tet, self.orient, self.col)
        self.ui.draw_next_tet(self.state.tet[self.orient])
        self.ui.set_score(self.state.score, self.high_score)

    def game_over(self):
        if self.state.score > self.high_score:
            self.high_score = self.state.score
            self.ui.set_score(self.state.score, self.high_score)
        self.ui.set_text('game over')
        self.ui.push_text('[r] play again') 
        self.ui.push_text('[f] save demonstrations')
        self.ui.push_text('[q] open AI menu')

    def demo_to_str(self, demo):
        #pylint:disable=protected-access
        board, tet, nt, orient, col = demo
        boardints = []
        for row in board._board:
            bits = ''.join(['1' if c else '0' for c in row])
            n = int(bits, base=2)
            boardints.append(str(n))
        return f'{"/".join(boardints)}|{tet.letter}|{nt.letter}:{orient},{col}\n'

    def save_demonstrations(self):
        processed_demos = [self.demo_to_str(demo) for demo in self.demonstrations]
        Path('demonstrations').mkdir(exist_ok=True)
        filename = f'demonstrations/{datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}.demo'
        with Path(filename).open(mode='w', encoding='utf-8') as f:
            f.writelines(processed_demos)
        self.demonstrations = []
        self.ui.set_text(f'demonstrations saved to {filename}')
        if self.runstate == RunState.GAME_OVER:
            self.ui.push_text('[r] play again ')
            self.ui.push_text('[q] open AI menu')
        self.ui.push_text('keep going or press [q] to open the AI menu')
        self.ui.set_text(f'recorded demonstrations: {len(self.demonstrations)}', self.ui.LEFT)

    def handle_keypress(self, k):
        if k in ['q']:
            self.ui.switch_runner(1)
            return


        if self.runstate == RunState.PLAYING:
            # ot = self.state.tet[self.orient]
            if k in ['a', 'LEFT']:
                self.move_cur_tet(-1)
            elif k in ['d', 'RIGHT']:
                self.move_cur_tet(1)
            elif k in ['w', 'UP']:
                self.rotate_cur_tet()
            elif k in [' ']:
                try:
                    self.place_cur_tet()
                except GameOver:
                    self.runstate = RunState.GAME_OVER
                    self.game_over()
        
        elif self.runstate == RunState.GAME_OVER:
            if k in ['r']:
                self.state = TetrisGameState()
                self.orient = 0
                self.col = 4
                self.runstate = RunState.PLAYING
                self.draw_controls(self.ui.info_win)
                self.ui.draw_board(self.state.board)
                self.ui.draw_cur_tet(self.state.tet[self.orient], self.col)
                self.ui.draw_next_tet(self.state.next_tet[0])
                self.ui.set_score(0, self.high_score)
        
        if k in ['f']:
            self.save_demonstrations()

    def draw_controls(self, win, start_x=0):
        win.clear()
        win.addstr(0, start_x+5, ' ⭮')
        win.addstr(1, start_x+5, '[w]')
        win.addstr(2, start_x, '<           >')
        win.addstr(2, start_x+2, '[a]   [d]')
        win.addstr(2, start_x+5, '[s]', curses.A_DIM)
        win.addstr(3, start_x+3, '[space]')
        win.addstr(4, start_x+6, '⭳')

        # win.addstr(1, start_x+20, 'instant column select')
        # win.addstr(2, start_x+23, '[z][x] ... [/]')
        # win.addstr(3, start_x+20, 'press again to rotate', curses.A_DIM)

        win.addstr(5, start_x+12, '[q] open AI menu')
        win.addstr(6, start_x+12, '[f] save demonstrations')

        win.refresh()


