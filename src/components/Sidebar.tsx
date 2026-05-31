import { LayoutGrid, MessageSquare, Settings, Activity } from "lucide-react";

export function Sidebar() {
  return (
    <aside className="w-64 bg-black/40 backdrop-blur-md border-r border-white/10 flex flex-col pt-8 pb-4 shrink-0">
      <div className="px-6 mb-8 flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <span className="text-white font-medium tracking-wide">Radmir AI</span>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        <button className="w-full flex items-center gap-3 px-3 py-2 bg-white/10 rounded-lg text-white transition-colors">
          <MessageSquare className="w-4 h-4 opacity-70" />
          <span className="text-sm font-medium">Новый чат</span>
        </button>
        <button className="w-full flex items-center gap-3 px-3 py-2 text-white/60 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
          <LayoutGrid className="w-4 h-4 opacity-70" />
          <span className="text-sm font-medium">Задачи</span>
        </button>
      </nav>

      <div className="px-3 mt-auto">
        <button className="w-full flex items-center gap-3 px-3 py-2 text-white/60 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
          <Settings className="w-4 h-4 opacity-70" />
          <span className="text-sm font-medium">Настройки</span>
        </button>
      </div>
    </aside>
  );
}
