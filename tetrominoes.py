from itertools import product
from lib import render_block, render_block_curses

def lastindex(l, item):
    try:
        return len(l) - l[::-1].index(item) - 1
    except ValueError:
        return -1
class OrientedTetromino:
    def __init__(self, shape, orientation, letter):
        self._blocks = []
        self.shapestr = shape
        self.orientation = orientation
        self.letter = letter

        for line in reversed(shape.strip().split()):
            self._blocks.append([1 if c == '#' else 0 for c in line])

        self.height = sum([int(any(l)) for l in self._blocks])
        self.width = max([lastindex(l, 1) for l in self._blocks]) + 1

    def __getitem__(self, slc):
        try:
            return self._blocks[slc[1]][slc[0]]
        except IndexError:
            return 0

    def __repr__(self):
        return f'OrientedTetromino({self.letter}, {self.orientation})'

    def __str__(self):
        s = ''
        for row in reversed(self._blocks):
            rs = ''
            if not any(row):
                continue
            for block in row:
                rs += render_block(self.letter if block else 0, skip_zeros=True)
            s += rs.rstrip() + '\n'
        return s[:-1]
    
    def __hash__(self):
        return hash(self.letter + str(self.orientation))

    def offsets(self):
        return product(range(self.width), range(self.height))

    def draw(self, scr, yi, col, attrs=0, empty=False, autocolor=True):
        x, y = 2*col, yi
        for row in reversed(self._blocks):
            if not any(row):
                continue
            for block in row:
                if block:
                    render_block_curses(self.letter, scr, y, x, 
                            attrs=attrs, empty=empty, autocolor=autocolor)
                x += 2
            y += 1
            x = 2*col



class Tetromino:
    def __init__(self, shapes, letter):
        self.orientations : 'list[OrientedTetromino]' = []
        self.letter = letter

        for i, s in enumerate(shapes):
            self.orientations.append(OrientedTetromino(s, i, letter))

    def __getitem__(self, slc) -> OrientedTetromino:
        return self.orientations[slc % len(self.orientations)]

    def __repr__(self):
        return f'Tetromino({self.letter})'

    def __iter__(self):
        return iter(self.orientations)
    
    def __hash__(self):
        return hash(self.letter)

    def n_orientations(self):
        return len(self.orientations)


tetrominoes = {
    's': Tetromino([
        '''
        ....
        ....
        .##.
        ##..
        ''',
        '''
        ....
        #...
        ##..
        .#..
        '''
    ], 's'),
    'z': Tetromino([
        '''
        ....
        ....
        ##..
        .##.
        ''',
        '''
        ....
        .#..
        ##..
        #...
        '''
    ], 'z'),
    'o': Tetromino([
        '''
        ....
        ....
        ##..
        ##..
        '''
    ], 'o'),
    'j': Tetromino([
        '''
        ....
        .#..
        .#..
        ##..
        ''',
        '''
        ....
        ....
        #...
        ###.
        ''',
        '''
        ....
        ##..
        #...
        #...
        ''',
        '''
        ....
        ....
        ###.
        ..#.
        '''
    ], 'j'),
    'l': Tetromino([
        '''
        ....
        #...
        #...
        ##..
        ''',
        '''
        ....
        ....
        ###.
        #...
        ''',
        '''
        ....
        ##..
        .#..
        .#..
        ''',
        '''
        ....
        ....
        ..#.
        ###.
        '''
    ], 'l'),
    't': Tetromino([
        '''
        ....
        ....
        .#..
        ###.
        ''',
        '''
        ....
        #...
        ##..
        #...
        ''',
        '''
        ....
        ....
        ###.
        .#..
        ''',
        '''
        ....
        .#..
        ##..
        .#..
        '''
    ], 't'),
    'i': Tetromino([
        '''
        ....
        ....
        ....
        ####
        ''',
        '''
        #...
        #...
        #...
        #...
        '''
    ], 'i')
}

tetlist = list(tetrominoes.values())