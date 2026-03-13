import subprocess
import json
import sys

def test_merge_conflict_question():
    # Вопрос, который должен привести к использованию read_file для git-workflow.md
    cmd = [sys.executable, "agent.py", "How do you resolve a merge conflict?"]
    # Запускаем agent.py как подпроцесс, захватываем stdout и stderr
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    
    # Проверяем, что процесс завершился успешно (код 0)
    assert result.returncode == 0, f"Ошибка: {result.stderr}"
    
    # Парсим stdout как JSON
    output = json.loads(result.stdout)
    
    # Проверяем наличие обязательных полей
    assert "answer" in output
    assert "source" in output
    assert "tool_calls" in output
    assert isinstance(output["tool_calls"], list)
    
    # Проверяем, что среди вызовов инструментов есть read_file с путём, содержащим git-workflow.md
    found = False
    for call in output["tool_calls"]:
        if call.get("tool") == "read_file":
            path = call.get("args", {}).get("path", "")
            if "git-workflow.md" in path:
                found = True
                break
    assert found, "Не найден вызов read_file для git-workflow.md"
    
    # Проверяем, что source содержит путь к wiki/git-workflow.md
    assert "wiki/git-workflow.md" in output["source"], f"Источник: {output['source']}"
    
    print("✅ test_merge_conflict_question passed")

def test_list_files_wiki():
    # Вопрос о содержимом директории wiki
    cmd = [sys.executable, "agent.py", "What files are in the wiki directory?"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    
    # Проверяем наличие полей
    assert "answer" in output
    assert "source" in output
    assert "tool_calls" in output
    
    # Проверяем, что был вызов list_files с путём wiki
    found = False
    for call in output["tool_calls"]:
        if call.get("tool") == "list_files":
            path = call.get("args", {}).get("path")
            if path == "wiki":
                found = True
                break
    assert found, "Не найден вызов list_files для wiki"
    
    print("✅ test_list_files_wiki passed")

if __name__ == "__main__":
    test_merge_conflict_question()
    test_list_files_wiki()
