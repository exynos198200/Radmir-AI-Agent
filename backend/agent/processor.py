import os
from google import genai
import json

class AgentProcessor:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            print("WARNING: GEMINI_API_KEY not found.")

    def process_command(self, command: str, image_context=None):
        self.memory.add_message("user", command)
        
        if not self.enabled:
            reply = "Gemini API ключ не настроен. Бэкенд генерирует запасной план."
            self.memory.add_message("agent", reply)
            mock_tasks = [
                {"id": 1, "title": "Анализ (нет связи)", "status": "pending", "tag": "MOCK", "action": "none"},
                {"id": 2, "title": "Нажать пробел 1 раз", "status": "pending", "tag": "REAL", "action": "press", "key": "space", "times": 1}
            ]
            return reply, mock_tasks

        try:
            system_prompt = """Ты системный процесс, управляющий ПК. Разбей задачу пользователя на системные шаги.
Формат ответа строго JSON:
{
  "reply": "Сообщение для юзера",
  "tasks": [
    {"id": 1, "title": "Шаг", "status": "pending", "tag": "REAL", "action": "press|none", "key": "кнопка", "times": 1}
  ]
}
Только реальные действия (press) с tag: REAL. Не симулируй."""
            model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            response = self.client.models.generate_content(
                model=model_name,
                contents=system_prompt + "\nЗадача: " + command
            )
            
            raw_text = response.text
            clean_json = raw_text.replace("```json", "").replace("```", "").strip()
            
            try:
                parsed = json.loads(clean_json)
                reply = parsed.get("reply", "План сформирован (REAL).")
                tasks = parsed.get("tasks", [])
                self.memory.add_message("agent", reply)
                return reply, tasks
            except Exception as e:
                return f"Ошибка JSON: {str(e)}", []
            
        except Exception as e:
            return f"Ошибка Gemini: {str(e)}", []
