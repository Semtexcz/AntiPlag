import os
import re


class CodeFileManager:
    def __init__(self, repos):
        self.files_dict = {}
        self.repos = repos

    def create_files_dict(self, path):
        for user, repo in self.repos.items():
            full_path = os.path.join(repo, path)
            self.files_dict[user] = full_path
        return self.files_dict

    @staticmethod
    def read_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    @staticmethod
    def remove_comments_and_empty_lines(js_code):
        js_code = re.sub(r'/\*.*?\*/', '', js_code, flags=re.DOTALL)
        lines = js_code.split('\n')
        cleaned_lines = [line for line in lines if not re.match(r'^\s*(//.*)?$', line)]
        return '\n'.join(cleaned_lines)
