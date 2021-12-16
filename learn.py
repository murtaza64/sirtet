import itertools as it
from collections import defaultdict
import random
from pprint import pprint
from board import GameOver, WIDTH, HEIGHT
from state import TetrisGameState

def neighborhood(state: TetrisGameState, orient, col):
    ot = state.tet[orient]
    shape = []
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    for dx, dy in it.product(range(-1, ot.width + 1), range(-1, ot.height)):
        if col + dx < 0 or WIDTH <= col + dx:
            shape.append((dx, dy))
        elif state.board[col + dx, yi + dy]:
            shape.append((dx, dy))
    return tuple(shape), ot


# row shape after potential placement here
def row_shape(state: TetrisGameState, orient, col):
    ot = state.tet[orient]
    shape = [0 for x in range(WIDTH)]
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    for x in range(WIDTH):
        if state.board[x, yi]:
            shape[x] = 1
    for dx in range(ot.width):
        if ot[dx, 0]:
            shape[col + dx] = 1
    return tuple(shape)

def cur_col_height(state: TetrisGameState, orient, col):
    max_ = 0
    for y in range(0, HEIGHT):
        # consider any block in columns that the tetromino would occupy
        if any(state.board[x, y] for x in range(col, col + state.tet[orient].width)):
            max_ = y + 1
    #try negating this?
    return HEIGHT - max_

def n_new_holes(state: TetrisGameState, orient, col):
    ot = state.tet[orient]
    holes = 0
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    for dx, dy in it.product(range(-1, ot.width + 1), range(-1, ot.height)):
        if col + dx < 0 or WIDTH <= col + dx or yi + dy < 0:
            continue
        if not (state.board[col + dx, yi + dy] or ot[dx, dy]):
            for ty in range(dy + 1, HEIGHT - yi):
                if state.board[col + dx, yi + ty] or ot[dx, ty]:
                    holes += 1
                    break
    return holes

def density(state: TetrisGameState, orient, col):
    ot = state.tet[orient]
    nbhd_sz = (ot.width + 2) * (ot.height * 2)
    found_blocks = 0
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    for dx, dy in it.product(range(-1, ot.width + 1), range(-1, ot.height)):
        if col + dx < 0 or WIDTH <= col + dx:
            found_blocks += 1
        elif state.board[col + dx, yi + dy] or ot[dx, dy]:
            found_blocks += 1
    return found_blocks/nbhd_sz

class TetrisQLearningAgent:
    DISCOUNT = 0.99
    LR_DECAY = 0.99
    RANDOM_MOVE_CHANCE = 0.05
    hashable_f_extrs = {
        neighborhood,
        row_shape
    }
    numeric_f_extrs = {
        cur_col_height,
        n_new_holes,
        density
    }

    def __init__(self):
        self.n_iterations = 0
        self.n_epochs = 0

        self.all_f_extrs = set()

        self.hashable_lr = {f: defaultdict(lambda: 1) for f in self.hashable_f_extrs}
        self.hashable_w = {f: defaultdict(lambda: 0) for f in self.hashable_f_extrs}
        self.all_f_extrs |= self.hashable_f_extrs

        self.numeric_lr = {f: 1 for f in self.numeric_f_extrs}
        self.numeric_w = {f: 0 for f in self.numeric_f_extrs}
        self.all_f_extrs |= self.numeric_f_extrs

    def choose_action(self, state: TetrisGameState):
        moves = list(state.get_moves())
        if random.random() < self.RANDOM_MOVE_CHANCE:
            return random.choice(moves)
        else:
            return max(moves, key=lambda a: self.q_estimate(state, *a))

    def f_get_q_contribution(self, f, state, activation):
        if f in self.hashable_f_extrs:
            return self.hashable_w[f][activation]
        if f in self.numeric_f_extrs:
            return self.numeric_w[f] * activation


    def f_update_weight(self, f, state, activation, delta):
        if f in self.hashable_f_extrs:
            lr = self.hashable_lr[f][activation]
            self.hashable_w[f][activation] += delta * lr
            self.hashable_lr[f][activation] *= self.LR_DECAY

        if f in self.numeric_f_extrs:
            lr = self.numeric_lr[f]
            self.numeric_w[f] += delta * lr * activation
            self.numeric_lr[f] *= self.LR_DECAY

    def q_estimate(self, state, orient, col, fmap=None):
        if fmap is None:
            fmap = dict()
        fmap.update({f : f(state, orient, col) for f in self.all_f_extrs})
        q = 0
        for f, activation in fmap.items():
            q += self.f_get_q_contribution(f, state, activation)
        return q
    
    def get_best_move(self, state):
        moves = list(state.get_moves())
        return max(moves, key=lambda a: self.q_estimate(state, *a))

    def train(self, iters):
        #pylint: disable=unused-variable

        for _ in range(iters):
            state = TetrisGameState()
            gameover = False
            while True:
                orient, col = self.choose_action(state)
                fmap = dict()
                q_old = self.q_estimate(state, orient, col, fmap=fmap)

                # get next state
                try:
                    _, reward, cleared = state.make_move(orient, col)
                    q_best_next = max([self.q_estimate(state, *a) for a in state.get_moves()])
                except GameOver:
                    gameover = True
                    reward = -100
                    cleared = []
                    q_best_next = 0

                # update weights
                delta = reward + self.DISCOUNT * q_best_next - q_old
                for f, activation in fmap.items():
                    self.f_update_weight(f, state, activation, delta)

                if gameover:
                    break
            self.n_iterations += 1
        self.n_epochs += 1
        with open(f'weights_epoch_{self.n_epochs}', 'w') as f:
            pprint(self.hashable_w, f)
            pprint(self.hashable_lr, f)
            pprint(self.numeric_w, f),
            pprint(self.numeric_lr, f)
