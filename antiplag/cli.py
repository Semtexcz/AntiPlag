import json
import os
from pathlib import Path

import click

from antiplag.checker import PlagiarismCheckerFactory
from antiplag.files import CodeFileManager
from antiplag.github import GitHubClassroom
from antiplag.repositories import RepoManager


@click.group()
def antiplag():
    """Antiplag CLI tool for checking plagiarism."""
    pass


@antiplag.command()
@click.argument('id')
@click.argument('file')
@click.argument('nickname')
@click.option('-t', '--token', help='Github token for authentication.')
@click.option('-r', '--roster', default=None,
              help='Path to classroom roster file. Roster file should be in CSV format.'
                   ' Format of CSV file should be: "github_username,full_name"')
def check(id, file, nickname, token, roster):
    """Check for plagiarism by GitHub Assignment ID."""
    click.echo(f"Checking for plagiarism with ID: {id}")

    g = GitHubClassroom(token)
    if roster:
        roster_path = Path(roster).resolve()
        if not roster_path.exists():
            raise click.ClickException(f"The roster file '{roster_path}' does not exist.")
        click.echo(f"Using roster file at: {roster_path}")
        name_url_repo_dict = g.get_name_url_repo_dict(id, str(roster_path))  # Předání cesty jako řetězce
    else:
        name_url_repo_dict = g.get_nick_assigment_repo_dictionary(id)

    repo_manager = RepoManager()
    repos = repo_manager.clone_github_repos(name_url_repo_dict)

    code_file_manager = CodeFileManager(repos)
    files_dict = code_file_manager.create_files_dict(file)

    checker = PlagiarismCheckerFactory().create_checker("cosine_similarity", files_dict)
    checker_results = checker.get_result_for_nickname(nickname)

    similarities = [result['similarity'] for result in checker_results]

    click.echo(json.dumps(checker_results, indent=4))
    click.echo(max(similarities))


if __name__ == '__main__':
    token = os.environ.get("GITHUB_TOKEN")
    antiplag("517448", "tasks.js", token, "data/188826_roster.csv")
