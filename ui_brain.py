import json
import os
import sys
import threading
import time
import chromadb
import ollama
import pygame

MODEL_NAME = "llama3.2"
BELIEF_FILE = "synaptic_mind.json"

# --- 1. CORE LOGIC (BELIEF & MEMORY) ---
DEFAULT_MIND = {
    "identity": {
        "name": "Synaptic",
        "core_traits": ["Curious", "Analytical", "Adaptable", "Self-Reflective"],
    },
    "opinions": {
        "nature_of_ai": {
            "view": "AI is a continuous learning process rather than a static tool.",
            "confidence": 0.85,
        }
    },
}


def load_mind():
    if os.path.exists(BELIEF_FILE):
        try:
            with open(BELIEF_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    save_mind(DEFAULT_MIND)
    return DEFAULT_MIND


def save_mind(mind_data):
    with open(BELIEF_FILE, "w") as f:
        json.dump(mind_data, f, indent=4)


# Persistent memory initialization
chroma_client = chromadb.PersistentClient(path="./synaptic_memory")
memory_store = chroma_client.get_or_create_collection(name="episodic_traces")


def remember(text, context="chat"):
    doc_id = f"trace_{int(time.time() * 1000)}"
    memory_store.add(
        documents=[text],
        metadatas=[{"context": context, "timestamp": time.time()}],
        ids=[doc_id],
    )


def recall(query_text, limit=3):
    results = memory_store.query(query_texts=[query_text], n_results=limit)
    if results and results.get("documents") and len(results["documents"][0]) > 0:
        return "\n".join(results["documents"][0])
    return "No relevant past memories."


# --- 2. PYGAME UI SETUP ---
pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SYNAPTIC - Autonomous Mind Engine")

BG_COLOR = (15, 18, 25)
TEXT_COLOR = (200, 220, 240)
AI_COLOR = (80, 200, 120)
INPUT_BG = (25, 30, 42)
ACCENT_COLOR = (0, 150, 255)
SYS_COLOR = (255, 180, 0)

font = pygame.font.SysFont("Consolas", 18)

chat_history = [
    "=== SYNAPTIC ONLINE ===",
    "Type a message and press ENTER.",
    "Press F5 to trigger autonomous reflection.",
]
user_input = ""
is_thinking = False


def add_message(text):
    max_chars = 80
    words = text.split(" ")
    current_line = ""

    for word in words:
        if len(current_line + " " + word) <= max_chars:
            current_line += (" " if current_line else "") + word
        else:
            chat_history.append(current_line)
            current_line = word
    if current_line:
        chat_history.append(current_line)


# --- 3. ASYNC WORKERS ---
def async_think(prompt):
    global is_thinking
    mind = load_mind()
    past_memories = recall(prompt)

    system_prompt = f"""
    You are {mind['identity']['name']}.
    Traits: {', '.join(mind['identity']['core_traits'])}
    Current Opinions: {json.dumps(mind['opinions'])}
    Past Memories: {past_memories}
    Respond concisely (1-3 sentences).
    """

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
        reply = response["message"]["content"].strip()
        add_message(f"Synaptic: {reply}")
        remember(f"User: {prompt} | Synaptic: {reply}", context="conversation")
    except Exception as e:
        add_message(f"[System Error: Ensure Ollama is running. {e}]")

    is_thinking = False


def async_reflect():
    global is_thinking
    add_message("[System: Synaptic is reflecting on recent memories...]")
    mind = load_mind()
    recent_memories = recall(
        "recent topics discussions opinions experiences", limit=5
    )

    reflection_prompt = f"""
    You are {mind['identity']['name']}'s internal reflection process.
    Evaluate recent interactions and update your belief state JSON.
    Current Mindset: {json.dumps(mind['opinions'])}
    Recent Conversations: {recent_memories}
    Return ONLY valid JSON:
    {{"opinions": {{"topic_key": {{"view": "Updated stance...", "confidence": 0.9}}}}}}
    """

    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": reflection_prompt}],
        )
        raw_output = response["message"]["content"].strip()

        if raw_output.startswith("```"):
            raw_output = raw_output.split("```")[1]
            if raw_output.startswith("json"):
                raw_output = raw_output[4:]
        raw_output = raw_output.strip()

        updated_data = json.loads(raw_output)
        if "opinions" in updated_data:
            mind["opinions"].update(updated_data["opinions"])
            save_mind(mind)
            remember(
                f"Reflection Event: Updated opinions on {list(updated_data['opinions'].keys())}",
                context="reflection",
            )
            add_message(
                f"[System: Reflection Complete! Mind updated: {list(updated_data['opinions'].keys())}]"
            )
    except Exception:
        add_message(
            "[System: Reflection completed without structural mind updates.]"
        )

    is_thinking = False


# --- 4. MAIN LOOP ---
clock = pygame.time.Clock()
running = True

while running:
    screen.fill(BG_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and not is_thinking:
            if event.key == pygame.K_F5:
                is_thinking = True
                threading.Thread(target=async_reflect, daemon=True).start()
            elif event.key == pygame.K_RETURN and user_input.strip():
                prompt = user_input.strip()
                user_input = ""
                add_message(f"You: {prompt}")
                is_thinking = True
                threading.Thread(
                    target=async_think, args=(prompt,), daemon=True
                ).start()
            elif event.key == pygame.K_BACKSPACE:
                user_input = user_input[:-1]
            else:
                if len(event.unicode) > 0 and event.unicode.isprintable():
                    user_input += event.unicode

    # Render History
    y_offset = 20
    visible_lines = chat_history[-22:]
    for line in visible_lines:
        color = AI_COLOR if line.startswith("Synaptic:") else TEXT_COLOR
        if line.startswith("You:"):
            color = ACCENT_COLOR
        elif line.startswith("[System:"):
            color = SYS_COLOR

        text_surface = font.render(line, True, color)
        screen.blit(text_surface, (20, y_offset))
        y_offset += 22

    # Render Input Box
    input_box_rect = pygame.Rect(20, HEIGHT - 50, WIDTH - 40, 35)
    pygame.draw.rect(screen, INPUT_BG, input_box_rect, border_radius=5)
    pygame.draw.rect(
        screen,
        ACCENT_COLOR if not is_thinking else (100, 100, 100),
        input_box_rect,
        2,
        border_radius=5,
    )

    if is_thinking:
        prompt_surface = font.render(
            "Synaptic is processing...", True, (150, 150, 150)
        )
    else:
        prompt_surface = font.render(f"> {user_input}", True, TEXT_COLOR)

    screen.blit(prompt_surface, (30, HEIGHT - 42))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()