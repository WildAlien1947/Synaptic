import json
import ollama
from assets.belief import load_mind
from assets.memory import remember, recall

MODEL_NAME = "llama3.2"  # Or another model running on your local Ollama setup

def think_and_respond(user_input):
    mind = load_mind()
    past_memories = recall(user_input)

    system_prompt = f"""
    You are {mind['identity']['name']}.
    Traits: {', '.join(mind['identity']['core_traits'])}
    
    Current Mindset & Opinions:
    {json.dumps(mind['opinions'], indent=2)}

    Relevant Past Memories:
    {past_memories}

    Respond naturally. Hold your ground if you have high confidence on an opinion, 
    but remain open to updating your stance if presented with clear logic.
    """

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )

    reply = response['message']['content']
    
    # Store the exchange in memory
    remember(f"User: {user_input} | Synaptic: {reply}", context="conversation")
    return reply

if __name__ == "__main__":
    print("=== SYNAPTIC ONLINE ===")
    print("Type your message, or 'quit' to exit.\n")
    
    while True:
        prompt = input("You: ")
        if prompt.lower() in ["quit", "exit"]:
            break
        output = think_and_respond(prompt)
        print(f"\nSynaptic: {output}\n")