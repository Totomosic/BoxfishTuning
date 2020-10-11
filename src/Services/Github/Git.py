import github

class GithubServer:
    def __init__(self):
        self.github = github.Github()
        repo = self.github.get_repo("Totomosic/Boxfish")
        print(dir(repo))
        print([x for x in repo.get_events()])

    def poll(self):
        return False

    def checkout_latest(self, path):
        pass
