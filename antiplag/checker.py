import os
from abc import ABC, abstractmethod

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from antiplag.files import CodeFileManager


class PlagiarismCheckerFactory:
    def create_checker(self, checker_type, files_dict, similarity_threshold=0.85):
        if checker_type == "cosine_similarity":
            return CosineSimilarityChecker(files_dict, similarity_threshold)
        # Zde můžete přidat další podmínky pro vytváření různých typů checkerů
        else:
            raise ValueError(f"Checker type '{checker_type}' is not supported.")


class PlagiarismChecker(ABC):
    @abstractmethod
    def compare_files(self):
        pass


class CosineSimilarityChecker(PlagiarismChecker):
    def __init__(self, files_dict, similarity_threshold=0.85):
        self.files_dict = files_dict
        self.similarity_threshold = similarity_threshold
        self._results = []

    @property
    def results(self):
        if not self._results:
            self.compare_files()
        return self._results

    def compare_files(self):
        texts, nicknames = [], []
        for nick, file_path in self.files_dict.items():
            if os.path.exists(file_path):
                file_manager = CodeFileManager({})
                texts.append(file_manager.remove_comments_and_empty_lines(file_manager.read_file(file_path)))
                nicknames.append(nick)
            else:
                print(f"Warning: File not found for {nick} at {file_path}")
        if len(texts) < 2:
            print("Not enough files to compare.")
            return
        plagiarism_results = self.compare_texts(nicknames, texts)
        self._results = sorted(plagiarism_results, key=lambda x: x['similarity'], reverse=True)
        return self._results

    def compare_texts(self, nicknames, texts):
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        cos_similarities = cosine_similarity(tfidf_matrix)
        plagiarism_results = []
        for i in range(len(nicknames)):
            for j in range(i + 1, len(nicknames)):
                if cos_similarities[i, j] > self.similarity_threshold:
                    result = {"pair": (nicknames[i], nicknames[j]), "similarity": cos_similarities[i, j]}
                    plagiarism_results.append(result)
        return plagiarism_results

    def get_result_for_nickname(self, nickname):
        return [result for result in self.results if nickname in result['pair']]


class SequenceMatcherSimilarityChecker(PlagiarismChecker):
    def __init__(self, files_dict, similarity_threshold=0.85):
        self.files_dict = files_dict
        self.similarity_threshold = similarity_threshold

    def compare_files(self):
        pass

        # TODO: dodělat, aby vracelo seřazený seznam podobností
        # with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        #     file1_lines = file1.readlines()
        #     file2_lines = file2.readlines()
        #
        #     similarity = difflib.SequenceMatcher(None, file1_lines, file2_lines).ratio()
        #     return similarity