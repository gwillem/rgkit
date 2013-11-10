import Tkinter
import game

class Render:
    def __init__(self, game_inst, settings, block_size=20):
        self._settings = settings
        self._blocksize = block_size
        self._winsize = block_size * self._settings.board_size + 40
        self._game = game_inst
        self._colors = game.Field(self._settings.board_size)

        self._master = Tkinter.Tk()
        self._master.title('robot game')
        self._win = Tkinter.Canvas(self._master, width=self._winsize, height=self._winsize + self._blocksize * 7/4)
        self._win.pack()

        self.prepare_backdrop(self._win)
        self._label = self._win.create_text(self._blocksize/2, self._winsize + self._blocksize/2,
            anchor='nw', font='TkFixedFont', fill='white')

        self.callback()
        self._win.mainloop()

    def prepare_backdrop(self, win):
        self._win.create_rectangle(0, 0, self._winsize, self._winsize + self._blocksize, fill='#555', width=0)
        self._win.create_rectangle(0, self._winsize, self._winsize, self._winsize + self._blocksize * 7/4, fill='#333', width=0)
        for x in range(self._settings.board_size):
            for y in range(self._settings.board_size):
                self._win.create_rectangle(
                    x * self._blocksize + 21, y * self._blocksize + 21,
                    x * self._blocksize + self._blocksize - 3 + 21, y * self._blocksize + self._blocksize - 3 + 21,
                    fill='black',
                    width=0)

    def draw_square(self, loc, color):
        if self._colors[loc] == color:
            return

        self._colors[loc] = color
        x, y = loc
        self._win.create_rectangle(x * self._blocksize + 20, y * self._blocksize + 20,
            x * self._blocksize + self._blocksize - 3 + 20, y * self._blocksize + self._blocksize - 3 + 20,
            fill=color, width=0)

    def update_title(self, turns, max_turns):
        red, green = self._game.get_scores()
        self._win.itemconfig(self._label,
            text='Red: %d | Green: %d | Turn: %d/%d' % (
                red, green, turns, max_turns))

    def callback(self):
        self._game.run_turn()
        self.paint()
        self.update_title(self._game.turns, self._settings.max_turns)

        if self._game.turns < self._settings.max_turns:
            self._win.after(self._settings.turn_interval, self.callback)

    def determine_color(self, loc):

        if loc in self._settings.obstacles:
            return '#222'

        robot = self._game.robot_at_loc(loc)
        
        if robot is None:
            return 'white'
             
        colorhex = 5 + robot.hp / 5
         
        if robot.player_id == 0: # red
            return '#%X00' % colorhex
        else: # green
            return '#0%X0' % colorhex
        
    def paint(self):
        for y in range(self._settings.board_size):
            for x in range(self._settings.board_size):
                loc = (x, y)
                self.draw_square(loc, self.determine_color(loc))
