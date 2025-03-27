from __future__ import annotations
from pydantic_graph import BaseNode, Graph, End, GraphRunContext
from dataclasses import dataclass
from typing import Dict, Any, List

from models.schemas import State
from utils.state_manager import StateManager
from agents.info_extractor import extract_info, save_extraction_results

@dataclass
class YTAnalysisState:
    state: State
    youtube_data: Dict[str, Any]

@dataclass
class ExtractInfoNode(BaseNode[YTAnalysisState, None, Dict[str, Any]]):
    async def run(self, ctx: GraphRunContext[YTAnalysisState]) -> End[Dict[str, Any]]:
        # Get data from state
        state = ctx.state.state
        video_id = state.video_id
        transcript = ctx.state.youtube_data.get("transcript", [])
        video_metadata = {
            'video': ctx.state.youtube_data.get("video_info", {}).get("video", {}),
            'channel': ctx.state.youtube_data.get("video_info", {}).get("channel", {})
        }
        
        # Run extraction
        results = await extract_info(transcript, video_metadata)
        
        # Save to output directory
        output_path = await save_extraction_results(video_id, results)
        
        # Update state
        state.interim_results["software"] = results.get("software", [])
        state.interim_results["tags"] = results.get("tags", [])
        state.completion_status.info_extraction = "complete"
        
        # Save state
        state_manager = StateManager()
        state_manager.save_state(state)
        
        return End(results)

def create_workflow():
    """Create the workflow graph with the extraction node"""
    # Ensure we're creating a graph with ExtractInfoNode properly included
    graph = Graph(nodes=[ExtractInfoNode])
    print(f"Created workflow graph with nodes: {graph.nodes}")
    return graph