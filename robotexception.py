class RobotException(Exception):
    pass

class UnitGuardCollision(RobotException):
    def __init__(self, other_robot):
        self.other_robot = other_robot

class UnitMoveCollision(RobotException):
    def __init__(self, other_robots):
        self.other_robots = other_robots

class UnitBlockCollision(RobotException):
    def __init__(self, other_robot):
        self.other_robot = other_robot
