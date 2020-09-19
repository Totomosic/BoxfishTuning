import os
import sys
import argparse

from Lib.BoxfishSource import BoxfishSource, checkout_source
from Lib.utils import CommandLine, delete_recursive

SRC_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, default="Boxfish", help="Folder to clone source code into")
    parser.add_argument("--repository", type=str, default="https://github.com/Totomosic/Boxfish.git", help="Boxfish git repository")
    parser.add_argument("--branch", type=str, default=None, help="Git branch to use")
    parser.add_argument("--commit", type=str, default=None, help="Git commit to use")
    parser.add_argument("--opponent", type=str, required=True, help="File path of UCI engine opponent")
    parser.add_argument("--movetime", type=int, default=1000, help="Time for each move in milliseconds")
    parser.add_argument("--results-file", type=str, default="Match.json", help="File to store match results")
    parser.add_argument("--os", type=str, default="windows", help="Os (linux, windows)")

    args = parser.parse_args()

    if not checkout_source(args.folder, args.repository, branch=args.branch, commit=args.commit):
        delete_recursive(args.folder)
        print("Failed to checkout Boxfish")
        sys.exit(1)

    source = BoxfishSource(args.folder)
    if args.os == "windows":
        executable = source.build_windows("C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community\\MSBuild\\Current\\Bin\\MSBuild.exe")
    else:
        executable = source.build_linux()

    if executable is None:
        delete_recursive(args.folder)
        print("Failed to build Boxfish")
        sys.exit(1)

    command = CommandLine("python {} --white \"{}\" --black \"{}\" --movetime {} --results-file \"{}\"".format(os.path.join(SRC_DIRECTORY, "play_match.py"), executable, args.opponent, args.movetime, args.results_file))
    if command.run() != CommandLine.SUCCESS:
        print("Match failed")
        sys.exit(1)

