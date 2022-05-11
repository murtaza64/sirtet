from pathlib import Path
import threading
from time import sleep
import logging
from deepq_exp import DeepQExpReplayAgent

from ui import UserInterface
from state import TetrisGameState
from base_runner import Runner
from tetrominoes import OrientedTetromino
from board import GameOver

from base_agent import BaseTetrisAgent
from q474 import TetrisQLearningAgent
from dellacherie import DellacherieAgent
from deepq import DeepQAgent

class Options:
    TRAINABLE = 1
    SAVABLE = 2
    MONITOR = 3

class RunState:
    CHOOSE_AGENT = 0
    AGENT_MENU = 1
    TRAINING = 2
    WATCHING = 3
    TRAINING_PAUSED = 4
    TRAINING_FINISHED = 5

class AgentMenuItems:
    WATCH = 0
    TRAIN = 1
    SAVE = 2
    LOAD = 3
    TRAIN_SILENT = 4

agent_menu_item_name = {
    AgentMenuItems.WATCH : 'watch agent play tetris',
    AgentMenuItems.TRAIN : 'train agent',
    AgentMenuItems.SAVE : 'save agent data',
    AgentMenuItems.LOAD : 'load saved agent data',
    AgentMenuItems.TRAIN_SILENT : 'train agent without watching'
}

