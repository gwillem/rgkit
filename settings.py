settings = {
    # game settings
    'spawn_every': 10,
    'spawn_per_player': 5,
    'board_size': 19,
    'robot_hp': 50,
    'attack_range': (15, 20),
    'collision_damage': 5,
    'suicide_damage': 10,
    'max_turns': 100,
    
    # rendering
    'turn_interval': 100,
    
    # rating systems
    'rating_range': 150,
    'default_rating': 1200,

    # user-scripting
    'max_usercode_time': 100,
    'exposed_properties': ('location', 'hp', 'player_id'),
    'valid_commands': ('move', 'attack', 'guard', 'suicide'),
}

# just change stuff above this line

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
settings = AttrDict(settings)
