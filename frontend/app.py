import streamlit as st

from src.components import DataManager, AppLayout
from src.settings import logger

import requests

# TODO: Add calls to API endpoints



def main():
    # logger.info("Hello, World!")

    # Initialize data management first
    data_manager = DataManager()
    # Perform any necessary data loading or initialization

    # Then initialize the UI layout
    layout = AppLayout("ALEX - Argumentation system for Legal Explanations", data_manager=data_manager)


if __name__ == "__main__":
    main()
    