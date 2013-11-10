import Tkinter
from settings import settings

BLOCKSIZE = 20
PADDING = 4

color_mapping = {
    'a': ('black', 'obstacle'),
    's': ('#ddd', None),
    'g': ('darkgreen', 'spawn'),
    'h': ('lightgreen', None),
    'r': ('darkred', None),
    't': ('pink', None),
}

def print_instructions():
    print '''
I made this map editor to use for myself. Therefore, it might not seem
very user-friendly, but it's not that hard. There are just a bunch of
keyboard shortcuts to use.

Game-related colors
===================
[a] paint black (obstacle)
[s] erase (walking space)
[g] paint green (spawn point)

Just for yourself
=================
[h] paint light green
[r] paint red
[t] paint pink

Other functions
===============
[d] fill board with selected color
[f] print map data to console (save as .py to create a map file)
[i] invert black and white colors
'''

class MapEditor:
    def __init__(self, settings.board_size, blocksize, padding):
        self._settings.board_size = settings.board_size
        self._blocksize = blocksize
        self._padding = padding
        self.make_canvas()

    def make_canvas(self):
        root = Tkinter.Tk()
        size = (self._blocksize + self._padding) * self._settings.board_size + self._padding * 2 + 40

        self._canvas = Tkinter.Canvas(root, width=size, height=size)
        self._rect_items = []
        self._colors = []
        self._pressed = False

        self.prepare_backdrop(size)
        self.set_color('black')
        self.bind_events()

        self._canvas.pack()
        root.title('robot game map editor')
        root.mainloop()

    def prepare_backdrop(self, size):
        for y in range(self._settings.board_size):
            for x in range(self._settings.board_size):
                item = self._canvas.create_rectangle(
                    x * (self._blocksize + self._padding) + self._padding + 20, y * (self._blocksize + self._padding) + self._padding + 20,
                    (x+1) * (self._blocksize + self._padding) + 20, (y+1) * (self._blocksize + self._padding) + 20,
                    fill='#ddd',
                    width=0)
                self._colors.append('#ddd')
                self._rect_items.append(item)
        self._bar = self._canvas.create_rectangle(0, 0, size, 15, width=0)

    def set_color(self, color):
        self._current_color = color
        self._canvas.itemconfigure(self._bar, fill=self._current_color)

    def bind_events(self):
        self._canvas.bind_all('<Button-1>', self.click_handler)
        self._canvas.bind_all('<B1-Motion>', self.move_handler)
        self._canvas.bind_all('<ButtonRelease-1>', self.release_handler)
        self._canvas.bind_all('<Key>', self.key_handler)

    def paint_square(self, tk_event=None, item_id=None):
        if tk_event is None and item_id is None:
            raise Exception('must supply either tk_event or item_id')

        if item_id is None:
            try:
                widget = tk_event.widget.find_closest(tk_event.x, tk_event.y)
                item_id = widget[0] - 1
            except:
                return

        if 0 <= item_id < len(self._rect_items):
            self._canvas.itemconfigure(self._rect_items[item_id], fill=self._current_color)
            self._colors[item_id] = self._current_color

    def click_handler(self, event):
        self._pressed = True
        self.paint_square(tk_event=event)
    
    def move_handler(self, event):
        if self._pressed:
            self.paint_square(tk_event=event)

    def release_handler(self, event):
        self._pressed = False

    def paint_all(self):
       for i, item in enumerate(self._rect_items):
            self.paint_square(item_id=i)
            self._canvas.itemconfigure(item, fill=self._current_color)

    def print_map(self):
        coords = {}
        label_mapping = dict(color_mapping.values())

        for color, label in label_mapping.iteritems():
            if label is not None:
                coords[label] = []

        for i, color in enumerate(self._colors):
            if color in label_mapping and label_mapping[color] is not None:
                coords[label_mapping[color]].append((i % self._settings.board_size, int(i / self._settings.board_size)))
        print coords

    def invert_colors(self):
        old_color = self._current_color
        for i, c in enumerate(self._colors):
            if c == '#ddd':
                self._current_color = 'black'
            elif c == 'black':
                self._current_color = '#ddd'

            self.paint_square(item_id=i)
            self._colors[i] = self._current_color
        self._current_color = old_color

    def key_handler(self, event):
        global color_mapping

        if event.char in color_mapping:
            self.set_color(color_mapping[event.char][0])

        func_map = {
            'd': self.paint_all,
            'f': self.print_map,
            'i': self.invert_colors
        }

        if event.char in func_map:
            func_map[event.char]()

if __name__ == '__main__':
    print_instructions()
    MapEditor(settings.board_size, BLOCKSIZE, PADDING)
