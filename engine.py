import os
from itertools import permutations
from bag import TILE_VALUES
from board import PREMIUM_SQUARES


def load_dictionary(path='words.txt'):
    with open(path) as f:
        return set(w.strip().upper() for w in f if w.strip().isalpha())


def get_words_from_rack(rack_tiles, word_set):
    """
    Given tiles and the list of words, provide a list of possible plays
    """
    results = set()

    def search(remaining_rack, current_word, tiles_used):

        if len(current_word) >= 2 and current_word in word_set:
            results.add((current_word, tuple(tiles_used)))
        if not remaining_rack:
            return

        seen = set()
        for i, tile in enumerate(remaining_rack):
            if tile in seen:
                continue
            seen.add(tile)
            next_rack = remaining_rack[:i] + remaining_rack[i+1:]
            if tile == '?':
                # try blank as each letter
                for ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    search(next_rack, current_word + ch, tiles_used + [('?', ch)])
            else:
                search(next_rack, current_word + tile, tiles_used + [(tile, tile)])

    search(rack_tiles, '', [])

    return list(results)


def score_move(board, placements, word):
    """
    Score a move including all modifiers and overlaps
    Returns the score value
    """

    placed_positions = {(r, c) for r, c, _, _ in placements}

    word_multiplier = 1
    word_score = 0

    for r, c, letter, is_blank in placements:
        letter_val = 0 if is_blank else TILE_VALUES.get(letter, 0)
        prem = PREMIUM_SQUARES.get((r, c))

        # only apply special tiles to newly placed tiles
        if prem == 'TL':
            letter_val *= 3
        elif prem == 'DL':
            letter_val *= 2
        elif prem == 'TW':
            word_multiplier *= 3
        elif prem == 'DW':
            word_multiplier *= 2

        word_score += letter_val

    # add score for existing tiles in the word (no bonuses yet)
    if placements:
        first_r, first_c, _, _ = placements[0]
        last_r, last_c, _, _ = placements[-1]
        if first_r == last_r:
            # horizontal
            for c in range(first_c, last_c + 1):
                if (first_r, c) not in placed_positions:
                    existing = board.get_letter(first_r, c)
                    if existing:
                        word_score += TILE_VALUES.get(existing, 0)
        else:
            # vertical
            for r in range(first_r, last_r + 1):
                if (r, first_c) not in placed_positions:
                    existing = board.get_letter(r, first_c)
                    if existing:
                        word_score += TILE_VALUES.get(existing, 0)

    total = word_score * word_multiplier

    # 50 piint bingo bonus for playing all letters
    if len(placements) == 7:
        total += 50

    return total


def get_word_at(board, row, col, direction):
    """
    Read the full word on the board starting from the leftmost/topmost letter
    """
    dr, dc = (0, 1) if direction == 'H' else (1, 0)

    # walk back to the start
    r, c = row, col
    while 0 <= r - dr < 15 and 0 <= c - dc < 15 and board.is_occupied(r - dr, c - dc):
        r -= dr
        c -= dc

    word = ''
    while 0 <= r < 15 and 0 <= c < 15 and board.is_occupied(r, c):
        word += board.get_letter(r, c)
        r += dr
        c += dc

    return word


def validate_and_score_placement(board, placements, word_set):
    """
    Check that a placement is valid and return its score.
    Returns (is_valid, score, error_message)
    """
    if not placements:
        return False, 0, "No tiles placed"

    placed_positions = {(r, c) for r, c, _, _ in placements}

    # check all placements are in bounds and on empty squares
    for r, c, _, _ in placements:
        if not (0 <= r < 15 and 0 <= c < 15):
            return False, 0, "Placement out of bounds"
        if board.is_occupied(r, c):
            return False, 0, f"Square ({r},{c}) is already occupied"

    # must all be in same row or same column
    rows = set(r for r, c, _, _ in placements)
    cols = set(c for r, c, _, _ in placements)

    if len(rows) > 1 and len(cols) > 1:
        return False, 0, "Tiles must be placed in a single row or column"

    if len(rows) == 1:
        direction = 'H'
        row = list(rows)[0]
        sorted_placements = sorted(placements, key=lambda x: x[1])
        # check no gaps
        min_c = sorted_placements[0][1]
        max_c = sorted_placements[-1][1]
        for c in range(min_c, max_c + 1):
            if (row, c) not in placed_positions and not board.is_occupied(row, c):
                return False, 0, "Gap in placed tiles"
    else:
        direction = 'V'
        col = list(cols)[0]
        sorted_placements = sorted(placements, key=lambda x: x[0])
        min_r = sorted_placements[0][0]
        max_r = sorted_placements[-1][0]
        for r in range(min_r, max_r + 1):
            if (r, col) not in placed_positions and not board.is_occupied(r, col):
                return False, 0, "Gap in placed tiles"

    # first move must cover center
    if board.is_empty():
        if (7, 7) not in placed_positions:
            return False, 0, "First move must cover the center square (7,7)"
    else:
        # must connect to existing tiles
        connects = False
        for r, c, _, _ in placements:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 15 and 0 <= nc < 15 and board.is_occupied(nr, nc):
                    connects = True
                    break
        if not connects:
            return False, 0, "Tiles must connect to existing words"

    # temporarily place tiles to read words
    temp_board = _temp_place(board, placements)

    # check main word
    if direction == 'H':
        r = list(rows)[0]
        c = sorted_placements[0][1]
    else:
        r = sorted_placements[0][0]
        c = list(cols)[0]

    main_word = get_word_at(temp_board, r, c, direction)
    if main_word not in word_set:
        return False, 0, f"'{main_word}' is not a valid word"

    # check all cross words
    cross_dir = 'V' if direction == 'H' else 'H'
    for pr, pc, _, _ in placements:
        cross_word = get_word_at(temp_board, pr, pc, cross_dir)
        if len(cross_word) > 1 and cross_word not in word_set:
            return False, 0, f"Cross-word '{cross_word}' is not valid"

    total_score = score_move(board, placements, main_word)

    # add cross word scores
    for pr, pc, letter, is_blank in placements:
        cross_word = get_word_at(temp_board, pr, pc, cross_dir)
        if len(cross_word) > 1:
            # score this cross word
            cross_score = _score_cross_word(board, pr, pc, cross_dir, placements)
            total_score += cross_score

    return True, total_score, ""


