# users will import rg to be able to use robot game functions
import math
import operator

settings = None

# constants

CENTER_POINT = None

def after_settings():
    global CENTER_POINT
    global settings
    CENTER_POINT = (int(settings.board_size / 2), int(settings.board_size / 2))

def set_settings(s):
    global settings
    settings = s
    after_settings()

##############################

dist = lambda p1, p2: math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
wdist = lambda p1, p2: abs(p2[0]-p1[0]) + abs(p2[1]-p1[1])

def loc_types(loc):
    for i in range(2):
        if not (0 <= loc[i] < settings.board_size):
            return ['invalid']
    types = ['normal']
    if loc in settings.spawn_coords:
        types.append('spawn')
    if loc in settings.obstacles:
        types.append('obstacle')
    return types

def locs_around(loc, filter_out=None):
    filter_out = filter_out or []
    offsets = ((0, 1), (1, 0), (0, -1), (-1, 0))
    locs = []

    for o in offsets:
        new_loc = tuple(map(operator.add, loc, o))
        if len(set(filter_out) & set(loc_types(new_loc))) == 0:
            locs.append(new_loc)
    return locs

def toward(curr, dest):
    if curr == dest:
        return curr

    x0, y0 = curr
    x, y = dest
    x_diff, y_diff = x - x0, y - y0

    if abs(x_diff) < abs(y_diff):
        return (x0, y0 + y_diff / abs(y_diff))
    return (x0 + x_diff / abs(x_diff), y0)
