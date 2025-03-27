# direct_extract.py
import asyncio
import json
import logging
import sys
from agents.info_extractor import extract_info, save_extraction_results
from services.transcript_service import get_video_transcript_data, get_video_id_from_url
from services.youtube_data_api import get_youtube_video_data

logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s: %(message)s')

async def extract_video_info(video_url):
    # Extract video ID
    video_id = get_video_id_from_url(video_url)
    if not video_id:
        print(f"Could not extract video ID from URL: {video_url}")
        return None
    
    logging.info(f"Processing video ID: {video_id}")
    
    # Fetch transcript data
    logging.info("Fetching transcript data...")
    transcript_data = get_video_transcript_data(video_url)
    
    # Fetch YouTube video and channel data
    logging.info("Fetching video and channel data...")
    video_info = get_youtube_video_data(video_id, include_channel_videos=False)
    
    # Prepare metadata for extraction
    video_metadata = {
        'video': video_info.get("video", {}),
        'channel': video_info.get("channel", {})
    }
    
    # Run extraction directly
    logging.info("Running info extraction...")
    results = await extract_info(transcript_data.get("transcript", []), video_metadata)
    
    # Save results
    output_path = await save_extraction_results(video_id, results)
    logging.info(f"Results saved to {output_path}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    else:
        video_url = "https://www.youtube.com/watch?v=eIJ6bSxD5so"
    
    print(f"Extracting info from: {video_url}")
    results = asyncio.run(extract_video_info(video_url))
    print("\nExtraction results:")
    print(json.dumps(results, indent=2))