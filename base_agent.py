
from state import TetrisGameState

class BaseTetrisAgent:

    agent_name = 'base class for Tetris agents'

    def get_move(self, state : TetrisGameState) -> 'tuple[int, int]':
        '''
        given a TetrisGameState, return selected move as (orient, col)
        '''
        pass

    def train(self, iters : int):
        pass
