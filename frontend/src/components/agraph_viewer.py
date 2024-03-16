import streamlit as st 
from src.settings import logger, ConfigLoader
from streamlit_agraph import agraph, Node, Edge, Config, ConfigBuilder
import requests

class AgraphViewer:
    def __init__(self, parent_container=None, data_manager=None):
        self._parent_container = parent_container
        self._data_manager = data_manager
        self._config = None
        self._setup_toolbox()
        self._setup_viewer()

    @property
    def config(self):
        if not self._config:
            self._config = self._get_config()
        return self._config

    def _get_config(self):
        user_config =  ConfigLoader().load_config("agraph_config")
        return Config(
            directed=user_config.get("directed", True),
            physics=user_config.get("physics", True),
            hierarchical=user_config.get("hierarchical", False),
            width=user_config.get("width", "100%"),
            groups=user_config.get("groups", {})
        )
        
    def _handle_extension_selection(self):
        seleced_extension = st.session_state['extension_selection']

    def _setup_toolbox(self):
        toolbox = self._parent_container.expander(":traffic_light: Argumentation Graph Toolbox")
        with toolbox:
            self.selected_extension = st.radio(
                "Extensions", 
                options=["grounded", "complete", "preferred", "stable", "ideal"], 
                index=0, 
                key="extension_selection",
                on_change=self._handle_extension_selection,
                disabled=True
            )
    def _setup_viewer(self):
        self._viewer = self._parent_container.container(height=700)

    def _apply_filters_to_nodes(self, selected_nodes, current_node):
        node_id = current_node.get('node_id')
        node_role = current_node.get('role')
        
        # Define a mapping of roles to return values
        status_mapping = {
            ('defense', True): "accepted_defense",
            ('defense', False): "defeated_defense",
            ('prosecution', True): "accepted_prosecution",
            ('prosecution', False): "defeated_prosecution",
        }
    
        # Use the node's role and selection status to determine the return value
        return status_mapping.get((node_role, node_id in selected_nodes))
        
    def _load_graph_data(self, filter='none'):
        graph_data = self._data_manager.get_arguments()
        accepted_nodes = []
        if filter != 'none':
            accepted_nodes = graph_data.get('extensions', {}).get(f'{filter}', [])
                         
        nodes = [
            Node(
                id=node.get('node_id',''), 
                label=node.get('label', ''), 
                label_expand = node.get('label_expanded', ''),
                title=node.get('text',''), 
                group=self._apply_filters_to_nodes(accepted_nodes, node)
                ) 
            for node in graph_data.get('nodes', [])
        ]
        
        edges = [
            Edge(
                source=edge.get('from',''), 
                target=edge.get('to',''), 
                label=edge.get('edge_type',''),
                width=3 if edge.get('edge_type','') == 'attack' else 1,
                color='red' if edge.get('edge_type','') == 'attack' else 'green'
                )
            for edge in graph_data.get('edges', [])
        ]
        return nodes, edges

    def render(self):
        nodes, edges = self._load_graph_data(filter=self.selected_extension)
        with self._viewer:
            return agraph(nodes=nodes, edges=edges, config=self.config)


        
    # def _load_graph_data(self):
    #     graph_data = self._data_manager.get_arguments()
    #     # selected_nodes = []
        
    #     # if selected_extension is not 'none':
    #     #     selected_nodes = graph_data.get('extensions', {}).get(f'{selected_extension}_extension', [])

    #     nodes = [
    #         Node(
    #             id=node['node_id'], 
    #             label=node.get('label', ''), 
    #             label_expanded=node.get('label_expanded', ''),
    #             title=node.get('title',''), 
    #             group=node.get('group','')
    #             )
    #         for node in graph_data.get('nodes', [])
    #     ]

    #     edges = [
    #         Edge(
    #             source=edge.get('from',''), 
    #             target=edge.get('to',''), 
    #             label=edge.get('edge_type','')
    #             )
    #         for edge in graph_data.get('edges', [])
    #     ]
    #     return nodes, edges
        
    # def render(self): 
    #     nodes, edges = self._load_graph_data()
    #     with self._viewer:
    #         return agraph(nodes=nodes, edges=edges, config=self.config)

    

# def load_graph_data(data):
#     nodes = [
#         Node(
#             id=node['id'], 
#             label=node.get('label', ''), 
#             title=node.get('title',''), 
#             group=node.get('group','')
#             ) 
#         for node in data.get('nodes', [])]
#     edges = [
#         Edge(
#             source=edge['source'], 
#             target=edge['target'], 
#             label=edge.get('label', '')
#             ) 
#         for edge in data.get('edges', [])]

#     return nodes, edges

# def apply_filters(nodes, edges, node_filter=None):
#     if node_filter:
#         filtered_nodes = [node for node in nodes if node_filter.lower() in node.label.lower()]
#         filtered_edges = [edge for edge in edges if edge.source in [node.id for node in filtered_nodes] and edge.target in [node.id for node in filtered_nodes]]
#     else:
#         filtered_nodes = nodes
#         filtered_edges = edges
#     return filtered_nodes, filtered_edges

