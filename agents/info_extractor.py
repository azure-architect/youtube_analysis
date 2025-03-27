# agents/info_extractor.py
import ollama
from ollama import AsyncClient
import json
import logging
import os
import asyncio
from typing import Dict, Any, List
from utils.retry_handler import RetryHandler

logger = logging.getLogger(__name__)

async def extract_info(
    transcript: List[Dict[str, Any]],
    video_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract software mentions and tags from video content"""
    # Prepare transcript text
    transcript_text = " ".join([item.get("text", "") for item in transcript])
    if len(transcript_text) > 16000:
        transcript_text = transcript_text[:16000] + "..."
    
    # Extract existing video data
    video_data = video_metadata.get('video', {})
    existing_tags = video_data.get('tags', [])
    
    # Prompt for LLM
    prompt = f"""Extract all software tools and keywords from this YouTube video:

Video: {video_data.get('title', '')}
Description excerpt: {video_data.get('description', '')[:300]}...

Transcript excerpt:
{transcript_text[:4000]}...

Format response as JSON:
```json
{{
  "software": [
    {{ "name": "Software Name", "description": "Brief description", "mentions": count }}
  ],
  "keywords": ["keyword1", "keyword2", "keyword3"]
}}
```

For software: include ALL software products, platforms, and digital tools mentioned
For keywords: focus on technical terms not already in: {existing_tags}
"""

    try:
        # Call LLM with gemma model using retry handler
        result, error = await RetryHandler.retry_async(
            _call_llm,
            max_retries=2,
            phase_name="info_extraction",
            prompt=prompt
        )
        
        if error:
            logger.error(f"Failed to extract info after retries: {error.message}")
            return {
                "software": [],
                "tags": existing_tags,
                "error": error.message
            }
        
        # Extract and parse content
        content = result["message"]["content"]
        logger.info(f"Received response from LLM, content length: {len(content)}")
        
        try:
            if "```json" in content:
                json_str = content.split("```json", 1)[1].split("```", 1)[0].strip()
                extracted_data = json.loads(json_str)
            else:
                extracted_data = json.loads(content)
                
            # Combine tags
            all_tags = existing_tags.copy()
            for tag in extracted_data.get("keywords", []):
                if tag not in all_tags:
                    all_tags.append(tag)
            
            return {
                "software": extracted_data.get("software", []),
                "tags": all_tags
            }
        except json.JSONDecodeError as je:
            logger.error(f"JSON decode error: {je}, content: {content[:200]}...")
            
            # Try to extract keywords even if JSON parsing fails
            keywords = []
            try:
                for line in content.split('\n'):
                    if '**' in line:
                        possible_keyword = line.split('**')[1].strip() if '**' in line else ''
                        if possible_keyword and len(possible_keyword) > 2:
                            keywords.append(possible_keyword)
            except Exception:
                pass
                
            return {
                "software": [],
                "tags": list(set(existing_tags + keywords)),
                "error": f"JSON parsing error: {str(je)}"
            }
        
    except Exception as e:
        logger.error(f"Error during info extraction: {e}")
        return {
            "software": [],
            "tags": existing_tags,
            "error": str(e)
        }

async def _call_llm(prompt: str) -> Dict[str, Any]:
    """Call Ollama LLM with the given prompt"""
    client = AsyncClient()
    response = await client.chat(
        model="gemma3:12b-8k",
        messages=[{"role": "user", "content": prompt}],
        format="json",
        options={"temperature": 0.1}
    )
    return response

async def save_extraction_results(video_id: str, results: Dict[str, Any]) -> str:
    """Save extraction results to output folder"""
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"{video_id}_extracted_info.json")
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return output_path

async def run_extraction(video_id: str, transcript_data: List[Dict[str, Any]], video_metadata: Dict[str, Any]) -> str:
    """Run the extraction process and save results"""
    logger.info(f"Starting extraction for video {video_id}")
    results = await extract_info(transcript_data, video_metadata)
    output_path = await save_extraction_results(video_id, results)
    logger.info(f"Extraction results saved to {output_path}")
    return output_path

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) != 3:
        print("Usage: python -m agents.info_extractor <video_id> <metadata_file_path>")
        sys.exit(1)
    
    video_id = sys.argv[1]
    metadata_path = sys.argv[2]
    
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    
    transcript = data.get('transcript', [])
    video_metadata = {
        'video': data.get('video_info', {}).get('video', {}),
        'channel': data.get('video_info', {}).get('channel', {})
    }
    
    asyncio.run(run_extraction(video_id, transcript, video_metadata))
