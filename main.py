import random

import sys
from bag import Bag
from board import Board
from rack import Rack
from engine import load_dictionary, validate_and_score_placement, find_best_bot_move


def parse_human_move(input_str, rack, board, word_set):
    """
    Parse input like: WORD ROW COL H/V, including letters that are already there
    """
    # separate input into requisite parts
    parts = input_str.strip().split()
    if len(parts) < 4:
        return None, "Usage: WORD ROW COL H/V  (use lowercase for blank tiles)"


    word_input = parts[0]
    try:
        row = int(parts[1])
        col = int(parts[2])
    except ValueError:
        return None, "Row and col must be integers"

    direction = parts[3].upper()
    if direction not in ('H', 'V'):
        return None, "Direction must be Horizontal (input H) or Vertical (input V)"

    if direction == 'H':
        dr, dc = (0, 1)
    else:
        dr, dc = (1, 0)
    rack_copy = rack.tiles[:]
    placements = []

    for i, ch in enumerate(word_input):
        r = row + i * dr
        c = col + i * dc

        if not (0 <= r < 15 and 0 <= c < 15):
            return None, f"Position ({r},{c}) is out of bounds"

        letter = ch.upper()
        is_blank = ch.islower()

        if board.is_occupied(r, c):
            # tile already on boardd
            existing = board.get_letter(r, c)
            if existing != letter:
                return None, f"Board already has '{existing}' at ({r},{c}), not '{letter}'"
            continue

        # not on board, need to pull from rack
        if is_blank:
            if '?' in rack_copy:
                rack_copy.remove('?')
            else:
                return None, "You don't have enough blank tiles"
        else:
            if letter in rack_copy:
                rack_copy.remove(letter)
            else:
                return None, f"You don't have the tile '{letter}'"

        placements.append((r, c, letter, is_blank))

    if not placements:
        return None, "No new tiles placed — all squares already occupied"

    return placements, None


def human_turn(board, rack, bag, word_set):
    # Begin the human turn with rack print and prompting
    print(f"\nYour rack: {rack}")
    print("Enter move as: WORD ROW COL H/V  (if you have blank, indicate with lowercase)")
    print("Or type 'pass' to pass, 'exchange TILES' to swap tiles")

    while True:
        user_input = input("> ").strip()

        if user_input.lower() == 'pass':
            return 0, True  # score, passed

        if user_input.lower().startswith('exchange'):
            parts = user_input.split()
            if len(parts) < 2:
                print("Usage: exchange TILES  e.g. exchange ABC  (use ? for blank)")
                continue

            if bag.remaining() < 7:
                print("Not enough tiles in the bag to exchange (need at least 7).")
                continue

            tiles_to_exchange = list(parts[1].upper())

            # make sure the player actually has the tiles they wanted to plaY
            rack_copy = rack.tiles[:]
            valid = True
            for t in tiles_to_exchange:
                if t in rack_copy:
                    rack_copy.remove(t)
                else:
                    print(f"You don't have the tile '{t}' in your rack.")
                    valid = False
                    break

            if not valid:
                continue

            # remove from rack, draw new ones, then return old ones to bag
            rack.remove_tiles(tiles_to_exchange)
            new_tiles = bag.draw(len(tiles_to_exchange))
            rack.tiles.extend(new_tiles)

            # put the exchanged tiles back in the bag and reshuffle
            bag.tiles.extend(tiles_to_exchange)
            import random
            random.shuffle(bag.tiles)

            print(f"Exchanged {len(tiles_to_exchange)} tile(s). New rack: {rack}")
            return 0, True
        placements, err = parse_human_move(user_input, rack, board, word_set)
        if err:
            print(f"Error: {err}")
            continue

        valid, score, err = validate_and_score_placement(board, placements, word_set)
        if not valid:
            print(f"Invalid move: {err}")
            continue

        # figure out which rack tiles were used
        tiles_consumed = []
        for r, c, letter, is_blank in placements:
            tiles_consumed.append('?' if is_blank else letter)

        rack.remove_tiles(tiles_consumed)
        board.place_tiles(placements)
        return score, False


def bot_turn(board, rack, word_set):
    placements, score = find_best_bot_move(board, rack.tiles, word_set)

    # bot has no valid moves
    if not placements:
        print("Bot passes.")
        return 0, True

    # indicate consumed tiles
    tiles_consumed = []
    for r, c, letter, is_blank in placements:
        tiles_consumed.append('?' if is_blank else letter)

    rack.remove_tiles(tiles_consumed)
    board.place_tiles(placements)

    # show what the bot played
    word_played = ''.join(letter for _, _, letter, _ in placements)
    print(f"Bot played '{word_played}' for {score} points.")
    return score, False


def main():
    try:
        word_set = load_dictionary('words.txt')
    except FileNotFoundError:
        print("words.txt not found. Please download a word list and save it as words.txt")
        sys.exit(1)

    print(f"Loaded {len(word_set)} words.")

    bag = Bag()
    board = Board()
    human_rack = Rack(bag)
    bot_rack = Rack(bag)

    human_score = 0
    bot_score = 0
    consecutive_passes = 0

    print("\nLet's play SCRABBLE!")

    while True:
        board.display()
        print(f"Score — You: {human_score}  |  Bot: {bot_score}")

        # human turn
        score, passed = human_turn(board, human_rack, bag, word_set)
        human_score += score

        if passed:
            consecutive_passes += 1
        else:
            consecutive_passes = 0
            human_rack.refill(bag)

        # check end conditions
        if not human_rack.tiles and bag.is_empty():
            print("You used all your tiles! Game over")
            break
        if consecutive_passes >= 6:
            print("Game over (6 consecutive passes)")
            break

        board.display()
        print(f"Score — You: {human_score}  |  Bot: {bot_score}")

        # bot turn
        score, passed = bot_turn(board, bot_rack, word_set)
        bot_score += score

        if passed:
            consecutive_passes += 1
        else:
            consecutive_passes = 0
            bot_rack.refill(bag)

        # check end conditions for bot
        if not bot_rack.tiles and bag.is_empty():
            print("Bot used all its tiles! Game over")
            break
        if consecutive_passes >= 6:
            print("Game over (6 consecutive passes)")
            break

    # final scores
    print("\nFINAL SCORES")
    print(f"You: {human_score}")
    print(f"Bot: {bot_score}")
    if human_score > bot_score:
        print("You win!")
    elif bot_score > human_score:
        print("Bot wins!")
    else:
        print("It's a tie!")


if __name__ == '__main__':
    main()