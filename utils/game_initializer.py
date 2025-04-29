from vizdoom import DoomGame

def initialize_game(mode):
    game = DoomGame()
    
    if mode == "bot":
        game.load_config("configs/bot.cfg")
        game.add_game_args("-host 1 -deathmatch +sv_spawnfarthest 1")
    else:
        game.load_config("configs/player.cfg")
    
    game.set_window_visible(True)
    game.set_sound_enabled(True)
    game.init()
    
    return game
