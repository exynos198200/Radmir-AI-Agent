import os
import json
import httpx
import time
import uuid

class AgentProcessor:
    def __init__(self, memory_manager):
        self.memory = memory_manager
        
        self.enabled = True
        self.gigachat_token = "MDE5ZTg3ODMtNzAwNi03ZWQzLWE0ZjAtYzExOWZmNzk4ZjMyOjhjNTFiYmNiLWI4MDQtNDlmNC1hYTA5LWZkNTY1MGQwY2E3ZA=="
        self.access_token = None
        self.token_expiry = 0
        
        print("Using GigaChat API.")

    def _get_access_token(self):
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token
            
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {self.gigachat_token}'
        }
        
        with httpx.Client(verify=False) as client:
            response = client.post(url, headers=headers, data='scope=GIGACHAT_API_PERS')
            response.raise_for_status()
            data = response.json()
            self.access_token = data['access_token']
            self.token_expiry = (data['expires_at'] / 1000) - 60
            return self.access_token

    def _generate_content(self, system_prompt, user_prompt):
        token = self._get_access_token()
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        payload = {
            "model": "GigaChat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        with httpx.Client(verify=False, timeout=30.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']

    def process_command(self, command: str, image_context=None):
        self.memory.add_message("user", command)
        
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
            
            response_text = None
            last_err = None
            for _ in range(3):
                try:
                    response_text = self._generate_content(system_prompt, "Задача: " + command)
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
            return f"Ошибка GigaChat: {str(e)}", []
