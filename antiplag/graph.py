import networkx as nx
import plotly.graph_objects as go


class GraphVisualizer:
    def __init__(self, plagiarism_results):
        self.plagiarism_results = plagiarism_results

    def create_networkx_graph(self):
        G = nx.Graph()
        for result in self.plagiarism_results:
            user1, user2 = result['pair']
            similarity = result['similarity']
            G.add_edge(user1, user2, weight=similarity)
        return G

    @staticmethod
    def calculate_positions(G):
        return nx.spring_layout(G, k=0.3, iterations=20)

    @staticmethod
    def create_edges_trace(G, pos):
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        return go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')

    @staticmethod
    def create_nodes_trace(G, pos):
        node_x, node_y, node_text = [], [], []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', text=node_text, textposition='top center',
                                hoverinfo='text', marker=dict(showscale=True, colorscale='YlGnBu', size=10,
                                                              color=list(dict(G.degree()).values()),
                                                              colorbar=dict(thickness=15, title='Node Connections',
                                                                            xanchor='left', titleside='right'),
                                                              line_width=2))
        return node_trace

    def draw_plotly_graph(self):
        G = self.create_networkx_graph()
        pos = self.calculate_positions(G)
        edge_trace = self.create_edges_trace(G, pos)
        node_trace = self.create_nodes_trace(G, pos)
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(title='Network Graph of Plagiarism Results', titlefont_size=16,
                                         showlegend=False, hovermode='closest', margin=dict(b=20, l=5, r=5, t=40),
                                         annotations=[dict(text="Plagiarism Network Visualization", showarrow=False,
                                                           xref="paper", yref="paper", x=0.005, y=-0.002)],
                                         xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                         yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        fig.show()
