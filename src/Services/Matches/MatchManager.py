import concurrent.futures

from Services.Matches.UCIEngine import UCIEngine, MoveInfo

class MatchManager:
    def __init__(self, white_executable: str, black_executable: str):
        self.white = white_executable
        self.black = black_executable

    def play_match(self, time_to_move, log=True):
        with UCIEngine(self.white, log=log) as first_white:
            with UCIEngine(self.black, log=log) as first_black:
                first_result = self._play_game(first_white, first_black, time_to_move)
        with UCIEngine(self.black, log=log) as second_white:
            with UCIEngine(self.white, log=log) as second_black:
                second_result = self._play_game(second_white, second_black, time_to_move)
        return first_result, second_result

    def _play_game(self, white_exe, black_exe, time_to_move):
        move_list = []
        move_infos = []
        evaluations = []
        zero_count = 0

        white_exe.init()
        black_exe.init()

        current_player = white_exe
        score = 0
        description = None

        while True:
            move_info = current_player.get_best_move(time_to_move)
            if move_info is None:
                score = 1 if current_player is black_exe else -1
                description = "Took too long to play move."
            if move_info.move == "(none)":
                # TODO: Check for stalemate
                score = 1 if current_player is black_exe else -1
                description = "Checkmate"
                break
            move_list.append(move_info.move)
            move_infos.append(move_info)

            if len(move_list) > 400:
                score = 0
                description = "Game took too long."
                break
            if move_info.evaluation == 0:
                zero_count += 1
                if zero_count > 10:
                    score = 0
                    description = "Repetition"
                    break
            else:
                zero_count = 0

            white_exe.set_position(move_list)
            black_exe.set_position(move_list)

            current_player = white_exe if current_player is black_exe else black_exe

        return { "movetime": time_to_move, "white": white_exe.executable, "black": black_exe.executable, "result": score, "description": description, "moves": list(map(lambda mv: mv.to_dict(), move_infos)) }
