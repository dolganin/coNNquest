import argparse
import logging
import sys
from utils.game_initializer import initialize_game
from agents.bot_agent import BotAgent
from agents.player_agent import PlayerAgent

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("doom_ai.log", mode='w')
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger("MAIN")

    parser = argparse.ArgumentParser(description="Doom II AI Bot Runner")
    parser.add_argument("--mode", choices=["bot", "player"], default="bot", help="Choose run mode")
    args = parser.parse_args()

    logger.info(f"Старт программы в режиме '{args.mode}'.")

    game = initialize_game(args.mode)

    agent = BotAgent() if args.mode == "bot" else PlayerAgent()

    episodes = 10
    for i in range(episodes):
        logger.info(f"Начало эпизода {i+1}.")
        game.new_episode()
        while not game.is_episode_finished():
            state = game.get_state()
            if state:
                action = agent.get_action(state)
                game.make_action(action)
    game.close()
    logger.info("Игра завершена успешно.")

if __name__ == "__main__":
    main()
