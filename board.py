
PREMIUM_SQUARES = {}

triple_word = [
    (0,0),(0,7),(0,14),(7,0),(7,14),(14,0),(14,7),(14,14)
]
double_word = [
    (1,1),(2,2),(3,3),(4,4),(1,13),(2,12),(3,11),(4,10),
    (10,4),(11,3),(12,2),(13,1),(10,10),(11,11),(12,12),(13,13),(7,7)
]
triple_letter = [
    (1,5),(1,9),(5,1),(5,5),(5,9),(5,13),
    (9,1),(9,5),(9,9),(9,13),(13,5),(13,9)
]
double_letter = [
    (0,3),(0,11),(2,6),(2,8),(3,0),(3,7),(3,14),
    (6,2),(6,6),(6,8),(6,12),(7,3),(7,11),
    (8,2),(8,6),(8,8),(8,12),(11,0),(11,7),(11,14),
    (12,6),(12,8),(14,3),(14,11)
]

for sq in triple_word:
    PREMIUM_SQUARES[sq] = 'TW'
for sq in double_word:
    PREMIUM_SQUARES[sq] = 'DW'
for sq in triple_letter:
    PREMIUM_SQUARES[sq] = 'TL'
for sq in double_letter:
    PREMIUM_SQUARES[sq] = 'DL'


class Board:
    def __init__(self):
        # grid stores tuples of letter, is_blank
        self.grid = [[None] * 15 for _ in range(15)]

    def place_tiles(self, placements):
        # placements: list of (row, col, letter, is_blank)
        for row, col, letter, is_blank in placements:
            self.grid[row][col] = (letter, is_blank)

    def get_letter(self, row, col): # return the letter at a specific position
        if self.grid[row][col] is None:
            return None
        return self.grid[row][col][0]

    def is_empty(self):
        for row in self.grid:
            for cell in row:
                if cell is not None:
                    return False
        return True

    def is_occupied(self, row, col):
        return self.grid[row][col] is not None

    def display(self):
        COLORS = {
            'TW': '\033[38;5;88m',  # dark red (triple w)
            'DW': '\033[31m',  # light red (double w)
            'TL': '\033[94m',  # blue (triple letter)
            'DL': '\033[38;5;117m',  # light blue (double letter)
        }
        RESET = '\033[0m'

        print('   ' + ' '.join(f'{i:2}' for i in range(15)))
        for r in range(15):
            row_str = f'{r:2} '
            for c in range(15):
                cell = self.grid[r][c]
                if cell is not None:
                    letter, is_blank = cell
                    if is_blank:
                        row_str += f' {letter.lower()}{RESET}'
                    else:
                        row_str += f'  {letter}'
                else:
                    prem = PREMIUM_SQUARES.get((r, c))
                    if prem:
                        row_str += f'{COLORS[prem]}{prem:>3}{RESET}'
                    elif r == 7 and c == 7:
                        row_str += '  *'
                    else:
                        row_str += '  .'
            print(row_str)
        print()