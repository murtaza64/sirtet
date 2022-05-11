import logging
from typing import Callable
import random

import tensorflow as tf
from tensorflow import keras
from keras import layers
from keras import Model
from board import WIDTH, GameOver, TetrisBoard

from base_agent import BaseTetrisAgent
from state import TetrisGameState
from features2 import (eroded_piece_cells, col_transitions, row_transitions,
    holes, landing_height, cumulative_wells)

class DeepQAgent(BaseTetrisAgent):

    agent_name = 'Deep Q learning agent'

    features = [
        eroded_piece_cells,
        col_transitions,
        row_transitions,
        holes,
        landing_height,
        cumulative_wells
    ]
    copy_iterations = 100

    def __init__(
            self,
            logger,
            exploration_prob=0.05,
            discount_rate=0.9,
            **kwargs
        ):
        super().__init__(**kwargs)
        self.exploration_prob = exploration_prob
        self.discount_rate = discount_rate
        self.optimizer = keras.optimizers.Adam(learning_rate=0.001)
        self.model = self.create_model()
        self.target_model = self.create_model()
        self.iterations = 0
        self.logger = logger

        self.avg_loss = 0
        self.epoch_iters = 0
        self.epochs = 0
        self.games = 0

    def create_model(self):
        inputs = layers.Input(shape=(len(self.features),))
        h1 = layers.Dense(16, activation='relu')(inputs)
        h2 = layers.Dense(16, activation='relu')(h1)
        outputs = layers.Dense(1)(h2)
        return Model(inputs=inputs, outputs=outputs)
    
    def choose_action(self, state : TetrisGameState):
        if random.random() < self.exploration_prob:
            return random.choice(list(state.get_moves()))
        else:
            return self.get_best_move(state)
    
    def get_q_value(self, state : TetrisGameState, orient, col):
        inputs = [f(state, orient, col) for f in self.features]
        inputs = tf.expand_dims(tf.convert_to_tensor(inputs), axis=0)
        return self.model(inputs)[0]
        
    def get_best_move(self, state : TetrisGameState) -> 'tuple[int, int]':
        move_q_values = {(orient, col): self.get_q_value(state, orient, col) for orient, col in state.get_moves()}
        return max(move_q_values, key=lambda m: move_q_values[m])
    
    def train_step(self, state : TetrisGameState):
        self.epoch_iters += 1
        self.iterations += 1
        # copy q model to target model
        if self.iterations % self.copy_iterations == 0:
            self.target_model.set_weights(self.model.get_weights())
        
        with tf.GradientTape() as tape:
            orient, col = self.choose_action(state)
            #q value of chosen action
            q_observed = self.get_q_value(state, orient, col)

            if random.random() < 0.01:
                self.logger.log(logging.DEBUG, f'random q value: {q_observed}')
            try:
                dummy, _, cleared = state.board.test_place_tetromino(state.tet, orient, col)
                gameover = False
                reward = state.board.score(cleared)
            except GameOver:
                gameover = True
                #penalize game over a little
                reward = -10
            
            
            # calculate estimate of q value based on reward and q of best action in next state
            if gameover:
                best_next_q_value = 0
            else:
                next_state = TetrisGameState()
                next_state.board = dummy
                next_state.tet = state.next_tet
                next_q_values = {}
                for o, c in next_state.get_moves():
                    inputs = [f(next_state, o, c) for f in self.features]
                    inputs = tf.expand_dims(tf.convert_to_tensor(inputs), axis=0)
                    next_q_values[(o, c)] = self.target_model(inputs)[0]
                best_next_q_value = max(next_q_values.values())
            
            q_estimate = reward + self.discount_rate * best_next_q_value
            #loss can be factored out--use model.compile(loss=keras.losses{DESIRED_LOSS_FUNCTION}) and call it using self.loss_function
            loss = (q_observed - q_estimate)**2
            
        grads = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.model.trainable_variables))
        
        self.avg_loss = (self.avg_loss*(self.epoch_iters-1)/self.epoch_iters) + loss / self.epoch_iters
        
        return orient, col
    
    def monitor(self):
        out = f'epoch = {self.epochs}\n'
        out += f'games played = {self.games}\n'
        out += f'train steps = {self.iterations}\n'
        try:
            out += f'average loss this epoch = {self.avg_loss}'
        except ZeroDivisionError:
            pass
        return out
    
    def save_weights(self, filename):
        self.model.save_weights(filename)
    
    def load_weights(self, filename):
        try:
            self.model.load_weights(filename)
        except tf.errors.NotFoundError:
            raise FileNotFoundError
    
    def train(self, iters):
        self.avg_loss = 0
        self.epoch_iters = 0
        self.epochs += 1
        for _ in range(iters):
            self.logger.log(logging.DEBUG, f'running new tetris game! iterations={self.iterations}')
            s = TetrisGameState()
            while True:
                # self.logger.log(logging.DEBUG, 'start train step')
                orient, col = self.train_step(s)
                # self.logger.log(logging.DEBUG, 'end train step')
                try:
                    s.make_move(orient, col)
                except GameOver:
                    self.games += 1
                    break
            self.logger.log(logging.DEBUG, f'average loss={self.avg_loss}')