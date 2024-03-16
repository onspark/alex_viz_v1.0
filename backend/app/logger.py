import logging
from datetime import datetime

# Create a custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set the minimum logging level

# Create handlers: one for the file and one for the console
file_handler = logging.FileHandler(f'app/logs/test_{datetime.now()}.log', mode='w',delay=True)
stream_handler = logging.StreamHandler()

# Create a formatter and set it for both handlers
formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)