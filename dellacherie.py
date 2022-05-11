from typing import Callable

from base_agent import BaseTetrisAgent
from state import TetrisGameState
from features2 import (eroded_piece_cells, col_transitions, row_transitions,
    holes, landing_height, cumulative_wells)

class DellacherieAgent(BaseTetrisAgent):

    agent_name = 'Dellacherie\'s legendary hand coded agent'

    weights : 'dict[Callable[[TetrisGameState, int, int], float], float]' = {
        eroded_piece_cells: 1.0,
        col_transitions: -1.0,
        row_transitions: -1.0,
        landing_height: -1.0,
        cumulative_wells: -1.0,
        holes: -4.0
    }

    def __init__(self, logger):
        self.logger = logger

    def get_best_move(self, state: TetrisGameState) -> 'tuple[int, int]':
        moves = list(state.get_moves())
        move_scores = {(orient, col): sum(w*f(state, orient, col) for f, w in self.weights.items())
            for orient, col in moves}
        return max(moves, key=lambda m: move_scores[m])
