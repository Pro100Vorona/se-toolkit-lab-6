# План Task 1
- Провайдер: OpenRouter
- Модель: meta-llama/llama-3.3-70b-instruct:free
- agent.py: через OpenAI SDK, чтение из .env.agent.secret
- Вывод: JSON с answer и tool_calls
- Тест: test_agent.py через subprocess
