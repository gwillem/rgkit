import ast
import inspect
import random
import sys
import traceback
import imp
###
from robotexception import *
from settings import settings
import rg

def init_settings(map_file):
    global settings
    map_data = ast.literal_eval(open(map_file).read())
    settings.spawn_coords = map_data['spawn']
    settings.obstacles = map_data['obstacle']
    rg.set_settings(settings)

class DefaultRobot:
    def act(self, game):
        return ['guard']

class Player:
    def __init__(self, code=None, robot=None):
        if code is not None:
            self._robot = None
            self._mod = imp.new_module('usercode%d' % id(self))
            exec code in self._mod.__dict__
        elif robot is not None:
            self._robot = robot
        else:
            raise Exception('you need to provide code or a module')

    def get_usercode_obj(self, class_name, default):
        if hasattr(self._mod, class_name):
            if inspect.isclass(getattr(self._mod, class_name)):
                return getattr(self._mod, class_name)()
        return default()

    def get_robot(self):
        if self._robot is not None:
            return self._robot
        self._robot = self.get_usercode_obj('Robot', DefaultRobot)
        return self._robot

class InternalRobot:
    def __init__(self, location, hp, player_id, field):
        self.location = location
        self.hp = hp
        self.player_id = player_id
        self.field = field
        
    @staticmethod
    def parse_command(action):
        return (action[0], action[1:])

    def issue_command(self, action, actions):
        cmd, params = InternalRobot.parse_command(action)
        if cmd == 'move' or cmd == 'attack':
            getattr(self, 'call_' + cmd)(params[0], actions)
        if cmd == 'suicide':
            self.call_suicide(actions)

    def get_robots_around(self, loc):
        locs_around = rg.locs_around(loc, filter_out=['obstacle', 'invalid'])
        locs_around.append(loc)

        robots = [self.field[x] for x in locs_around]
        return [x for x in robots if x is not None]

    def movable_loc(self, loc):
        good_around = rg.locs_around(self.location,
            filter_out=['invalid', 'obstacle'])
        return loc in good_around

    def can_act(self, loc, action_table, no_raise=False, move_stack=None):
        global settings

        if move_stack is not None and self in move_stack:
            return self == move_stack[0]
        if not self.movable_loc(loc):
            return False

        moving = []

        nearby_robots = self.get_robots_around(loc)
        for robot in nearby_robots:
            if robot == self:
                continue

            cmd, params = InternalRobot.parse_command(action_table[robot])

            if cmd == 'suicide' and robot.location == loc:
                continue
            if cmd == 'guard' and robot.location == loc:
                if no_raise:
                    return False
                raise UnitGuardCollision(robot)
            if cmd == 'attack' and robot.location == loc:
                if no_raise:
                    return False
                raise UnitBlockCollision(robot)
            if cmd == 'move':
                if params[0] == loc:
                    moving.append(robot)
                elif robot.location == loc:
                    if move_stack is None:
                        move_stack = [self]
                    move_stack.append(robot)
                    if not robot.can_act(params[0], action_table, True, move_stack):
                        if no_raise:
                            return False
                        raise UnitBlockCollision(robot)
                            
        if len(moving) > 0:
            if no_raise:
                return False
            raise UnitMoveCollision(moving)
        return True

    def call_move(self, loc, action_table):
        global settings
        try:
            if self.can_act(loc, action_table):
                self.location = loc
        except UnitGuardCollision as e:
            if e.other_robot.player_id != self.player_id:
                self.hp -= settings.collision_damage
        except UnitMoveCollision as e:
            for robot in e.other_robots:
                if robot.player_id != self.player_id:
                    robot.hp -= settings.collision_damage
        except UnitBlockCollision as e:
            if e.other_robot.player_id != self.player_id:
                self.hp -= settings.collision_damage
                e.other_robot.hp -= settings.collision_damage
        except RobotException:
            pass

    def call_attack(self, loc, action_table, damage=None):
        if damage is None:
            damage = random.randint(*settings.attack_range)
        try:
            self.can_act(loc, action_table)
        except UnitGuardCollision as e:
            if e.other_robot.player_id != self.player_id:
                e.other_robot.hp -= int(damage / 2)
        except UnitMoveCollision as e:
            for robot in e.other_robots:
                if robot.player_id != self.player_id:
                    robot.hp -= damage
        except UnitBlockCollision as e:
            if e.other_robot.player_id != self.player_id:
               e.other_robot.hp -= int(damage)
        except RobotException:
            pass

    def call_suicide(self, action_table):
        self.hp = 0
        self.call_attack(self.location, action_table, damage=settings.suicide_damage)
        for loc in rg.locs_around(self.location):
            self.call_attack(loc, action_table, damage=settings.suicide_damage)

    @staticmethod
    def is_valid_action(action):
        global settings

        cmd, params = InternalRobot.parse_command(action)
        return cmd in settings.valid_commands