def _temp_place(board, placements):

    import copy
    temp = copy.deepcopy(board)
    temp.place_tiles(placements)
    return temp


def _score_cross_word(board, anchor_r, anchor_c, direction, new_placements):
    """
    Score a cross word formed by a new word play
    """
    placed_positions = {(r, c): (letter, is_blank) for r, c, letter, is_blank in new_placements}
    dr, dc = (1, 0) if direction == 'V' else (0, 1)

    # find start of cross word
    r, c = anchor_r, anchor_c
    while 0 <= r - dr < 15 and 0 <= c - dc < 15:
        nr, nc = r - dr, c - dc
        if board.is_occupied(nr, nc) or (nr, nc) in placed_positions:
            r, c = nr, nc
        else:
            break

    word_score = 0
    word_multiplier = 1

    while 0 <= r < 15 and 0 <= c < 15:
        if (r, c) in placed_positions:
            letter, is_blank = placed_positions[(r, c)]
            letter_val = 0 if is_blank else TILE_VALUES.get(letter, 0)
            prem = PREMIUM_SQUARES.get((r, c))
            if prem == 'TL':
                letter_val *= 3
            elif prem == 'DL':
                letter_val *= 2
            elif prem == 'TW':
                word_multiplier *= 3
            elif prem == 'DW':
                word_multiplier *= 2
            word_score += letter_val
        elif board.is_occupied(r, c):
            word_score += TILE_VALUES.get(board.get_letter(r, c), 0)
        else:
            break
        r += dr
        c += dc

    return word_score * word_multiplier


def find_best_bot_move(board, rack_tiles, word_set):
    """
    Find the highest scoring valid move for the bot, iterating through possible plays
    Returns (best_placements, best_score) or (None, 0) if no move found
    """
    formable = get_words_from_rack(rack_tiles, word_set)

    best_score = 0
    best_placements = None

    if board.is_empty():
        anchors = [(7, 7)]
    else:
        anchors = _get_anchor_squares(board)

    for word, tiles_used in formable:
        for direction in ['H', 'V']:
            dr, dc = (0, 1) if direction == 'H' else (1, 0)
            for anchor_r, anchor_c in anchors:
                # try placing word such that each position aligns with anchor
                for start_offset in range(len(word)):
                    start_r = anchor_r - start_offset * dr
                    start_c = anchor_c - start_offset * dc

                    placements = _build_placements(board, word, tiles_used, start_r, start_c, direction)
                    if placements is None:
                        continue

                    valid, score, _ = validate_and_score_placement(board, placements, word_set)
                    if valid and score > best_score:
                        best_score = score
                        best_placements = placements

    return best_placements, best_score


def _get_anchor_squares(board):
    """
    Provide possible starting squares for a word
    """
    anchors = set()
    for r in range(15):
        for c in range(15):
            if not board.is_occupied(r, c):
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 15 and 0 <= nc < 15 and board.is_occupied(nr, nc):
                        anchors.add((r, c))
                        break
    return list(anchors)


def _build_placements(board, word, tiles_used, start_r, start_c, direction):
    """
    Build a placement list for a word starting at (start_r, start_c).
    """
    dr, dc = (0, 1) if direction == 'H' else (1, 0)
    placements = []
    tile_index = 0  # index into tiles_used for unplaced letters

    for i, letter in enumerate(word):
        r = start_r + i * dr
        c = start_c + i * dc

        if not (0 <= r < 15 and 0 <= c < 15):
            return None

        if board.is_occupied(r, c):
            # must match existing tile
            if board.get_letter(r, c) != letter:
                return None
            # no tile consumed from rack here
        else:
            # need to place from rack
            if tile_index >= len(tiles_used):
                return None
            rack_tile, resolved = tiles_used[tile_index]
            if resolved != letter:
                return None
            is_blank = rack_tile == '?'
            placements.append((r, c, letter, is_blank))
            tile_index += 1

    # all rack tiles should be consumed
    if tile_index != len(tiles_used):
        return None

    return placements