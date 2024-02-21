import os
import subprocess
import tempfile


class RepoManager:
    def __init__(self):
        self.repos = {}

    def clone_github_repos(self, user_repos):
        cloned_repos = {}
        temp_dir = tempfile.mkdtemp()
        for user, repo_url in user_repos.items():
            ssh_link = self.get_ssh_link_from_url(repo_url)
            repo_name = repo_url.split('/')[-1]
            repo_path = os.path.join(temp_dir, repo_name)
            subprocess.run(['git', 'clone', ssh_link, repo_path])
            cloned_repos[user] = repo_path
        self.repos = cloned_repos
        return self.repos

    @staticmethod
    def get_ssh_link_from_url(url):
        url_array = url.split("/")
        return f"git@github.com:{url_array[-2]}/{url_array[-1]}.git"