# just to make things easier
class Field:
    def __init__(self, size):
        self.field = [[None for x in range(size)] for y in range(size)]
    def __getitem__(self, point):
        return self.field[point[1]][point[0]]
    def __setitem__(self, point, v):
        self.field[point[1]][point[0]] = v

class Game:
    def __init__(self, player1, player2, record_turns=False):
        self._players = (player1, player2)
        self.turns = 0
        self._robots = []
        self._field = Field(settings.board_size)
        self._record = record_turns
        if self._record:
            self.history = [[] for i in range(2)]

    def build_game_info(self):
        global settings

        return {
            'robots': dict((
                y.location,
                dict((x, getattr(y, x)) for x in settings.exposed_properties)
            ) for y in self._robots),
            'turn': self.turns,
        }

    def notify_new_turn(self):
        for player_id in range(2):
            user_robot = self._players[player_id].get_robot()
            if hasattr(user_robot, 'on_new_turn'):
                if inspect.ismethod(user_robot.on_new_turn):
                    user_robot.on_new_turn()

    def make_robots_act(self):
        global settings

        game_info = self.build_game_info()
        actions = {}

        for robot in self._robots:
            user_robot = self._players[robot.player_id].get_robot()
            for prop in settings.exposed_properties:
                setattr(user_robot, prop, getattr(robot, prop))

            try:
                next_action = user_robot.act(game_info)
                if not InternalRobot.is_valid_action(next_action):
                    raise Exception('%s is not a valid action' % str(next_action))
            except Exception:
                print "The robot at (%s, %s) raised an exception:" % robot.location
                print '-' * 60
                traceback.print_exc(file=sys.stdout)
                print '-' * 60
                next_action = ['guard']
            actions[robot] = next_action

        for robot, action in actions.iteritems():
            old_loc = robot.location
            robot.issue_command(action, actions)
            if robot.location != old_loc:
                self._field[old_loc] = None
                self._field[robot.location] = robot

    def robot_at_loc(self, loc):
        robot = self._field[loc]
        return robot

    def spawn_robot(self, player_id, loc):
        if self.robot_at_loc(loc) is not None:
            return False

        robot = InternalRobot(loc, settings.robot_hp, player_id, self._field)
        self._robots.append(robot)
        self._field[loc] = robot

    def spawn_robot_batch(self):
        global settings

        locs = random.sample(settings.spawn_coords, settings.spawn_per_player * 2)
        for player_id in range(2):
            for i in range(settings.spawn_per_player):
                self.spawn_robot(player_id, locs.pop())

    def clear_spawn_points(self):
        for loc in settings.spawn_coords:
            if self._field[loc] is not None:
                self._robots.remove(self._field[loc])
                self._field[loc] = None

    def remove_dead(self):
        to_remove = [x for x in self._robots if x.hp <= 0]
        for robot in to_remove:
            self._robots.remove(robot)
            if self._field[robot.location] == robot:
                self._field[robot.location] = None

    def make_history(self):
        # indeed, let's hope this game does
        global settings

        robots = [[] for i in range(2)]
        for robot in self._robots:
            robot_info = []
            for prop in settings.exposed_properties:
                if prop != 'player_id':
                    robot_info.append(getattr(robot, prop))
            robots[robot.player_id].append(robot_info)
        return robots

    def run_turn(self):
        global settings

        self.notify_new_turn()
        self.make_robots_act()
        self.remove_dead()

        if self.turns % settings.spawn_every == 0:
            self.clear_spawn_points()
            self.spawn_robot_batch()

        if self._record:
            round_history = self.make_history()
            for i in (0, 1):
                self.history[i].append(round_history[i])

        self.turns += 1

    def get_scores(self):
        scores = [0, 0]
        for robot in self._robots:
            scores[robot.player_id] += 1
        return scores
