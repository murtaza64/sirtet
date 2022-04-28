import threading
from time import sleep
import logging

from ui import UserInterface
from state import TetrisGameState
from base_runner import Runner
from base_agent import BaseTetrisAgent
from learn import TetrisQLearningAgent
from tetrominoes import OrientedTetromino
from board import GameOver

class Options:
    TRAINABLE = 1
    SAVABLE = 2
    MONITOR = 3

class RunState:
    CHOOSE_AGENT = 0
    AGENT_MENU = 1
    TRAINING = 2
    WATCHING = 3

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
        (TetrisQLearningAgent, {Options.TRAINABLE, Options.MONITOR})
    ]

    

    def __init__(self, ui : UserInterface, prev_runner : Runner):
        self.runstate = RunState.CHOOSE_AGENT
        
        self.ui = ui
        self.parent_runner = prev_runner
        #TODO: go back to previous runner

        self.state = TetrisGameState()
        self.orient = 0
        self.col = 4

        self.ui.draw_board(self.state.board)
        self.ui.set_score(0)
        self.ui.draw_cur_tet(None, None)
        self.ui.draw_next_tet(None)
        self.show_initial_menu()

        self.agent = None
        self.agent_menu_items = []
        self.menu_item_method = {
            AgentMenuItems.WATCH : self.watch_agent,
            AgentMenuItems.TRAIN : self.train_agent
        }
        self.thread = None

    def watch_agent(self):
        pass
    
    def watch_agent_game(self):
        moves = 0
        lines = 0
        self.state = TetrisGameState()
        self.orient = 0
        self.col = 4
        while True:
            self.ui.logger.log(logging.DEBUG, 'started loop')
            ot : OrientedTetromino = self.state.tet[0]
            self.ui.logger.log(logging.DEBUG, 'draw board')
            self.ui.draw_board(self.state.board)
            self.ui.logger.log(logging.DEBUG, 'draw next')
            self.ui.draw_next_tet(ot)
            self.ui.logger.log(logging.DEBUG, 'set score')
            self.ui.set_score(self.state.score)
            self.ui.logger.log(logging.DEBUG, 'draw cur tet')
            self.ui.draw_cur_tet(ot, 4)


            self.ui.logger.log(logging.DEBUG, 'getting move...')
            self.orient, self.col = self.agent.get_best_move(self.state)
            ot = self.state.tet[self.orient]

            self.ui.draw_placement_preview(self.state.board, self.state.tet, self.orient, self.col)
            sleep(0.05)
            self.ui.draw_cur_tet(ot, self.col)
            sleep(0.05)

            moves += 1
            self.ui.logger.log(logging.DEBUG, 'finished animations')
            try:
                old_board, reward, cleared = self.state.make_move(self.orient, self.col)
            except GameOver:
                break
            if cleared:
                self.ui.celebrate(old_board, reward, cleared)
                self.state.score += reward
                lines += len(cleared)
            self.ui.logger.log(logging.DEBUG, 'finished loop')

        return self.state.score, lines, moves

    def training_thread(self, epochs, iters):
        self.ui.push_text(f'running {epochs} epochs of {iters} iters')
        for i in range(epochs):
            self.ui.push_text(f'epoch {i}...')
            self.agent.train(iters)
            self.ui.push_text(f'weights = {list(self.agent.numeric_w.values())}')

    def train_agent(self):
        self.runstate = RunState.TRAINING
        self.ui.set_text(f'training agent {self.agent.agent_name} in new thread...')
        epochs = 35
        iters = 100
        self.thread = threading.Thread(target=self.training_thread, args=(epochs, iters))
        self.thread.start()

        while self.thread.is_alive():
            score, lines, moves = self.watch_agent_game()
            self.ui.push_text(f'score: {score}, lines cleared: {lines}, moves made: {moves}')
        self.ui.logger.log(logging.DEBUG, 'train_agent ended')
    
    def show_initial_menu(self):
        self.ui.set_text('')
        for i, (agent, _) in enumerate(self.installed_agents):
            self.ui.push_text(f'[{i}] {agent.agent_name}')

    def show_agent_menu(self):
        self.ui.set_text(f'select option for {self.agent.agent_name}:')
        for i, menu_item in enumerate(self.agent_menu_items):
            self.ui.push_text(f'[{i}] {agent_menu_item_name[menu_item]}')

    def handle_keypress(self, k: str):
        self.ui.logger.log(logging.DEBUG, 'handling keypress...')
        if self.runstate == RunState.CHOOSE_AGENT:
            try:
                agent, options = self.installed_agents[int(k)]
                self.agent = agent(self.ui.logger)
                self.agent_menu_items = [AgentMenuItems.WATCH]
                if Options.TRAINABLE in options:
                    self.agent_menu_items.append(AgentMenuItems.TRAIN)
                if Options.SAVABLE in options:
                    self.agent_menu_items.append(AgentMenuItems.SAVE)
                    self.agent_menu_items.append(AgentMenuItems.LOAD)
                self.runstate = RunState.AGENT_MENU
                self.show_agent_menu()
            except (IndexError, ValueError):
                return
        
        if self.runstate == RunState.AGENT_MENU:
            try:
                self.menu_item_method[int(k)]()
            except (IndexError, ValueError):
                return
