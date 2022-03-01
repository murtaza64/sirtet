#pylint:disable=unused-argument
import itertools as it
from collections import defaultdict
import random
from pprint import pprint
from board import GameOver, WIDTH, HEIGHT
from lib import fullwidth
from state import TetrisGameState

def neighborhood(state: TetrisGameState, orient, col, context):
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
def row_shape(state: TetrisGameState, orient, col, context):
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

def row_count(state: TetrisGameState, orient, col, context):
    ot = state.tet[orient]
    count = 0
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    for x in range(WIDTH):
        if state.board[x, yi]:
            count += 1
    for dx in range(ot.width):
        if ot[dx, 0]:
            count += 1
    return (count/WIDTH)**4

def target_roughness(state: TetrisGameState, orient, col, context):
    ot = state.tet[orient]
    shape = [0 for x in range(ot.width + 2)]
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    for dx in range(-1, ot.width + 1):
        if col + dx < 0:
            shape[dx + 1] = ot.height
            continue
        dy = 0
        while dy < ot.height and not ot[dx, dy]:
            dy += 1
        while yi + dy >= 0 and not state.board[col + dx, yi + dy]:
            dy -= 1
        shape[dx + 1] = max(min(dy + 1, ot.height), -1)
    return tuple(shape), ot


def lines_cleared(state: TetrisGameState, orient, col, context):
    if context['gameover']:
        return 0
    n = len(context['cleared'])
    return [-1e-3, 40, 100, 300, 1200][n]/40

def hspan_count(state: TetrisGameState, orient, col, context):
    ot = state.tet[orient]
    count = 0
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    for dy in range(ot.height):
        for x in range(WIDTH):
            if state.board[x, yi + dy]:
                count += 1
        for dx in range(ot.width):
            if ot[dx, dy]:
                count += 1
    return (count/(ot.height*WIDTH))**12

def cur_col_height(state: TetrisGameState, orient, col, context):
    max_ = 0
    for y in range(0, HEIGHT):
        # consider any block in columns that the tetromino would occupy
        if any(state.board[x, y] for x in range(col, col + state.tet[orient].width)):
            max_ = y + 1
    #try negating this?
    return max_/HEIGHT

def n_new_holes(state: TetrisGameState, orient, col, context):
    ot = state.tet[orient]
    holes = 0
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    if context['gameover']:
        return 0
    if context['cleared']:
        return 0
    for dx, dy in it.product(range(-1, ot.width + 1), range(-1, ot.height)):
        if col + dx < 0 or WIDTH <= col + dx or yi + dy < 0:
            continue
        if not (state.board[col + dx, yi + dy] or ot[dx, dy]):
            for ty in range(dy + 1, HEIGHT - yi):
                if state.board[col + dx, yi + ty] or ot[dx, ty]:
                    holes += 1
                    break
    return max(1, holes/3)

def holes_per_block(state: TetrisGameState, orient, col, context):
    holes = n_holes(state, orient, col, context)
    blocks = n_blocks(state, orient, col, context)
    return (holes/blocks) / 20

def n_blocks(state: TetrisGameState, orient, col, context):
    if context['gameover']:
        return 1
    total = 0
    board = context['dummy']
    for x, y in board.coords():
        if board[x, y]:
            total += 1
    return total/200

def n_holes(state: TetrisGameState, orient, col, context):
    if context['gameover']:
        return 1
    holes = 0
    board = context['dummy']
    for x, y in board.coords():
        if not board[x, y]:
            for ty in range(y + 1, HEIGHT):
                if state.board[x, ty]:
                    holes += 1
                    break
    return holes/200

def no_new_holes(state: TetrisGameState, orient, col, context):
    ot = state.tet[orient]
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    if context['cleared']:
        return False
    for dx, dy in it.product(range(-1, ot.width + 1), range(-1, ot.height)):
        if col + dx < 0 or WIDTH <= col + dx or yi + dy < 0:
            continue
        if not (state.board[col + dx, yi + dy] or ot[dx, dy]):
            for ty in range(dy + 1, HEIGHT - yi):
                if state.board[col + dx, yi + ty] or ot[dx, ty]:
                    return True
    return False

def tetromino_seq(state : TetrisGameState, orient, col, context):
    return state.tet[orient], state.next_tet

