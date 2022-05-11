#pylint:disable=unused-argument
import itertools as it
from collections import defaultdict
import logging
import random

from pprint import pprint
from board import GameOver, WIDTH, HEIGHT
from state import TetrisGameState
from base_agent import BaseTetrisAgent

from features import (cur_col_height, relative_cur_col_height, n_holes, n_new_holes, 
    density, row_count, lines_cleared, surface_area, target_roughness,
    board_total_height, contact, holes_per_block, height_per_block)

class TetrisQLearningAgent(BaseTetrisAgent):

    agent_name = 'Q learning agent (474)'

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

    def __init__(self, logger):
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

        self.logger = logger

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
        self.logger.log(logging.DEBUG, 'returning best move...')
        moves = list(state.get_moves())
        ret = max(moves, key=lambda a: self.q_estimate(state, *a))
        self.logger.log(logging.DEBUG, 'returned best move')
        return ret

    def train(self, iters):
        # with open('info/updates.txt', 'w') as fp:
        #     print(f'hello world!', file=fp)
        for _ in range(iters):
            self.logger.log(logging.DEBUG, 'train step')

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
