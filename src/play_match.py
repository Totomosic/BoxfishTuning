import os
import json
import argparse

from Lib.MatchManager import MatchManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--white", type=str, required=True, help="Path to white player executable")
    parser.add_argument("--black", type=str, required=True, help="Path to black player executable")
    parser.add_argument("--movetime", type=int, default=1000, help="Time for each move in milliseconds")
    parser.add_argument("--results-file", type=str, default="Match.json", help="File to store match results")

    args = parser.parse_args()

    manager = MatchManager(args.white, args.black)
    first_result, second_result = manager.play_match(args.movetime)

    with open(args.results_file, "w") as f:
        json.dump([first_result, second_result], f)