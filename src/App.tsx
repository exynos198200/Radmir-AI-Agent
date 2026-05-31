import { useEffect } from "react";
import { Sidebar } from "./components/Sidebar";
import { Chat } from "./components/Chat";
import { useStore } from "./store/useStore";

export default function App() {
  const connect = useStore((state) => state.connect);

  useEffect(() => {
    connect();
  }, [connect]);

  return (
    <div className="flex h-screen bg-[#000000] text-white overflow-hidden font-sans selection:bg-indigo-500/30">
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-purple-500/5 pointer-events-none" />
      <Sidebar />
      <Chat />
    </div>
  );
}
