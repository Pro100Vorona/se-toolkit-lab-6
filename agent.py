#!/usr/bin/env python3
import os
import sys
import json
import argparse
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv('.env.agent.secret')

PROJECT_ROOT = Path(__file__).parent.absolute()

def safe_path(user_path: str) -> Path:
    requested = (PROJECT_ROOT / user_path).resolve()
    if not str(requested).startswith(str(PROJECT_ROOT)):
        raise ValueError(f"Доступ за пределы проекта запрещён: {user_path}")
    return requested

def read_file(path: str) -> str:
    try:
        full_path = safe_path(path)
        if not full_path.is_file():
            return f"Ошибка: файл {path} не найден"
        return full_path.read_text(encoding='utf-8')
    except Exception as e:
        return f"Ошибка чтения файла {path}: {str(e)}"

def list_files(path: str = ".") -> str:
    try:
        full_path = safe_path(path)
        if not full_path.is_dir():
            return f"Ошибка: {path} не является директорией"
        entries = list(full_path.iterdir())
        names = sorted(e.name + ("/" if e.is_dir() else "") for e in entries)
        return "\n".join(names)
    except Exception as e:
        return f"Ошибка при листинге {path}: {str(e)}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Прочитать содержимое файла внутри проекта. Указывай относительный путь от корня проекта.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Путь к файлу относительно корня проекта, например 'wiki/git-workflow.md'"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Получить список файлов и директорий по указанному пути. Путь должен быть относительным, например 'wiki'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Путь к директории относительно корня проекта (по умолчанию корень проекта)"}
                },
                "required": []
            }
        }
    }
]

def execute_tool_call(tool_call):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    if name == "read_file":
        result = read_file(args["path"])
    elif name == "list_files":
        path = args.get("path", ".")
        result = list_files(path)
    else:
        result = f"Неизвестный инструмент: {name}"
    return {
        "tool": name,
        "args": args,
        "result": result
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('question')
    args = parser.parse_args()

    api_key = os.getenv('LLM_API_KEY')
    api_base = os.getenv('LLM_API_BASE')
    model = os.getenv('LLM_MODEL')
    if not all([api_key, api_base, model]):
        print("Missing LLM env vars", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url=api_base, timeout=60)

    system_prompt = (
        "Ты – Documentation Agent. Твоя задача – отвечать на вопросы, используя документацию из папки wiki.\n"
        "У тебя есть инструменты: read_file (прочитать файл) и list_files (посмотреть содержимое папки).\n"
        "Сначала исследуй wiki с помощью list_files, затем читай нужные файлы через read_file.\n"
        "Когда найдёшь ответ, обязательно укажи источник в формате 'Source: wiki/имя_файла.md#раздел' (раздел можно вывести из markdown-заголовков).\n"
        "Если не уверен – продолжай исследование, но не делай больше 10 вызовов инструментов.\n"
        "В конечном ответе просто напиши ответ, а источник добавь отдельно строкой Source: ...\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": args.question}
    ]

    tool_calls_history = []
    max_turns = 10
    turn = 0

    while turn < max_turns:
        turn += 1
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.0
            )
        except Exception as e:
            print(f"Ошибка при вызове LLM: {e}", file=sys.stderr)
            sys.exit(1)

        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)
            for tool_call in message.tool_calls:
                result_info = execute_tool_call(tool_call)
                tool_calls_history.append(result_info)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_info["result"]
                })
            continue
        else:
            content = message.content or ""
            source = ""
            if "Source:" in content:
                parts = content.split("Source:")
                if len(parts) > 1:
                    source = parts[1].split("\n")[0].strip()
                    content = parts[0].strip()
            answer = content.strip()
            result = {
                "answer": answer,
                "source": source,
                "tool_calls": tool_calls_history
            }
            print(json.dumps(result, ensure_ascii=False))
            break
    else:
        result = {
            "answer": "Не удалось найти ответ за допустимое число шагов.",
            "source": "",
            "tool_calls": tool_calls_history
        }
        print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
