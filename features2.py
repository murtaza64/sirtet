'''
The features here are written somewhat more cleanly than the old features used in 
the old Q-learning agent, hence separation into its own module.
The signature of all features is f(state, orient, col) -> number
'''

from typing import Callable

from state import TetrisGameState
from board import TetrisBoard, HEIGHT, WIDTH

# def next_board_feature(f : 'Callable[[TetrisBoard], float]', default=1.0):
#     '''
#     this decorator transforms features that are only based on the successor state
#     of the form `board -> float` into the desired form of `state -> orient -> col -> float`
#     '''
#     def g(state : TetrisGameState, orient, col):
#         gameover, dummy, _, _ = state.generate_move_context(orient, col)
#         if gameover:
#             return default
#         return f(dummy)
#     return g

def holes(state : TetrisGameState, orient, col):
    '''
    count number of holes in board resulting from action (normalized to [0, 1])
    '''
    
    #this preamble is standard for move-agnostic features
    gameover, board, _, _ = state.generate_move_context(orient, col)
    if gameover:
        return 0

    h = 0
    for x, y in board.coords():
        if not board[x, y]:
            for ty in range(y + 1, HEIGHT):
                if board[x, ty]:
                    h += 1
                    break
    return h/200

def landing_height(state : TetrisGameState, orient, col):
    '''
    height where placed piece lands (0 is the bottom)
    '''

    gameover, dummy, yi, cleared = state.generate_move_context(orient, col)
    if gameover:
        return 1
    yi = state.board.place_tetromino(state.tet, orient, col, dry_run=True)
    return yi

def eroded_piece_cells(state : TetrisGameState, orient, col):
    '''
    from Dellacherie; <lines cleared> * <blocks in placed tetromino cleared>
    '''
    gameover, dummy, yi, cleared = state.generate_move_context(orient, col)
    if gameover:
        return 0
    relative_cleared = [i - yi for i in cleared]
    ot = state.tet[orient]
    cleared_bricks = 0
    for i in relative_cleared:
        for dx in range(ot.width):
            if ot[dx, i]:
                cleared_bricks += 1
    return cleared_bricks*len(cleared)

def col_transitions(state : TetrisGameState, orient, col):
    '''
    number of vertical cell pairs which contain both an empty space and a block
    '''

    gameover, board, _, _ = state.generate_move_context(orient, col)
    if gameover:
        return 0

    transitions = 0
    for x in range(WIDTH):
        for y in range(HEIGHT-1):
            if (board[x, y] and not board[x, y+1]
                    or board[x, y+1] and not board[x, y]):
                transitions += 1
    return transitions

def row_transitions(state : TetrisGameState, orient, col):
    '''
    number of horizontal cell pairs which contain both an empty space and a block
    '''

    gameover, board, _, _ = state.generate_move_context(orient, col)
    if gameover:
        return 0

    transitions = 0
    for x in range(WIDTH-1):
        for y in range(HEIGHT):
            if (board[x, y] and not board[x+1, y]
                    or board[x+1, y] and not board[x, y]):
                transitions += 1
    return transitions
    
def cumulative_wells(state : TetrisGameState, orient, col):
    '''
    Dellacherie: sum over wells (1 + 2 + ... + depth(well))

    well defined as vertical sequence of empty cells with blocks left and right 
    '''

    gameover, board, _, _ = state.generate_move_context(orient, col)
    if gameover:
        return 0

    total = 0
    for x in range(WIDTH):
        y = HEIGHT-1
        cur_well_depth = 0
        while y >= 0:
            if (not board[x, y] 
                    and (x == 0 or board[x-1, y])
                    and (x == WIDTH-1 or board[x+1, y])):
                cur_well_depth += 1
            elif cur_well_depth:
                total += cur_well_depth * (cur_well_depth + 1) / 2 # sum (1..depth)
                cur_well_depth = 0
            y -= 1
        total += cur_well_depth * (cur_well_depth + 1) / 2

    return total

