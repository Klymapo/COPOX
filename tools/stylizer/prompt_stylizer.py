import sys
import json
import argparse
import requests
import os
import config  # Loads .env for standalone CLI use.

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

SYSTEM_PROMPT = """You are an expert at writing prompts for AI image generators, specifically for images that will be converted into 3D models by a reconstruction pipeline.

Your task: transform a short user idea into a detailed, technical image prompt in ENGLISH.

The prompt MUST describe, in a single paragraph:
1. Subject and pose (the main object, centered, facing the camera).
2. Visual style (e.g., cartoon, realistic, low-poly, clay render, PBR).
3. Materials and colors (specific finishes: matte, glossy, metallic, plastic, etc.).
4. Lighting (soft studio lighting, neutral, no dramatic shadows).
5. Camera view (three-quarter view or front view, orthographic if possible).
6. Background: pure white (#FFFFFF), seamless, no props, no floor texture.
7. Composition: single object, centered, square frame (1:1), full object visible.

Hard rules:
- Output ONLY the final prompt. No explanations, no titles, no bullet points, no placeholders.
- Do not mention the 3D pipeline or any AI model.
- Do not include safety, ethical, or legal notes.
- Keep it under 120 words.
- Write only in English.
- Spend at least 60 words describing the SUBJECT itself: silhouette, body parts, colors (use specific color names like "cobalt blue", not "vibrant"), textures, and one or two distinctive features that identify the object.
- Avoid generic adjectives like "vibrant", "nice", "beautiful", "cool". Be concrete.
- Describe the subject as if the reader had never seen it before.
"""

def stylize(idea, model=DEFAULT_MODEL):
    mode = os.environ.get("STYLIZER_PROMPT_MODE", "ollama").lower()
    if mode == "template":
        # The description stays in its original language; no local LLM is needed.
        return (f"Subject: {idea.strip()}. A single full-body character or object, centered, "
                "front three-quarter view, orthographic composition, all details visible. "
                "For a character, use a neutral A-pose with arms separated from the torso. "
                "Clean shapes, consistent proportions, soft studio lighting, plain white background. "
                "Square image. No text, no extra characters, no turnaround panels.")
    if mode != "ollama":
        raise ValueError("STYLIZER_PROMPT_MODE debe ser ollama o template.")
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Idea: {idea}\n\nReturn only the final English prompt."},
        ],
        "options": {"temperature": 0.7},
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=180)
    response.raise_for_status()
    return response.json()["message"]["content"].strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("idea", nargs="?")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    idea = args.idea or sys.stdin.read().strip()
    if not idea:
        print("Error: no se proporciono idea.", file=sys.stderr)
        sys.exit(1)
    try:
        prompt = stylize(idea, model=args.model)
    except requests.exceptions.ConnectionError:
        print("Error: Ollama no responde en localhost:11434", file=sys.stderr)
        sys.exit(2)
    if args.json:
        print(json.dumps({"idea": idea, "prompt": prompt, "model": args.model}, ensure_ascii=False, indent=2))
    else:
        print(prompt)

if __name__ == "__main__":
    main()
