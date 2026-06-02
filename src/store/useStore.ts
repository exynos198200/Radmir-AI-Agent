import { create } from 'zustand';

export type TagStatus = 'REAL' | 'MOCK' | 'DISABLED';

export type Task = {
  id: number;
  title: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  tag: TagStatus;
};

export type Message = {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: string;
  tag?: TagStatus;
};

interface AppState {
  ws: WebSocket | null;
  isConnected: boolean;
  messages: Message[];
  tasks: Task[];
  isRecording: boolean;
  connect: () => void;
  sendMessage: (msg: string) => void;
  addMessage: (msg: Message) => void;
  setRecording: (status: boolean) => void;
  updateTasks: (tasks: Task[]) => void;
}

export const useStore = create<AppState>((set, get) => ({
  ws: null,
  isConnected: false,
  messages: [
    {
      id: 'welcome',
      role: 'agent',
      content: 'Привет! Я Radmir AI Agent. Для работы мне нужно реальное websocket-подключение к Python Backend.',
      timestamp: new Date().toISOString(),
      tag: 'REAL'
    }
  ],
  tasks: [],
  isRecording: false,
  connect: () => {
    const socket = new WebSocket('ws://localhost:8192/ws');
    
    socket.onopen = () => {
      set({ isConnected: true, ws: socket });
      get().addMessage({
         id: Date.now().toString(),
         role: 'system',
         content: 'Подключение к Backend установлено (WebSocket).',
         timestamp: new Date().toISOString(),
         tag: 'REAL'
      });
    };

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.type === 'chat') {
        get().addMessage({
          id: Date.now().toString(),
          role: 'agent',
          content: payload.data,
          timestamp: new Date().toISOString()
        });
      } else if (payload.type === 'tasks') {
        get().updateTasks(payload.data);
      } else if (payload.type === 'status') {
         get().addMessage({
          id: Date.now().toString(),
          role: 'system',
          content: `Системный брокер: ${payload.data}`,
          timestamp: new Date().toISOString(),
          tag: payload.tag || 'REAL'
        });
      }
    };

    socket.onclose = () => {
      if (get().isConnected) {
          get().addMessage({
              id: Date.now().toString(),
              role: 'system',
              content: 'Связь с Backend потеряна.',
              timestamp: new Date().toISOString(),
              tag: 'REAL'
          });
      }
      set({ isConnected: false, ws: null });
    };
    
    socket.onerror = () => {
    };
  },
  sendMessage: (msg: string) => {
    get().addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: msg,
      timestamp: new Date().toISOString()
    });

    const { ws, isConnected } = get();
    if (ws && isConnected) {
      ws.send(JSON.stringify({ action: 'chat', message: msg }));
    } else {
        get().addMessage({
            id: (Date.now() + 1).toString(),
            role: 'system',
            content: 'ОШИБКА: Нет подключения к локальному Backend. Задача не отправлена.',
            timestamp: new Date().toISOString(),
            tag: 'REAL'
        });
    }
  },
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setRecording: (status) => set({ isRecording: status }),
  updateTasks: (tasks) => set({ tasks }),
}));
