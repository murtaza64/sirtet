import logging
from typing import Callable
import random
from collections import deque

import tensorflow as tf
from tensorflow import keras
from keras import layers
from keras import Model
from board import WIDTH, GameOver, TetrisBoard

from base_agent import BaseTetrisAgent
from state import TetrisGameState
from features2 import (eroded_piece_cells, col_transitions, row_transitions,
    holes, landing_height, cumulative_wells)

class DeepQExpReplayAgent(BaseTetrisAgent):

    agent_name = 'Deep Q learning with experience replay'

    features = [
        eroded_piece_cells,
        col_transitions,
        row_transitions,
        holes,
        landing_height,
        cumulative_wells
    ]
    copy_iterations = 500
    minibatch_size = 8
    exploration_prob = 0.05
    discount_rate = 0.9
    experience_buffer_size = 10000
    def __init__(
            self,
            logger,
            **kwargs
        ):
        super().__init__(**kwargs)
        self.optimizer = keras.optimizers.Adam(learning_rate=0.001)
        self.model = self.create_model()
        self.target_model = self.create_model()
        self.iterations = 0
        self.logger = logger

        self.experiences = deque(maxlen=self.experience_buffer_size)

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
    
    def state_to_input(self, state, orient, col):
        inputs = [f(state, orient, col) for f in self.features]
        inputs = tf.convert_to_tensor(inputs, dtype=tf.float64)
        return inputs
        
    def get_best_move(self, state : TetrisGameState) -> 'tuple[int, int]':
        moves = list(state.get_moves())
        moves_input_set = [self.state_to_input(state, o, c) for o, c in moves]
        #calculate q values in batch
        q_values = tf.squeeze(self.target_model(tf.convert_to_tensor(moves_input_set)))
        i = tf.math.argmax(q_values)
        return moves[i]

    def sample_experiences(self):
        inputss, rewards, next_states = zip(*random.sample(self.experiences, self.minibatch_size))
        return list(inputss), list(rewards), list(next_states)
    
    def train_step(self, state : TetrisGameState):
        self.epoch_iters += 1
        self.iterations += 1
        
        # copy q model to target model
        if self.iterations % self.copy_iterations == 0:
            self.target_model.set_weights(self.model.get_weights())

        # world interaction phase
        
        orient, col = self.choose_action(state)
        #q value of chosen action
        # q_observed = self.get_q_value(state, orient, col)

        try:
            dummy, _, cleared = state.board.test_place_tetromino(state.tet, orient, col)
            gameover = False
            reward = state.board.score(cleared)
        except GameOver:
            gameover = True
            #penalize game over a little
            reward = -10

        #experiences consist of F(state, action), reward, next state
        
        if gameover:
            ns_moves_input_vec = None
        else:
            next_state = TetrisGameState()
            next_state.board = dummy
            next_state.tet = state.next_tet
            ns_moves_input_vec = [self.state_to_input(next_state, o, c) for o, c in next_state.get_moves()]
        self.experiences.append((self.state_to_input(state, orient, col), reward, ns_moves_input_vec))

        # experience replay phase
        if len(self.experiences) < self.minibatch_size:
            return orient, col

        with tf.GradientTape() as tape:
            input_list, rewards, ns_movesets_as_input_vectors = self.sample_experiences()

            # calculate estimates of q value based on reward and q of best action in next state
            best_next_q_values = []
            for iv in ns_movesets_as_input_vectors:
                if iv is None:
                    best_next_q_values.append(0)
                else:
                    #get q values of all next actions in one batch
                    # moves_input_set = [self.state_to_input(ns, o, c) for o, c in ns.get_moves()]
                    q_values = self.target_model(tf.convert_to_tensor(iv))
                    #best q value of all moves possible in next state
                    best_next_q_value = max(tf.squeeze(q_values))
                    best_next_q_values.append(best_next_q_value)
            
            best_next_q_vec = tf.convert_to_tensor(best_next_q_values)
            reward_vec = tf.convert_to_tensor(rewards, dtype=tf.float32)

            q_observed_vec = tf.squeeze(self.model(tf.convert_to_tensor(input_list)))
            
            q_estimates_vec = reward_vec + self.discount_rate * best_next_q_vec

            loss = (q_observed_vec - q_estimates_vec)**2
            
        grads = tape.gradient(loss, self.model.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.model.trainable_variables))

        loss = tf.reduce_mean(loss)
        self.avg_loss = tf.cast((self.avg_loss*(self.epoch_iters-1)/self.epoch_iters) + loss / self.epoch_iters, tf.float32)
        
        return orient, col
    
    def monitor(self):
        out = ''
        out += f'{self.copy_iterations=}\n{self.exploration_prob=}\n{self.discount_rate=}\n{self.minibatch_size=}\n'
        out += 'features: ' + ', '.join([f.__name__ for f in self.features]) + '\n'
        out += '===\n'
        out += f'epoch = {self.epochs}\n'
        out += f'games played = {self.games}\n'
        out += f'train steps = {self.iterations}\n'
        out += f'experiences saved = {len(self.experiences)}\n'
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