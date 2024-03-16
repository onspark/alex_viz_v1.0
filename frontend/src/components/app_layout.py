import streamlit as st
from .document_viewer import DocumentViewer
from .argument_manager import ArgumentManager
from .agraph_viewer import AgraphViewer
from .formal_verifier import FormalVerifier

# TODO: Add wrappers and clean UI

class AppLayout:
    def __init__(self, title='', data_manager=None):
        self.data_manager = data_manager
        st.set_page_config(layout="wide")
        st.title(title)
        self.setup_layouts()

    def setup_page(self):
        st.set_page_config(layout="wide")
        st.title(self.title)

    def setup_layouts(self):
        col1, col2 = st.columns([1, 2])
        df_wrapper = col1.container()
        arg_wrapper = col1.container()
        agraph_wrapper = col2.container()
        fv_wrapper = col2.container()
        
        self.document_reader = DocumentViewer(df_wrapper)
        self.argument_manager = ArgumentManager(arg_wrapper, self.data_manager)
        self.argument_manager.render()
        self.agraph_viewer = AgraphViewer(agraph_wrapper, self.data_manager)
        clicked_id = self.agraph_viewer.render() #returns the clicked node id
        self.formal_verifier = FormalVerifier(fv_wrapper, clicked_id, self.data_manager) 

        

'''
import streamlit as st

class DocumentReader:
    def __init__(self, col):
        self.col = col
        self.setup()

    def setup(self):
        reader = self.col.expander("📑 Case Description")
        with reader:
            # Assuming 'document_text' is already in session_state
            self.text_area = st.text_area("Case Description", value=st.session_state.get('document_text', 'Insert text here...'), height=300, label_visibility='collapsed')

class AgraphViewer:
    def __init__(self, col):
        self.col = col
        self.setup()

    def setup(self):
        toolbox = self.col.expander("Argumentation Graph Toolbox")
        with toolbox:
            # Example of setting up UI components specific to the Agraph Viewer
            self.selected_extension = st.radio("Extensions", options=["complete", "admissible", "grounded", "preferred", "ideal"], index=0, key="extension_selection")

        viewer = self.col.container(height=700)
        with viewer:
            self.viewer = st.empty()  # Placeholder for graph visualization

class AppLayout:
    def __init__(self, title):
        self.title = title
        st.set_page_config(layout="wide")
        st.title(self.title)
        self.create_layouts()

    def create_layouts(self):
        col1, col2 = st.columns([1, 2])
        self.document_reader = DocumentReader(col1)
        self.argument_manager = None  # Placeholder for an ArgumentManager class
        self.agraph_viewer = AgraphViewer(col2)
        self.formal_verifier = None  # Placeholder for a FormalVerifier class

# Example of how you might use AppLayout in your main.py
if __name__ == "__main__":
    app_layout = AppLayout("My Streamlit App")


'''
    
            