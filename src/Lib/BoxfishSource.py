import os
import sys

from Lib.utils import CommandLine, ChangeDirectory, directory_exists, ensure_directory_exists

def checkout_source(folder, repo, branch=None, commit=None):
    if not directory_exists(folder):
        ensure_directory_exists(folder)
        if CommandLine("git clone \"{}\" \"{}\"".format(repo, folder)).run() != CommandLine.SUCCESS:
            if not CommandLine.chain("git submodule init", "git submodule update", working_directory=folder):
                return False
    else:
        if CommandLine("git pull origin {}".format(branch if branch is not None else "master"), working_directory=folder).run() != CommandLine.SUCCESS:
            print("Failed to pull")
            return False
    if branch is not None:
        if CommandLine("git checkout \"{}\"".format(branch), working_directory=folder).run() == CommandLine.SUCCESS:
            return True
    elif commit is not None:
        if CommandLine("git checkout \"{}\"".format(commit), working_directory=folder).run() == CommandLine.SUCCESS:
            return True
    return True

class BoxfishSource:
    def __init__(self, folder):
        self.folder = folder

    def build_windows(self, msbuild_command: str):
        scripts_directory = os.path.join(self.folder, "Scripts")
        if CommandLine("Win-GenProjects.bat < nul", working_directory=scripts_directory).run() != CommandLine.SUCCESS:
            return None
        if CommandLine("{} -t:Boxfish-Cli -p:Configuration=Dist -p:Platform=x64".format(msbuild_command), working_directory=self.folder).run() != CommandLine.SUCCESS:
            return None
        return os.path.join(self.folder, "bin", "Dist-windows-x86_64", "Boxfish-Cli", "Boxfish-Cli.exe")

    def build_linux(self, jobs=4):
        scripts_directory = os.path.join(self.folder, "Scripts")
        if CommandLine("./Linux-GenProjects.sh < /dev/nul", working_directory=scripts_directory).run() != CommandLine.SUCCESS:
            return None
        if CommandLine("make -j {} Boxfish-Cli config=dist".format(jobs), working_directory=self.folder).run() != CommandLine.SUCCESS:
            return None
        return os.path.join(self.folder, "bin", "Dist-linux-x86_64", "Boxfish-Cli", "Boxfish-Cli.exe")
