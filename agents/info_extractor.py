# agents/info_extractor.py

import ollama
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

async def extract_info(
    transcript: List[Dict[str, Any]],
    video_metadata: Dict[str, Any],
    processes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Extract software mentions, tags, and additional metadata from video content"""
    # Prepare transcript text
    transcript_text = " ".join([item.get("text", "") for item in transcript])
    if len(transcript_text) > 16000:
        transcript_text = transcript_text[:16000] + "..."
    
    # Extract existing video data
    video_data = video_metadata.get('video', {})
    channel_data = video_metadata.get('channel', {})
    
    # Get existing tags from API data (if any)
    existing_tags = video_data.get('tags', [])
    
    # Normalize metadata
    metadata = {
        "title": video_data.get('title', ''),
        "description": video_data.get('description', ''),
        "publish_date": video_data.get('publishedAt', ''),
        "view_count": video_data.get('views', 0),
        "like_count": video_data.get('likes', 0),
        "comment_count": video_data.get('comments', {}).get('commentCount', 0),
        "channel_id": channel_data.get('id', ''),
        "channel_name": channel_data.get('title', ''),
        "subscriber_count": channel_data.get('subscriberCount', 0),
        "thumbnail_path": video_data.get('thumbnail', '')
    }
    
    # Prompt for LLM
    prompt = f"""Extract all software tools and related terms from this YouTube video:

Video: {metadata['title']}
Description excerpt: {metadata['description'][:300]}...

Transcript excerpt:
{transcript_text[:4000]}...

Format response as JSON:
```json
{{
  "software": [
    {{ "name": "Software Name", "description": "Brief description of its purpose and how it's used in the video", "mentions": count }}
  ],
  "additional_tags": ["tag1", "tag2", "tag3"]
}}
```

For software:
- Include ALL software products, platforms, and digital tools
- Focus on their purpose and how they're used in the video
- Count actual mentions accurately
- Be specific (e.g., "Deepseek R1" rather than just "AI")

For tags:
- Focus on identifying relevant keywords not already in: {existing_tags}
- Include specific techniques, methodologies, and key concepts
- Prioritize technical terms over generic descriptions
"""

    try:
        # Call LLM
        response = await ollama.chat(
            model="llama3.2:latest",
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.1}
        )
        
        # Extract content
        content = response["message"]["content"]
        
        # Parse JSON
        if "```json" in content:
            json_str = content.split("```json", 1)[1].split("```", 1)[0].strip()
            extracted_data = json.loads(json_str)
        else:
            extracted_data = json.loads(content)
        
        # Combine existing and additional tags
        all_tags = existing_tags.copy()
        for tag in extracted_data.get("additional_tags", []):
            if tag not in all_tags:
                all_tags.append(tag)
        
        # Create final result
        result = {
            "metadata": metadata,
            "software": extracted_data.get("software", []),
            "tags": all_tags
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error during info extraction: {e}")
        return {
            "metadata": metadata,
            "software": [],
            "tags": existing_tags,
            "error": str(e)
        }
