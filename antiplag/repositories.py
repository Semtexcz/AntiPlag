import json
import os
import re
import subprocess
import tempfile
from pprint import pprint

import networkx as nx
import plotly.graph_objects as go
from esprima import esprima
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class PlagDetector:
    def __init__(self):
        self.files_dict = {}
        self.repos = {}
        self._similarity_threshold = 0.85

    @property
    def similarity_threshold(self):
        return self._similarity_threshold

    @similarity_threshold.setter
    def similarity_threshold(self, threshold):
        self._similarity_threshold = threshold

    def clone_github_repos(self, user_repos):
        # Slovník pro ukládání cest ke staženým repozitářům
        cloned_repos = {}

        # Vytvoření dočasné složky
        temp_dir = tempfile.mkdtemp()

        for user, repo_url in user_repos.items():
            # Získání názvu repozitáře z URL
            ssh_link = self.get_ssh_link_from_url(repo_url)

            repo_name = repo_url.split('/')[-1]

            # Cesta k repozitáři ve dočasné složce
            repo_path = os.path.join(temp_dir, repo_name)

            # Stažení repozitáře
            subprocess.run(['git', 'clone', ssh_link, repo_path])

            # Přidání cesty do slovníku
            cloned_repos[user] = repo_path

        self.repos = cloned_repos

    def get_ssh_link_from_url(self, url):
        url_array = url.split("/")
        return f"git@github.com:{url_array[-2]}/{url_array[-1]}.git"

    def read_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def remove_comments_and_empty_lines(self, js_code):
        # Odstranění víceřádkových komentářů
        js_code = re.sub(r'/\*.*?\*/', '', js_code, flags=re.DOTALL)

        # Odstranění jednořádkových komentářů a prázdných řádků
        lines = js_code.split('\n')
        cleaned_lines = [line for line in lines if not re.match(r'^\s*(//.*)?$', line)]

        return '\n'.join(cleaned_lines)

    def compare_files(self):
        texts = []
        nicknames = []

        for nick, file_path in self.files_dict.items():
            if os.path.exists(file_path):
                texts.append(self.remove_comments_and_empty_lines(self.read_file(file_path)))
                nicknames.append(nick)
            else:
                print(f"Warning: File not found for {nick} at {file_path}")

        if len(texts) < 2:
            print("Not enough files to compare.")
            return

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)

        cos_similarities = cosine_similarity(tfidf_matrix)
        plagiarism_results = []

        for i in range(len(nicknames)):
            for j in range(i + 1, len(nicknames)):
                if cos_similarities[i, j] > self._similarity_threshold:
                    result = {
                        "pair": (nicknames[i], nicknames[j]),
                        "similarity": cos_similarities[i, j]
                    }
                    plagiarism_results.append(result)
                    # threshold for similarity
                    print(
                        f"Potential plagiarism: {nicknames[i]} and {nicknames[j]} (similarity: {cos_similarities[i, j]})")
        sorted_results = sorted(plagiarism_results, key=lambda x: x['similarity'], reverse=True)
        return sorted_results

    def create_files_dict(self, path):
        files_dict = {}
        for user, repo in self.repos.items():
            full_path = os.path.join(repo, path)
            files_dict[user] = full_path
        self.files_dict = files_dict

    def create_networkx_graph(self, plagiarism_results):
        G = nx.Graph()
        for result in plagiarism_results:
            user1, user2 = result['pair']
            similarity = result['similarity']
            G.add_edge(user1, user2, weight=similarity)
        return G

    def calculate_positions(self, G):
        return nx.spring_layout(G)

    def create_edges_trace(self, G, pos):
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        return edge_trace

    def create_nodes_trace(self, G, pos):
        node_x = []
        node_y = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=10,
                color=list(dict(G.degree()).values()),
                colorbar=dict(
                    thickness=15,
                    title='Počet spojení',
                    xanchor='left',
                    titleside='right'
                ),
                line_width=2))
        node_text = [node for node in G.nodes()]
        node_trace.text = node_text
        return node_trace

    def draw_plotly_graph(self, edge_trace, node_trace):
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            title='Interaktivní graf spolupráce mezi uživateli',
                            titlefont_size=16,
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20, l=5, r=5, t=40),
                            annotations=[dict(
                                text="Pythonová vizualizace s Plotly",
                                showarrow=False,
                                xref="paper", yref="paper",
                                x=0.005, y=-0.002)],
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                        )
        fig.show()

    # Hlavní funkce pro sestavení grafu
    def create_collaboration_graph(self, plagiarism_results):
        G = self.create_networkx_graph(plagiarism_results)
        pos = self.calculate_positions(G)
        edge_trace = self.create_edges_trace(G, pos)
        node_trace = self.create_nodes_trace(G, pos)
        self.draw_plotly_graph(edge_trace, node_trace)


