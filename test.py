# test_ollama.py
import ollama
import json
import asyncio
from ollama import AsyncClient


def test_ollama():
    print("Testing Ollama connection...")
    
    try:
        # Simple test prompt
        prompt = "Extract keywords from this text: Python is a programming language that is widely used for web development, data analysis, AI, and scientific computing."
        
        # Test with the specific model
        print(f"Testing the gemma3:12b-8k model...")
        response = ollama.chat(
            model="gemma3:12b-8k",
            messages=[{"role": "user", "content": prompt}]
        )
        
        print(f"Response received!")
        print(f"Raw response type: {type(response)}")
        print(f"Content: {response.message.content}")
        
        # Try to parse the JSON if it's a string
        try:
            if isinstance(response.message.content, str) and "{" in response.message.content:
                json_str = response.message.content
                if "```json" in json_str:
                    json_str = json_str.split("```json", 1)[1].split("```", 1)[0].strip()
                json_data = json.loads(json_str)
                print(f"Parsed JSON: {json_data}")
        except json.JSONDecodeError:
            print("Content is not valid JSON")
        
        print("Ollama test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing Ollama: {str(e)}")
        print(f"Error type: {type(e)}")
        return False
    
async def test_ollama_async():
    print("Testing Ollama connection using AsyncClient...")
    
    try:
        # Simple test prompt
        prompt = "Extract keywords from this text: Python is a programming language that is widely used for web development, data analysis, AI, and scientific computing."
        
        # Test with the specific model
        print(f"Testing the gemma3:12b-8k model...")
        client = AsyncClient()
        response = await client.chat(
            model="gemma3:12b-8k",
            messages=[{"role": "user", "content": prompt}]
        )
        
        print(f"Response received!")
        print(f"Raw response type: {type(response)}")
        print(f"Content: {response['message']['content']}")
        
        # Try to parse the JSON if it's a string
        try:
            if isinstance(response['message']['content'], str) and "{" in response['message']['content']:
                json_str = response['message']['content']
                if "```json" in json_str:
                    json_str = json_str.split("```json", 1)[1].split("```", 1)[0].strip()
                json_data = json.loads(json_str)
                print(f"Parsed JSON: {json_data}")
        except json.JSONDecodeError:
            print("Content is not valid JSON")
        
        print("Ollama async test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing Ollama: {str(e)}")
        print(f"Error type: {type(e)}")
        return False

if __name__ == "__main__":
    # Run synchronous test
    test_ollama()
    
    # Run async test properly
    asyncio.run(test_ollama_async())