def density(state: TetrisGameState, orient, col, context):
    ot = state.tet[orient]
    nbhd_sz = (ot.width + 2) * (ot.height * 2)
    found_blocks = 0
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    for dx, dy in it.product(range(-1, ot.width + 1), range(-1, ot.height)):
        if yi + dy < 0:
            found_blocks += 1
        elif col + dx < 0 or WIDTH <= col + dx:
            nbhd_sz -= 1
        elif state.board[col + dx, yi + dy] or ot[dx, dy]:
            found_blocks += 1
    return found_blocks/nbhd_sz

def adjacent(x, y):
    yield x + 1, y
    # yield x + 1, y + 1
    yield x,     y + 1
    # yield x - 1, y + 1
    yield x - 1, y
    # yield x - 1, y - 1
    yield x,     y - 1
    # yield x + 1, y - 1

def surface_area(state: TetrisGameState, orient, col, context):
    total = 0
    if context['gameover']:
        return 1
    board = context['dummy']
    for x, y in it.product(range(WIDTH), range(HEIGHT)):
        if board[x, y]:
            for ax, ay in adjacent(x, y):
                if not 0 <= ax < WIDTH and 0 <= ay <= HEIGHT:
                    continue
                if not board[ax, ay]:
                    total += 1
    return total/200

def board_total_height(state : TetrisGameState, orient, col, context):
    if context['gameover']:
        return 1
    board = context['dummy']
    total = 0
    for x in range(WIDTH):
        y = HEIGHT - 1
        while not board[x, y] and y > 0:
            y -= 1
        total += y
    return total/200

def height_per_block(state : TetrisGameState, orient, col, context):
    if context['gameover']:
        return 1
    board = context['dummy']
    blocks = n_blocks(state, orient, col, context)
    total = 0
    for x in range(WIDTH):
        y = HEIGHT - 1
        while not board[x, y] and y > 0:
            y -= 1
        total += y
    return (total/(200*blocks)) / 20

def relative_cur_col_height(state, orient, col, context):
    if context['gameover']:
        return 1
    board = context['dummy']
    ot = state.tet[orient]
    heights = [0 for i in range(WIDTH)]
    for x in range(WIDTH):
        y = 0
        while y < HEIGHT:
            if board[x, y]:
                heights[x] = y
            y += 1
    highest = max(list(range(ot.width)), key=lambda dx: heights[col + dx])
    return int(heights[highest + col] - sum(heights)/WIDTH)/HEIGHT

def contact(state: TetrisGameState, orient, col, context):
    if context['gameover']:
        return 0
    ot = state.tet[orient]
    touching = 0
    total = 0
    yi = context['yi']
    for dx, dy in ot.offsets():
        if not ot[dx, dy]:
            continue
        for adx, ady in adjacent(dx, dy):
            if ot[adx, ady]:
                continue
            ax = col + adx
            ay = yi + ady
            if ay >= yi + ot.height:
                continue
            if not 0 <= ax < WIDTH or ay < 0:
                touching += 1
            elif state.board[ax, ay]:
                touching += 1
            total += 1
    return touching/total ** 2

def zero(*_):
    return 0

def one(*_):
    return 1

