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
                    if action == "none":
                        await asyncio.sleep(1)
                        success = True
                    elif action == "press":
                        key = task.get("key", "space")
                        times = int(task.get("times", 1))
                        for _ in range(times):
                            loop = asyncio.get_running_loop()
                            success, msg = await loop.run_in_executor(None, self.executor.execute, {"action": "press", "key": key})
                            await asyncio.sleep(0.1)
                    else:
                        loop = asyncio.get_running_loop()
                        success, inline_msg = await loop.run_in_executor(None, self.executor.execute, task)
                        msg = inline_msg if inline_msg else msg

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

