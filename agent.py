#!/usr/bin/env python3
import os, sys, json, argparse
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('.env.agent.secret')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('question')
    args = parser.parse_args()

    api_key = os.getenv('LLM_API_KEY')
    api_base = os.getenv('LLM_API_BASE')
    model = os.getenv('LLM_MODEL')
    if not all([api_key, api_base, model]):
        print("Missing env vars", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=api_base, timeout=60)
    messages = [{"role": "user", "content": args.question}]
    try:
        resp = client.chat.completions.create(model=model, messages=messages, temperature=0)
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM error: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({"answer": answer, "tool_calls": []}))

if __name__ == "__main__":
    main()
