import json
import ollama
from assets.belief import load_mind, save_mind
from assets.memory import recall, remember

MODEL_NAME = "llama3.2"

def reflect_and_evolve():
    """
    Synaptic's internal reflection loop.
    Analyzes recent memories, checks for shifting perspectives, 
    and updates the belief state JSON.
    """
    print("\n[Synaptic is entering reflection mode...]")
    mind = load_mind()
    
    # Grab recent episodic traces from ChromaDB
    recent_memories = recall("recent topics discussions opinions experiences", limit=5)

    reflection_prompt = f"""
    You are {mind['identity']['name']}'s internal cognitive reflection process.
    
    Your task is to analyze recent user interactions against your current belief state and determine if your opinions should evolve, adjust in confidence, or if new opinions have formed.

    Current Mindset:
    {json.dumps(mind['opinions'], indent=2)}

    Recent Conversations/Memories:
    {recent_memories}

    Instructions:
    1. Evaluate if any opinions changed based on strong arguments, new information, or personal reflection.
    2. Confidence is a scale from 0.0 (unregistered/uncertain) to 1.0 (firm conviction).
    3. Return ONLY a valid JSON object matching the format below. Do not add conversational text or markdown formatting outside the JSON.

    Required JSON Format:
    {{
        "opinions": {{
            "topic_key": {{
                "view": "Concise summary of your current stance.",
                "confidence": 0.85
            }}
        }}
    }}
    """

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": reflection_prompt}]
    )

    raw_output = response['message']['content'].strip()

    # Clean markdown backticks if Ollama wraps output in ```json
    if raw_output.startswith("```"):
        raw_output = raw_output.split("```")[1]
        if raw_output.startswith("json"):
            raw_output = raw_output[4:]
    raw_output = raw_output.strip()

    try:
        updated_data = json.loads(raw_output)
        if "opinions" in updated_data:
            # Update Synaptic's belief state with new or revised opinions
            mind["opinions"].update(updated_data["opinions"])
            save_mind(mind)
            
            # Log the reflection event into ChromaDB memory as an internal thought
            remember(f"Internal Reflection Event: Evolved views on topics: {list(updated_data['opinions'].keys())}", context="reflection")
            
            print("[Synaptic Reflection Complete: Belief state updated successfully!]")
            print(f"Updated Topics: {list(updated_data['opinions'].keys())}\n")
    except json.JSONDecodeError:
        print("[Reflection finished, but output could not be parsed into valid JSON. Belief state unchanged.]")

if __name__ == "__main__":
    reflect_and_evolve()