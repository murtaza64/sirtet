from lib import render_block

class OrientedTetromino:
    def __init__(self, shape, orientation, letter):
        self._blocks = []
        self.shapestr = shape
        self.orientation = orientation
        self.letter = letter

        for line in reversed(shape.strip().split()):
            self._blocks.append([1 if c == '#' else 0 for c in line])

    def __getitem__(self, slc):
        return self._blocks[slc[1]][slc[0]]

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



class Tetromino:
    def __init__(self, shapes, letter):
        self.orientations : 'list[OrientedTetromino]' = []
        self.letter = letter

        for i, s in enumerate(shapes):
            self.orientations.append(OrientedTetromino(s, i, letter))

    def __getitem__(self, slc):
        return self.orientations[slc]

    def __repr__(self):
        return f'Tetromino({self.letter})'

    def __iter__(self):
        return iter(self.orientations)



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
