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

Examples:
 python main.py https://www.youtube.com/watch?v=OFk8HvCr_pY
 python main.py https://www.youtube.com/watch?v=OFk8HvCr_pY --save
 python main.py https://www.youtube.com/watch?v=OFk8HvCr_pY -s -o custom_dir
"""

import sys
import json
import os
import argparse

# Import from the services directory
from services.transcript_service import get_video_transcript_data, get_video_id_from_url
from services.youtube_data_api import get_youtube_video_data

def main():
   # Set up argument parser
   parser = argparse.ArgumentParser(description='YouTube video analysis')
   parser.add_argument('url', help='YouTube video URL')
   parser.add_argument('--save', '-s', action='store_true', help='Save output to file')
   parser.add_argument('--output', '-o', default='output', help='Output directory')
   args = parser.parse_args()
   
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
   
   # Print to screen by default
   print(json.dumps(result, indent=2))
   
   # Save to file if requested
   if args.save:
       os.makedirs(args.output, exist_ok=True)
       output_file = f"{args.output}/{video_id}.json"
       with open(output_file, "w") as f:
           json.dump(result, f, indent=2)
       print(f"Data saved to {output_file}")

if __name__ == "__main__":
   main()