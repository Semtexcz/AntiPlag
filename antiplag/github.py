import csv
import os
from functools import cached_property
from pprint import pprint

import requests


class GitHubClassroom:
    def __init__(self, token: str):
        """
        Initialize the GitHubClassroom object.

        :param token: A string representing the authentication token for GitHub API access.
        """
        self._classrooms = []
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_response_json(self, url: str):
        """
        Sends a GET request to the specified URL and returns the JSON response.

        :param url: A string representing the URL to which the GET request is to be sent.
        :return: A dictionary containing the JSON response from the request.
        """
        response = requests.get(url, headers=self.headers)
        return response.json()

    @cached_property
    def classrooms(self):
        """
        Lazily loads and returns a list of classrooms.
        If not already loaded, it fetches the classroom data from the GitHub API.

        :return: A list of classroom data.
        """
        url = "https://api.github.com/classrooms"

        if not self._classrooms:
            classrooms_list = []
            response = self.get_response_json(url)
            if not response:
                return {}
            for classroom in response:
                classrooms_list.append(
                    Classroom(classroom["id"], classroom["name"], classroom["archived"], classroom["url"],
                              classroom.get("organization"), github_client=self))
            self._classrooms = classrooms_list
        return self._classrooms

    def get_classroom(self, classroom_id: int | str) -> list:
        """
        Fetches and returns the details of a classroom by its ID.

        :param classroom_id: An integer or string representing the ID of the classroom.
        :return: A list containing the details of the classroom.
        """
        url = f"https://api.github.com/classrooms/{classroom_id}"
        return self.get_response_json(url)

    def get_accepted_assignments_for_assignment(self, assignment_id: int | str) -> list:
        """
        Fetches a list of accepted assignments for a given assignment ID.

        :param assignment_id: An integer or string representing the ID of the assignment.
        :return: A list containing the accepted assignments.
        """
        url = f"https://api.github.com/assignments/{assignment_id}/accepted_assignments"
        return self.get_response_json(url)

    def get_nick_assigment_repo_dictionary(self, assignment_id: int | str) -> dict[str: str]:
        accepted_assignments = self.get_accepted_assignments_for_assignment(assignment_id)
        nick_repo_dictionary = {}
        for student_assignment in accepted_assignments:
            nick_repo_dictionary[student_assignment["students"][0]["login"]] = student_assignment["repository"][
                "html_url"]
        return nick_repo_dictionary

    def get_nick_name_dict(self, path: str):
        with open(path, "r") as f:
            reader = csv.reader(f)
            nick_name_dict = {}
            for i, row in enumerate(reader):
                if i == 1:
                    continue
                nick_name_dict[row[1]] = row[0]
        return nick_name_dict

    def get_name_url_repo_dict(self, assignment_id: int | str, classroom_roster_path: str) -> dict[
                                                                                              str: str]:
        nick_name_dict = self.get_nick_name_dict(classroom_roster_path)
        nick_assigment_repo_dictionary = self.get_nick_assigment_repo_dictionary(assignment_id)
        name_assignment_repo_dict = {}
        for k, v in nick_assigment_repo_dictionary.items():
            if nick_name_dict.get(k):
                name_assignment_repo_dict[nick_name_dict[k]] = v
            else:
                name_assignment_repo_dict[k] = v
        return name_assignment_repo_dict


class Classroom:
    def __init__(self, id_, name, archived, url, organization=None, github_client=None):
        self.id = id_
        self.name = name
        self.archived = archived
        self.url = url
        self._assignments = None
        if organization:
            self.organization = organization
        else:
            self.organization = {}
        if github_client:
            self.g = github_client

    def get_assignments_for_classroom(self):
        """
        Retrieves a list of assignments for a given classroom.

        :return: A list of assignments for the specified classroom.
        """
        url = f"https://api.github.com/classrooms/{self.id}/assignments"
        response = self.g.get_response_json(url)
        return response


if __name__ == '__main__':
    token = os.environ.get("GITHUB_TOKEN")
    g = GitHubClassroom(token)
    classrooms = g.classrooms
    assignments = classrooms[1].get_assignments_for_classroom()
    print(assignments)

    accepted_assignments = g.get_accepted_assignments_for_assignment(517448)
    # pprint(accepted_assignments)
    pprint(g.get_name_url_repo_dict(517448,
                                    "/media/Data/Drive/Projekty/Pracovní/Github Classroom/AntiPlag/data/188826_roster.csv"))
