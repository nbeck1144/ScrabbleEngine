from bag import TILE_VALUES


class Rack:
    def __init__(self, bag):
        self.tiles = []
        self.refill(bag)

    def refill(self, bag):
        needed = 7 - len(self.tiles)
        if needed > 0:
            self.tiles.extend(bag.draw(needed))

    def remove_tiles(self, tiles_to_remove):
        # tiles_to_remove is a list of tile letters
        temp = self.tiles[:]
        for t in tiles_to_remove:
            temp.remove(t)
        self.tiles = temp

    def has_tiles(self, tiles):
        temp = self.tiles[:]
        for t in tiles:
            if t in temp:
                temp.remove(t)
            else:
                return False
        return True

    def __str__(self):
        # returns a string that
        return ' '.join(self.tiles)