class AIRunner(Runner):
    
    installed_agents : 'list[tuple[BaseTetrisAgent, set]]' = [
        (TetrisQLearningAgent,  {Options.TRAINABLE, Options.MONITOR}),
        (DellacherieAgent,      {}),
        (DeepQAgent,            {Options.TRAINABLE, Options.MONITOR, Options.SAVABLE}),
        (DeepQExpReplayAgent,   {Options.TRAINABLE, Options.MONITOR, Options.SAVABLE})
    ]

    

    def __init__(self, ui : UserInterface):
        self.runstate = RunState.CHOOSE_AGENT
        
        self.ui = ui
        # self.parent_runner = prev_runner
        #TODO: go back to previous runner

        self.state = TetrisGameState()
        self.orient = 0
        self.col = 4
        self.high_score = 0

        self.ui.draw_board(self.state.board)
        self.ui.set_score(0, 0)
        self.ui.draw_cur_tet(None, None)
        self.ui.draw_next_tet(None)
        self.show_initial_menu()

        self.agent = None
        self.cur_agent_options = set()
        self.agent_menu_items = []
        self.menu_item_method = {
            AgentMenuItems.WATCH : self.watch_agent,
            AgentMenuItems.TRAIN : self.train_agent,
            AgentMenuItems.LOAD  : self.load_weights
        }
        self.thread = None

    def load_weights(self):
        filename = self.ui.get_str('load checkpoint name')
        # self.ui.logger.log(logging.DEBUG, filename)
        filename = self.agent.__class__.__name__ + '/' + filename
        try:
            # with Path(filename).open('r', encoding='utf-8') as f:
            self.agent.load_weights(filename)
            self.ui.push_text('loaded weights!')
        except FileNotFoundError:
            self.ui.push_text(f'checkpoint {filename} not found')
            sleep(3)
            self.show_agent_menu()


    def save_weights(self):
        filename = self.ui.get_str('save checkpoint name')
        Path(self.agent.__class__.__name__).mkdir(exist_ok=True)
        filename = self.agent.__class__.__name__ + '/' + filename
        # with Path(filename).open('w', encoding='utf-8') as f:
        self.agent.save_weights(filename)
        # self.ui.logger.log(logging.DEBUG, filename)
        self.ui.push_text(f'saved weights to {filename}!')
        if self.runstate == RunState.TRAINING_PAUSED:
            self.ui.push_text('[r] resume viewing')
        else:
            self.ui.push_text('[q] top of AI menu')

    def watch_agent(self):
        self.runstate = RunState.WATCHING
        try:
            while True:
                score, lines, moves = self.watch_agent_game()
                self.ui.push_text(f'score: {score}, lines cleared: {lines}, moves made: {moves}')
        except KeyboardInterrupt:
            self.runstate = RunState.AGENT_MENU
            self.show_agent_menu()
            return
    
    def watch_agent_game(self):
        moves = 0
        lines = 0
        self.state = TetrisGameState()
        self.orient = 0
        self.col = 4
        while True:
            if Options.MONITOR in self.cur_agent_options:
                self.ui.set_text(self.agent.monitor(), self.ui.LEFT)
            # self.ui.logger.log(logging.DEBUG, 'started loop')
            ot : OrientedTetromino = self.state.tet[0]
            # self.ui.logger.log(logging.DEBUG, 'draw board')
            self.ui.draw_board(self.state.board)
            # self.ui.logger.log(logging.DEBUG, 'draw next')
            self.ui.draw_next_tet(ot)
            # self.ui.logger.log(logging.DEBUG, 'set score')
            self.ui.set_score(self.state.score, self.high_score)
            # self.ui.logger.log(logging.DEBUG, 'draw cur tet')
            self.ui.draw_cur_tet(ot, 4)


            # self.ui.logger.log(logging.DEBUG, 'getting move...')
            self.orient, self.col = self.agent.get_best_move(self.state)
            ot = self.state.tet[self.orient]

            self.ui.draw_placement_preview(self.state.board, self.state.tet, self.orient, self.col)
            sleep(0.05)
            self.ui.draw_cur_tet(ot, self.col)
            sleep(0.05)

            moves += 1
            # self.ui.logger.log(logging.DEBUG, 'finished animations')
            try:
                old_board, reward, cleared = self.state.make_move(self.orient, self.col)
            except GameOver:
                break
            if cleared:
                self.ui.celebrate(old_board, reward, cleared)
                self.state.score += reward
                lines += len(cleared)
            # self.ui.logger.log(logging.DEBUG, 'finished loop')
        if self.state.score > self.high_score:
            self.high_score = self.state.score
            self.ui.set_score(self.state.score, self.high_score)
        return self.state.score, lines, moves

    def training_thread(self, epochs, iters):
        self.ui.push_text(f'running {epochs} epochs of {iters} iters')
        for i in range(epochs):
            self.ui.push_text(f'epoch {i}...')
            self.agent.train(iters)
            # self.ui.push_text(f'weights = {list(self.agent.numeric_w.values())}')

    def train_agent(self):
        self.runstate = RunState.TRAINING
        self.ui.set_text(f'training agent {self.agent.agent_name} in new thread...')
        self.ui.push_text('[ctrl][c] to pause the live feed and save weights')
        epochs = 35
        iters = 100
        self.thread = threading.Thread(target=self.training_thread, args=(epochs, iters))
        self.thread.daemon = True
        self.thread.start()
        try:
            while self.thread.is_alive():
                score, lines, moves = self.watch_agent_game()
                self.ui.push_text(f'score: {score}, lines cleared: {lines}, moves made: {moves}')
        except KeyboardInterrupt:
            self.ui.push_text('paused viewing (training still continuing in background)')
            self.ui.push_text('[s] save current weights')
            self.ui.push_text('[r] resume viewing')
            self.ui.push_text('stopping training early is currently unsupported, so please exit using [ctrl][c] if you want to abort')
            self.runstate = RunState.TRAINING_PAUSED
            return
        self.ui.push_text('training finished!')
        self.runstate = RunState.TRAINING_FINISHED
        self.ui.push_text('[s] save current weights')
        self.ui.push_text('[q] top of AI menu')
        self.ui.logger.log(logging.DEBUG, 'train_agent ended')
    
    def resume_training(self):
        self.runstate = RunState.TRAINING
        self.ui.push_text('resuming viewing...')
        try:
            while self.thread.is_alive():
                score, lines, moves = self.watch_agent_game()
                self.ui.push_text(f'score: {score}, lines cleared: {lines}, moves made: {moves}')
        except KeyboardInterrupt:
            self.ui.push_text('paused viewing (training still continuing in background)')
            self.ui.push_text('[s] save current weights')
            self.ui.push_text('[r] resume viewing')
            self.ui.push_text('stopping training early is currently unsupported, so please exit using [ctrl][c] if you want to abort')
            self.runstate = RunState.TRAINING_PAUSED
            return
        self.ui.push_text('training finished!')
        self.runstate = RunState.TRAINING_FINISHED
        self.ui.push_text('[s] save current weights')
        self.ui.push_text('[q] top of AI menu')
        self.ui.logger.log(logging.DEBUG, 'train_agent ended')
    
    def show_initial_menu(self):
        self.ui.set_text('')
        for i, (agent, _) in enumerate(self.installed_agents):
            self.ui.push_text(f'[{i}] {agent.agent_name}')
        self.ui.push_text('[r] record demonstrations')
        self.ui.push_text('[p] play Tetris')

    def show_agent_menu(self):
        self.ui.set_text(f'{self.agent.agent_name}:')
        for i, menu_item in enumerate(self.agent_menu_items):
            self.ui.push_text(f'[{i}] {agent_menu_item_name[menu_item]}')
        self.ui.push_text('[b] back')

    def handle_keypress(self, k: str):
        self.ui.logger.log(logging.DEBUG, 'handling keypress...')
        if self.runstate == RunState.CHOOSE_AGENT:
            try:
                agent, options = self.installed_agents[int(k)]
                self.cur_agent_options = options
                self.agent = agent(self.ui.logger)
                self.agent_menu_items = [AgentMenuItems.WATCH]
                if Options.TRAINABLE in options:
                    self.agent_menu_items.append(AgentMenuItems.TRAIN)
                if Options.SAVABLE in options:
                    # self.agent_menu_items.append(AgentMenuItems.SAVE)
                    self.agent_menu_items.append(AgentMenuItems.LOAD)
                self.runstate = RunState.AGENT_MENU
                self.show_agent_menu()
            except (IndexError, ValueError):
                if k in ['r']:
                    self.ui.switch_runner(2)
                if k in ['p']:
                    self.ui.switch_runner(0)
        
        elif self.runstate == RunState.AGENT_MENU:
            try:
                menu_item = self.agent_menu_items[int(k)]
                self.menu_item_method[menu_item]()
            except (IndexError, ValueError):
                if k in ['b']:
                    self.runstate = RunState.CHOOSE_AGENT
                    self.show_initial_menu()

        elif self.runstate == RunState.TRAINING_PAUSED:
            if k in ['s']:
                self.save_weights()
            if k in ['r']:
                self.resume_training()

        elif self.runstate == RunState.TRAINING_FINISHED:
            if k in ['s']:
                self.save_weights()
            if k in ['q']:
                self.runstate = RunState.CHOOSE_AGENT
                self.show_initial_menu()
