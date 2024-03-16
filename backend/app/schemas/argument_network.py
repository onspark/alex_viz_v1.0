from pydantic import BaseModel
from typing import Optional, List, Dict


# class ArgNetwork(BaseModel):
#     nodes: List[Dict]
#     edges: List[Dict]
#     extension: Dict

class UserInput(BaseModel):
    crime_fact: str
    selected_extension: str
    selected_role: str
    arguments: Dict
    target_node_id: str
    target_focused: bool
    generation_rounds: int 
    action_option: int
 