class TetrisQLearningAgent:
    DISCOUNT = 0.95
    LR_DECAY = defaultdict(lambda: 0.9996)
    LR_DECAY.update({
        lines_cleared: 0.99,
        target_roughness: 0.99
    })
    NUMERIC_LR = 1
    NUMERIC_LR_COUNT = 1

    RANDOM_MOVE_CHANCE = 0.02
    GAMEOVER_REWARD = -10
    MOVE_REWARD = 0
    hashable_f_extrs = {
        # target_roughness,
        # tetromino_seq
        # zero
    }
    hashable_f_extrs = set()
    INITIAL_WEIGHTS_NUMERIC = {
        cur_col_height: 0,
        relative_cur_col_height: -1,
        n_holes: -1,
        n_new_holes: -1,
        density: 5,
        row_count: 10,
        lines_cleared: 40,
        surface_area: -1,
        board_total_height: -10,
        contact: 60,
        holes_per_block: -1,
        height_per_block: -1
    }
    numeric_f_extrs = {
        # cur_col_height,
        relative_cur_col_height,
        # no_new_holes,
        # n_holes,
        # density,
        # row_count,
        lines_cleared,
        contact,
        holes_per_block,
        height_per_block
        # board_total_height
        # surface_area
    }

    def __init__(self):
        self.n_iterations = 0
        self.n_epochs = 0

        self.all_f_extrs = set()

        self.hashable_lr = {f: defaultdict(lambda: 0.9) for f in self.hashable_f_extrs}
        self.hashable_lr[target_roughness] = defaultdict(lambda: 0.5)

        self.hashable_w = {f: defaultdict(lambda: 0) for f in self.hashable_f_extrs}

        self.all_f_extrs |= self.hashable_f_extrs


        self.numeric_lr = {f: 1 for f in self.numeric_f_extrs}
        self.numeric_w = dict(self.INITIAL_WEIGHTS_NUMERIC)
        # self.numeric_w = {f: 0 for f in self.numeric_f_extrs}

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
            self.hashable_lr[f][activation] *= self.LR_DECAY[f]

            with open('info/updates.txt', 'a', encoding='utf-8') as fp:
                print(f'{f.__name__} weight update: {delta * lr}', file=fp)

        if f in self.numeric_f_extrs:
            lr = self.numeric_lr[f]
            self.numeric_w[f] += delta * lr * activation
            if activation:
                self.numeric_lr[f] *= self.LR_DECAY[f]
            with open('info/updates.txt', 'a', encoding='utf-8') as fp:
                print(f'{f.__name__} weight update: {delta * lr * activation} (lr={lr}', file=fp)


    def q_estimate(self, state : TetrisGameState, orient, col, fmap=None):
        if fmap is None:
            fmap = dict()
        context = {}
        try:
            context['gameover'] = False
            board, yi, cleared = state.board.test_place_tetromino(state.tet, orient, col)
            context['dummy'] = board
            context['cleared'] = cleared
            context['yi'] = yi
        except GameOver:
            context['gameover'] = True

        # b = state.board.copy()
        # b.test_place_tetromino(state.tet, orient, col)
        # context['uncleared_dummy'] = b

        fmap.update({f : f(state, orient, col, context) for f in self.all_f_extrs})
        q = 0
        for f, activation in fmap.items():
            q += self.f_get_q_contribution(f, state, activation)
        return q

    def get_best_move(self, state):
        moves = list(state.get_moves())
        return max(moves, key=lambda a: self.q_estimate(state, *a))

    def train(self, iters):
        # with open('info/updates.txt', 'w') as fp:
        #     print(f'hello world!', file=fp)
        for _ in range(iters):
            state = TetrisGameState()
            gameover = False
            n_moves = 0
            while True:
                orient, col = self.choose_action(state)
                fmap = dict()
                q_old = self.q_estimate(state, orient, col, fmap=fmap)

                # get next state
                try:
                    _, reward, _ = state.make_move(orient, col)
                    reward += self.MOVE_REWARD
                    q_best_next = max([self.q_estimate(state, *a) for a in state.get_moves()])
                except GameOver:
                    gameover = True
                    # reward = min(self.GAMEOVER_REWARD + n_moves/4, -1)
                    reward = self.GAMEOVER_REWARD
                    # cleared = []
                    q_best_next = 0

                # update weights
                delta = reward + self.DISCOUNT * q_best_next - q_old
                with open('info/updates.txt', 'a', encoding='utf-8') as fp:
                    pprint(fmap, fp)
                    print(f'q_best_next ={q_best_next} q_old = {q_old}', file=fp)
                    print(f'delta: {delta}', file=fp)
                for f, activation in fmap.items():
                    self.f_update_weight(f, state, activation, delta)

                if gameover:
                    break

                n_moves += 1

            self.n_iterations += 1
        with open(f'info/weights_epoch_{self.n_epochs}.txt', 'w', encoding='utf-8') as f:
            n_features = len(self.numeric_w) + sum(len(x) for x in self.hashable_w.values())
            pprint(f'n_features: {n_features}', f)
            pprint(self.hashable_w, f)
            pprint(self.hashable_lr, f)
            pprint(self.numeric_w, f)
            pprint(self.numeric_lr, f)
        self.n_epochs += 1
