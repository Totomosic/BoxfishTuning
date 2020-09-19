import concurrent.futures

from Lib.UCIEngine import UCIEngine

class MatchManager:
    def __init__(self, white_executable: str, black_executable: str):
        self.white = white_executable
        self.black = black_executable

    def play_match(self, time_to_move, log=True):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            with UCIEngine(self.white, log=log) as first_white:
                with UCIEngine(self.black, log=log) as first_black:
                    with UCIEngine(self.black, log=log) as second_white:
                        with UCIEngine(self.white, log=log) as second_black:
                            first_result_future = executor.submit(self._play_game, first_white, first_black, time_to_move)
                            second_result_future = executor.submit(self._play_game, second_white, second_black, time_to_move)
                            return first_result_future.result(), second_result_future.result()
        return None, None

    def _play_game(self, white_exe, black_exe, time_to_move):
        move_list = []
        evaluations = []
        zero_count = 0

        white_exe.init()
        black_exe.init()

        current_player = white_exe
        winner = None
        description = None

        while True:
            move, evaluation = current_player.get_best_move(time_to_move)
            if move is None:
                winner = "TEAM_WHITE" if current_player is black_exe else "TEAM_BLACK"
                description = "Took too long to play move."
            if move == "(none)":
                # TODO: Check for stalemate
                winner = "TEAM_WHITE" if current_player is black_exe else "TEAM_BLACK"
                description = "Checkmate"
                break
            move_list.append(move)
            evaluations.append(evaluation)

            if len(move_list) > 300:
                winner = "DRAW"
                description = "Game took too long."
                break
            if evaluation == 0:
                zero_count += 1
                if zero_count > 10:
                    winner = "DRAW"
                    description = "Repetition"
                    break
            else:
                zero_count = 0

            white_exe.set_position(move_list)
            black_exe.set_position(move_list)

            current_player = white_exe if current_player is black_exe else black_exe

        return { "RESULT": winner, "DESCRIPTION": description, "MOVES": move_list, "EVALUATIONS": evaluations }
