"""
YouTube Video Analysis Tool

This script extracts and analyzes data from YouTube videos, including transcript 
and metadata information.

Usage:
python main.py URL [options]

Arguments:
URL                 YouTube video URL

Options:
--save, -s          Save output to file instead of just printing to console
--output, -o DIR    Specify output directory (default: 'output')
--workflow, -w      Run the full analysis workflow
--debug, -d         Enable debug output

Examples:
python main.py https://www.youtube.com/watch?v=OFk8HvCr_pY
python main.py https://www.youtube.com/watch?v=OFk8HvCr_pY --save
python main.py https://www.youtube.com/watch?v=OFk8HvCr_pY -s -o custom_dir
python main.py https://www.youtube.com/watch?v=OFk8HvCr_pY -w
"""

import sys
import json
import os
import argparse
import asyncio
import logging

# Import from the services directory
from services.transcript_service import get_video_transcript_data, get_video_id_from_url
from services.youtube_data_api import get_youtube_video_data
from utils.state_manager import StateManager
from workflow.graph import create_workflow, YTAnalysisState, ExtractInfoNode

def make_json_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if hasattr(obj, 'to_dict') and callable(obj.to_dict):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return {k: make_json_serializable(v) for k, v in obj.__dict__.items() 
                if not k.startswith('_')}
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    else:
        try:
            # Test if it's JSON serializable
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            # If not serializable, convert to string
            return str(obj)

def run_workflow(video_id, video_info, transcript_data):
    """Run the analysis workflow synchronously"""
    workflow = create_workflow()
    channel_id = video_info.get("channel", {}).get("id", "unknown")
    
    state_manager = StateManager()
    initial_state = YTAnalysisState(
        state=state_manager.initialize_state(channel_id, video_id),
        youtube_data={
            "video_id": video_id,
            "transcript": transcript_data.get("transcript", []),
            "video_info": video_info
        }
    )
    
    # Run the workflow using the ExtractInfoNode directly
    print("Starting workflow execution...")
    extractInfoNode = ExtractInfoNode()
    result = extractInfoNode.run(GraphRunContext(state=initial_state))
    print("Workflow execution completed")
    
    return result.value

def main():
   # Set up argument parser
   parser = argparse.ArgumentParser(description='YouTube video analysis')
   parser.add_argument('url', help='YouTube video URL')
   parser.add_argument('--save', '-s', action='store_true', help='Save output to file')
   parser.add_argument('--output', '-o', default='output', help='Output directory')
   parser.add_argument('--workflow', '-w', action='store_true', help='Run the full analysis workflow')
   parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output')
   args = parser.parse_args()
   
   # Set up logging
   log_level = logging.DEBUG if args.debug else logging.INFO
   logging.basicConfig(level=log_level, 
                      format='%(asctime)s - %(levelname)s: %(message)s')
   
   # Extract video ID from URL
   video_id = get_video_id_from_url(args.url)
   if not video_id:
       print(f"Could not extract video ID from URL: {args.url}")
       sys.exit(1)
   
   # Fetch transcript data
   transcript_data = get_video_transcript_data(args.url)
   
   # Fetch YouTube video and channel data
   video_info = get_youtube_video_data(video_id, include_channel_videos=False)
   
   # Combine the results
   result = {
       "video_id": video_id,
       "transcript": transcript_data["transcript"] if transcript_data else [],
       "available_transcripts": transcript_data.get("available_transcripts", {}) if transcript_data else {},
       "video_info": video_info
   }
   
   # Run workflow if requested
   if args.workflow:
       try:
           workflow_result = run_workflow(video_id, video_info, transcript_data)
           result["workflow_output"] = workflow_result
           print(f"Workflow completed successfully")
       except Exception as e:
           print(f"Workflow error: {e}")
           if args.debug:
               import traceback
               traceback.print_exc()
           result["workflow_error"] = str(e)
   
   # Make result JSON serializable
   serializable_result = make_json_serializable(result)
   
   # Print to screen by default
   print(json.dumps(serializable_result, indent=2))
   
   # Save to file if requested
   if args.save:
       os.makedirs(args.output, exist_ok=True)
       output_file = f"{args.output}/{video_id}.json"
       with open(output_file, "w") as f:
           json.dump(serializable_result, f, indent=2)
       print(f"Data saved to {output_file}")

if __name__ == "__main__":
   main()