if __name__ == '__main__':
    # Příklad použití
    repo_urls = {'Eliška Semorádová': 'https://github.com/1-IT-Gymnazium/8-loops-Awyyn',
                 'Filip Janoušek': 'https://github.com/1-IT-Gymnazium/8-loops-FilipnotfounD',
                 'Filip Černý': 'https://github.com/1-IT-Gymnazium/8-loops-FilipCer',
                 'Honza-Hoff': 'https://github.com/1-IT-Gymnazium/8-loops-Honza-Hoff',
                 'Jakub Lehar': 'https://github.com/1-IT-Gymnazium/8-loops-notkorasek',
                 'Jakub Oškera': 'https://github.com/1-IT-Gymnazium/8-loops-oskyc',
                 'Janek Hujer': 'https://github.com/1-IT-Gymnazium/8-loops-WestrCZ',
                 'Jáchym Ježek': 'https://github.com/1-IT-Gymnazium/8-loops-JJJezek',
                 'Lukáš Otáhal': 'https://github.com/1-IT-Gymnazium/8-loops-Otahlu',
                 'Mariana Lipková': 'https://github.com/1-IT-Gymnazium/8-loops-Amyk22',
                 'Matyáš Jan Diviš': 'https://github.com/1-IT-Gymnazium/8-loops-mejtxd',
                 'Matěj Fibiger': 'https://github.com/1-IT-Gymnazium/8-loops-Matejop',
                 'Matěj Hladeček': 'https://github.com/1-IT-Gymnazium/8-loops-Chnapak',
                 'Maxime Gabarre': 'https://github.com/1-IT-Gymnazium/8-loops-gameprotoCZECH',
                 'Mykola Ivanko': 'https://github.com/1-IT-Gymnazium/8-loops-Stormmm4128',
                 'Nicol Rozumová': 'https://github.com/1-IT-Gymnazium/8-loops-nikuskaaa',
                 'Sarah Štěpánová': 'https://github.com/1-IT-Gymnazium/8-loops-Sarash-s',
                 'Sebastian Jirkal': 'https://github.com/1-IT-Gymnazium/8-loops-Sejge',
                 'Tobiáš Špringr': 'https://github.com/1-IT-Gymnazium/8-loops-Gravitak',
                 'privacyconsern': 'https://github.com/1-IT-Gymnazium/8-loops-privacyconsern'}
    detector = PlagDetector()

    # detector.clone_github_repos(repo_urls)
    # detector.create_files_dict("tasks.js")
    detector.files_dict = {'Eliška Semorádová': '/tmp/tmp6q5omo99/8-loops-Awyyn/tasks.js',
                           'Filip Janoušek': '/tmp/tmp6q5omo99/8-loops-FilipnotfounD/tasks.js',
                           'Filip Černý': '/tmp/tmp6q5omo99/8-loops-FilipCer/tasks.js',
                           'Honza-Hoff': '/tmp/tmp6q5omo99/8-loops-Honza-Hoff/tasks.js',
                           'Jakub Lehar': '/tmp/tmp6q5omo99/8-loops-notkorasek/tasks.js',
                           'Jakub Oškera': '/tmp/tmp6q5omo99/8-loops-oskyc/tasks.js',
                           'Janek Hujer': '/tmp/tmp6q5omo99/8-loops-WestrCZ/tasks.js',
                           'Jáchym Ježek': '/tmp/tmp6q5omo99/8-loops-JJJezek/tasks.js',
                           'Lukáš Otáhal': '/tmp/tmp6q5omo99/8-loops-Otahlu/tasks.js',
                           'Mariana Lipková': '/tmp/tmp6q5omo99/8-loops-Amyk22/tasks.js',
                           'Matyáš Jan Diviš': '/tmp/tmp6q5omo99/8-loops-mejtxd/tasks.js',
                           'Matěj Fibiger': '/tmp/tmp6q5omo99/8-loops-Matejop/tasks.js',
                           'Matěj Hladeček': '/tmp/tmp6q5omo99/8-loops-Chnapak/tasks.js',
                           'Maxime Gabarre': '/tmp/tmp6q5omo99/8-loops-gameprotoCZECH/tasks.js',
                           'Mykola Ivanko': '/tmp/tmp6q5omo99/8-loops-Stormmm4128/tasks.js',
                           'Nicol Rozumová': '/tmp/tmp6q5omo99/8-loops-nikuskaaa/tasks.js',
                           'Sarah Štěpánová': '/tmp/tmp6q5omo99/8-loops-Sarash-s/tasks.js',
                           'Sebastian Jirkal': '/tmp/tmp6q5omo99/8-loops-Sejge/tasks.js',
                           'Tobiáš Špringr': '/tmp/tmp6q5omo99/8-loops-Gravitak/tasks.js',
                           'privacyconsern': '/tmp/tmp6q5omo99/8-loops-privacyconsern/tasks.js'}
    pprint(detector.files_dict)
    plagiarism_results = detector.compare_files()
    print(json.dumps(plagiarism_results, ensure_ascii=False))
    detector.create_collaboration_graph(plagiarism_results)
