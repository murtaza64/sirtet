#pylint:disable=unused-argument
import itertools as it

from board import WIDTH, HEIGHT
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
