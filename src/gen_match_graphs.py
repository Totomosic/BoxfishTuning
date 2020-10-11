import os
import argparse
import matplotlib.pyplot as plt
import json
import numpy as np

def rescale_eval(score):
    if abs(score) > 90000:
        score = int(5000 * (score / abs(score)))
    return score

def rescale_depth(depth):
    if depth >= 99:
        depth = None
    return depth

def create_graph_data(move_list, field, scaling=None):
    if scaling is None:
        scaling = lambda x: x
    move_count = len(move_list)
    x = [x + 1 for x in range(move_count)]
    first_ys = [scaling(move_list[i][field]) for i in range(0, move_count, 2)]
    second_ys = [scaling(move_list[i][field]) for i in range(1, move_count, 2)]
    return (x[0 : len(first_ys)], first_ys), (x[0 : len(second_ys)], second_ys)

def save_graph(filename, white_data, black_data, color):
    plt.clf()
    plt.plot(*white_data, color, *black_data, "{}--".format(color))
    plt.savefig(filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--match-result", type=str, required=True, help="Path to match result file")

    args = parser.parse_args()

    with open(args.match_result, "r") as f:
        data = json.load(f)

    first_game = data

    first_eval = create_graph_data(first_game["moves"], "eval", rescale_eval)

    first_depth = create_graph_data(first_game["moves"], "depth", rescale_depth)

    first_nodes = create_graph_data(first_game["moves"], "nodes")

    first_nps = create_graph_data(first_game["moves"], "nps")

    save_graph("WhiteEvals.png", first_eval[0], first_eval[1], "r")
    save_graph("WhiteDepth.png", first_depth[0], first_depth[1], "r")
    save_graph("WhiteNodes.png", first_nodes[0], first_nodes[1], "r")
    save_graph("WhiteNps.png", first_nps[0], first_nps[1], "r")
