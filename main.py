import argparse
from utils.game_initializer import initialize_game
from agents.bot_agent import BotAgent
from agents.player_agent import PlayerAgent

def main():
    parser = argparse.ArgumentParser(description="Doom II AI Bot Runner")
    parser.add_argument("--mode", choices=["bot", "player"], default="bot", help="Choose run mode")
    args = parser.parse_args()

    game = initialize_game(args.mode)

    agent = BotAgent() if args.mode == "bot" else PlayerAgent()

    episodes = 10
    for i in range(episodes):
        print(f"Starting episode {i+1}")
        game.new_episode()
        while not game.is_episode_finished():
            state = game.get_state()
            if state:
                action = agent.get_action(state)
                game.make_action(action)
    game.close()

if __name__ == "__main__":
    main()
