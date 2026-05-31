import asyncio
import pyautogui
import keyboard

class LocalExecutor:
    def __init__(self):
        self.ws_manager = None

    def set_ws_manager(self, manager):
        self.ws_manager = manager

    async def execute_tasks(self, tasks: list):
        if not self.ws_manager:
            return
        
        for i, task in enumerate(tasks):
            task["status"] = "in-progress"
            tasks[i] = task
            await self.ws_manager.send_message({"type": "tasks", "data": tasks})
            
            tag = task.get("tag", "DISABLED")
            if tag == "REAL":
                action = task.get("action")
                try:
                    if action == "press":
                        key = task.get("key", "space")
                        times = int(task.get("times", 1))
                        for _ in range(times):
                            pyautogui.press(key)
                            await asyncio.sleep(0.1)
                    elif action == "none":
                        await asyncio.sleep(1)
                    
                    task["status"] = "completed"
                except Exception as e:
                    task["status"] = "failed"
                    task["title"] = f"{task['title']} (Экзекутор Ошибка: {str(e)})"
            elif tag == "MOCK":
                await asyncio.sleep(1)
                task["status"] = "completed"
            else:
                task["status"] = "failed"
                task["title"] = f"{task['title']} (DISABLED)"
            
            tasks[i] = task
            await self.ws_manager.send_message({"type": "tasks", "data": tasks})
