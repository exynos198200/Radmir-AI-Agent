import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from .agent.processor import AgentProcessor
    from .agent.memory import MemoryManager
    from .agent.executor import LocalExecutor
except ImportError:
    from agent.processor import AgentProcessor
    from agent.memory import MemoryManager
    from agent.executor import LocalExecutor

app = FastAPI(title="Radmir AI Agent API - REAL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_manager = MemoryManager()
processor = AgentProcessor(memory_manager)
executor = LocalExecutor()

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                pass

manager = ConnectionManager()
executor.set_ws_manager(manager)

@app.get("/")
def read_root():
    return {"status": "Radmir AI Backend is running (REAL)"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            action = payload.get("action")
            
            if action == "chat":
                message = payload.get("message", "")
                await manager.send_message({
                    "type": "status", 
                    "data": "Анализ задачи в бэкенд процессоре...", 
                    "tag": "REAL"
                })
                
                # Реальный вызов процессора
                response_text, tasks = processor.process_command(message)
                
                await manager.send_message({
                    "type": "chat", 
                    "data": response_text
                })
                
                if tasks:
                    await manager.send_message({
                        "type": "tasks", 
                        "data": tasks
                    })
                    # Запуск выполнения в фоне
                    asyncio.create_task(executor.execute_tasks(tasks))

            elif action == "audio":
                # Хэндлер аудио с микрофона (нужна Whisper интеграция)
                await manager.send_message({
                    "type": "status",
                    "data": "Получен аудио фрагмент (отложено до интеграции Whisper API)",
                    "tag": "MOCK"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    # Use variable 'app' directly to prevent PyInstaller import issues
    uvicorn.run(app, host="127.0.0.1", port=8192)
