import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from models.schemas import State

class StateManager:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def get_state_path(self, channel_id: str, video_id: str) -> str:
        return os.path.join(self.output_dir, f"{channel_id}_{video_id}_state.json")
    
    def load_state(self, channel_id: str, video_id: str) -> Optional[State]:
        """Load state from disk if it exists"""
        state_path = self.get_state_path(channel_id, video_id)
        
        if os.path.exists(state_path):
            try:
                with open(state_path, 'r') as f:
                    data = json.load(f)
                return State.model_validate(data)
            except Exception as e:
                print(f"Error loading state: {e}")
                return None
        
        return None
    
    def save_state(self, state: State) -> None:
        """Save state to disk"""
        state_path = self.get_state_path(state.channel_id, state.video_id)
        
        # Update timestamp
        state.timestamp = datetime.now().isoformat()
        
        with open(state_path, 'w') as f:
            f.write(state.model_dump_json(indent=2))
    
    def initialize_state(self, channel_id: str, video_id: str) -> State:
        """Create a new state or load existing one"""
        existing_state = self.load_state(channel_id, video_id)
        if existing_state:
            return existing_state
        
        return State(
            channel_id=channel_id,
            video_id=video_id,
            interim_results={
                "processes": [],
                "metadata": {},
                "software": [],
                "tags": []
            }
        )