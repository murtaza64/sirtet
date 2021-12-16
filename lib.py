from itertools import zip_longest


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


def colorize(s, color):
    return f'{Colors.prefix}{color}{s}{Colors.reset}'

def render_block(letter=0, empty=False, skip_zeros=False):
    if skip_zeros and not letter:
        return '  '
    if empty:
        return colorize('⬜', block_colors[letter])
    return colorize('⬛', block_colors[letter])

FULLWIDTH_DELTA =  ord('Ａ') - ord('A')

def fullwidth(c):
    return chr(ord(c) + FULLWIDTH_DELTA)

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
