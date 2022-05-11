from itertools import zip_longest
import curses

class Colors:
    prefix = "\033["
    reset = f'{prefix}0m'
    black = "30m"
    red = "31m"
    green = "32m"
    orange = "33m"
    yellow = "33;1m"
    blue = "34m"
    magenta = "35m"
    cyan = "36m"
    white = "37m"

block_colors = {
    0:   Colors.black,
    'z': Colors.red,
    'l': Colors.orange,
    'o': Colors.yellow,
    's': Colors.green,
    'j': Colors.blue,
    't': Colors.magenta,
    'i': Colors.cyan
}

color_attrs = {}

def colorize(s, color):
    return f'{Colors.prefix}{color}{s}{Colors.reset}'

def render_block(letter=0, empty=False, skip_zeros=False):
    if skip_zeros and not letter:
        return '  '
    if empty:
        return colorize('⬜', block_colors[letter])
    return colorize('⬛', block_colors[letter])

def render_block_curses(letter, scr, y=None, x=None, 
        autocolor=True, attrs=None, empty=False, skip_zeros=False):
    if y < 0 or x < 0:
        return
    att = 0
    if autocolor:
        att |= color_attrs[letter]
    if attrs is not None:
        att |= attrs
    # char = '⬜' if empty else '⬛'
    char = '⬜' if empty else '██'

    if skip_zeros and not letter:
        return scr.addstr('  ')
    if x is not None and y is not None:
        return scr.addstr(y, x, char, att)
    return scr.addstr(char, att)


FULLWIDTH_DELTA =  ord('Ａ') - ord('A')

def fullwidth(s):
    out = ''
    for c in s:
        out += chr(ord(c) + FULLWIDTH_DELTA)
    return out

def linewidth(s):
    total = 0
    i = 0
    while i < len(s):
        if s[i:i+2] == Colors.prefix:
            while s[i] != 'm':
                i += 1
        elif '\uFF00' <= s[i] <= '\uFF60' or s[i] in '⬜⬛':
            total += 2
        else:
            total += 1
        i += 1
    return total

def horizontal_str(strings, sep=fullwidth('|')):
    widths = [max([linewidth(line) for line in s.splitlines()]) for s in strings]
    heights = [len(s.splitlines()) for s in strings]
    newstrings = []
    for s in strings:
        while len(s.splitlines()) < max(heights):
            s = '\n' + s
        newstrings.append(s)
    # print(lengths)
    out = ''
    z = zip_longest(*[s.splitlines() for s in newstrings], fillvalue='')
    for row in z:
        for i, line in enumerate(row):
            out += line
            out += ' ' * (widths[i] - linewidth(line))
            if i != len(row):
                out += sep
        out += '\n'
    return out


def brackethandler(k, win):
    if k != '[':
        return k
    try:
        return BRACKET_MAP[win.getkey()]
    except KeyError:
        return '['

BRACKET_MAP = {
    'A': 'UP',
    'B': 'DOWN',
    'C': 'RIGHT',
    'D': 'LEFT'
}

def split_into_lines(inp, length):
    lines = inp.split('\n')
    ret = []
    for s in lines:
        while s:
            ret.append(s[:length])
            s = s[length:]
    return ret

CURSES_COLOR_MAP = {
    'z': curses.COLOR_RED,
    'l': curses.COLOR_YELLOW,
    'o': curses.COLOR_YELLOW,
    's': curses.COLOR_GREEN,
    'j': curses.COLOR_BLUE,
    't': curses.COLOR_MAGENTA,
    'i': curses.COLOR_CYAN
}