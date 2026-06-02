import os
from google import genai
import json

class AgentProcessor:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        
        self.use_free_api = False
        self.use_deepseek = False
        
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "sk-7550e1e31d75425dbcf6d288842003a5")
        
        if deepseek_api_key and deepseek_api_key.strip():
            self.use_deepseek = True
            from openai import OpenAI
            self.client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")
            self.enabled = True
            print("Using DeepSeek API.")
        elif gemini_api_key and gemini_api_key.strip():
            self.client = genai.Client(api_key=gemini_api_key)
            self.enabled = True
            print("Using Gemini API.")
        else:
            self.client = None
            self.enabled = True
            self.use_free_api = True
            print("WARNING: API keys not found. Using Free API (g4f) fallback.")

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
            import time
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
            
            response_text = None
            last_err = None
            for _ in range(3):
                try:
                    if self.use_deepseek:
                        resp = self.client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": "Задача: " + command}
                            ]
                        )
                        response_text = resp.choices[0].message.content
                    elif self.use_free_api:
                        from g4f.client import Client as G4FClient
                        g4f_client = G4FClient()
                        resp = g4f_client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": "Задача: " + command}
                            ]
                        )
                        response_text = resp.choices[0].message.content
                    else:
                        response = self.client.models.generate_content(
                            model=model_name,
                            contents=system_prompt + "\nЗадача: " + command
                        )
                        response_text = response.text
                    break
                except Exception as ex:
                    last_err = ex
                    time.sleep(1.5)
                    
            if response_text is None:
                raise last_err
            
            clean_json = response_text.replace("```json", "").replace("```", "").strip()
            
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
