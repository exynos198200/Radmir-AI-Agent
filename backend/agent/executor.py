import asyncio
import pyautogui
# Use the new robust system architecture
from .system_controllers import ActionExecutor

class LocalExecutor:
    def __init__(self):
        self.ws_manager = None
        self.executor = ActionExecutor()

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
                success, msg = False, "No action executed"
                action = task.get("action")
                try:
                    if action == "press":
                        key = task.get("key", "space")
                        times = int(task.get("times", 1))
                        for _ in range(times):
                            success, msg = self.executor.execute({"action": "press", "key": key})
                            await asyncio.sleep(0.1)
                    elif action == "hotkey":
                        keys = task.get("keys", ["windows", "r"])
                        success, msg = self.executor.execute({"action": "hotkey", "keys": keys})
                    elif action == "launch":
                        prog = task.get("program", "")
                        proc = task.get("process", prog + ".exe")
                        success, msg = self.executor.execute({"action": "launch", "program": prog, "process": proc})
                    elif action == "mouse_click":
                        success, msg = self.executor.execute({"action": "mouse_click", "button": task.get("button", "left")})
                    elif action == "game_action":
                        success, msg = self.executor.execute({"action": "game_action", "cmd": task.get("cmd", "")})
                    elif action == "none":
                        await asyncio.sleep(1)
                        success = True
                    else:
                        success, msg = self.executor.execute(task) # pass directly if matched

                    if success:
                        task["status"] = "completed"
                    else:
                        task["status"] = "failed"
                        task["title"] = f"{task['title']} (Экзекутор Ошибка: {msg})"

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

