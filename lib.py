class Colors:
    pref = "\033["
    reset = f'{pref}0m'
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
    0:   Colors.white,
    'z': Colors.red,
    'l': Colors.orange,
    'o': Colors.yellow,
    's': Colors.green,
    'j': Colors.blue,
    't': Colors.magenta,
    'i': Colors.cyan
}


def colorize(s, color):
    return f'{color}{s}{Colors.reset}'

def render_block(letter=0):
    return colorize('⬜', block_colors[letter])

FULLWIDTH_DELTA =  ord('Ａ') - ord('A')

def fullwidth(c):
    return chr(ord(c) + FULLWIDTH_DELTA)
