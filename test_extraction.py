# test_extraction.py
import asyncio
import json
import logging
from agents.info_extractor import extract_info, save_extraction_results

async def test_extraction(json_file):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Loading test data from {json_file}")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Get video ID and data
    video_id = data.get('video_id', json_file.replace('.json', ''))
    transcript = data.get('transcript', [])
    video_metadata = {
        'video': data.get('video_info', {}).get('video', {}),
        'channel': data.get('video_info', {}).get('channel', {})
    }
    
    logger.info(f"Running extraction for video {video_id} with {len(transcript)} transcript segments")
    
    # Run extraction
    results = await extract_info(transcript, video_metadata)
    
    # Save results
    output_path = await save_extraction_results(video_id, results)
    
    # Log summary
    software_count = len(results.get('software', []))
    keywords_count = len(results.get('tags', []))
    
    logger.info(f"Extraction complete! Found {software_count} software mentions and {keywords_count} keywords")
    
    if software_count > 0:
        logger.info("Software mentions:")
        for i, software in enumerate(results.get('software', [])[:5]):  # Show first 5
            logger.info(f"  {i+1}. {software.get('name')}: {software.get('description', 'No description')}")
    
    if keywords_count > 0:
        logger.info("Sample keywords:")
        sample_keywords = results.get('tags', [])[-10:] if len(results.get('tags', [])) > 10 else results.get('tags', [])
        for keyword in sample_keywords:
            logger.info(f"  - {keyword}")
    
    logger.info(f"Full results saved to {output_path}")
    return results

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python test_extraction.py <json_file>")
        sys.exit(1)
        
    json_file = sys.argv[1]
    asyncio.run(test_extraction(json_file))