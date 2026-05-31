import { useState, useEffect, useRef } from "react";
import { Mic, Send, StopCircle, Eye, ShieldAlert, Wifi, WifiOff } from "lucide-react";
import { useStore } from "../store/useStore";
import { motion } from "motion/react";
import { TaskTracker } from "./TaskTracker";

export function Chat() {
  const [input, setInput] = useState("");
  const { messages, sendMessage, isRecording, setRecording, isConnected, addMessage, ws } = useStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleVoiceToggle = async () => {
      if (isRecording) {
          mediaRecorderRef.current?.stop();
          audioStreamRef.current?.getTracks().forEach(track => track.stop());
          setRecording(false);
          audioStreamRef.current = null;
          addMessage({
              id: Date.now().toString(),
              role: 'system',
              content: 'Аудио захват завершен. Кодирование...',
              timestamp: new Date().toISOString(),
              tag: 'REAL'
          });
      } else {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioStreamRef.current = stream;
            const recorder = new MediaRecorder(stream);
            const chunks: BlobPart[] = [];
            
            recorder.ondataavailable = (e) => chunks.push(e.data);
            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: 'audio/webm' });
                const reader = new FileReader();
                reader.readAsDataURL(blob);
                reader.onloadend = () => {
                    const base64data = reader.result as string;
                    if (ws && isConnected) {
                        ws.send(JSON.stringify({
                            action: 'audio',
                            data: base64data
                        }));
                    } else {
                        addMessage({
                            id: Date.now().toString() + "_err",
                            role: "system",
                            content: "Ошибка: Нет связи с сервером для передачи аудиофайла.",
                            timestamp: new Date().toISOString(),
                            tag: 'REAL'
                        });
                    }
                }
            };
            
            recorder.start();
            mediaRecorderRef.current = recorder;
            setRecording(true);
            addMessage({
                id: Date.now().toString(),
                role: 'system',
                content: 'Микрофон активирован. Аудио поток записывается...',
                timestamp: new Date().toISOString(),
                tag: 'REAL'
            });
        } catch (e) {
            addMessage({
                id: Date.now().toString() + "_err",
                role: "system",
                content: "Ошибка доступа к микрофону: " + (e as Error).message,
                timestamp: new Date().toISOString(),
                tag: 'REAL'
            });
            console.error("Mic error", e);
        }
      }
  };

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <div className="flex-1 flex flex-col h-screen relative bg-[#09090b]">
        {/* Top Status Bar */}
        <div className="h-12 border-b border-white/5 flex items-center justify-center desktop-drag">
           <div className="flex items-center gap-2 text-xs text-white/40 font-mono">
               {isConnected ? (
                   <span className="flex items-center gap-1 text-emerald-400">
                       <Wifi className="w-3 h-3" /> Backend Connected
                   </span>
               ) : (
                   <span className="flex items-center gap-1 text-red-400">
                       <WifiOff className="w-3 h-3" /> Backend Offline
                   </span>
               )}
               <span className="mx-2">•</span>
               <Eye className="w-3 h-3 text-indigo-400" />
               <span className="text-indigo-400">Vision: STANDBY</span>
           </div>
        </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-6 scroll-smooth">
        <div className="max-w-3xl mx-auto flex flex-col gap-6">
          {messages.map((msg) => (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={msg.id}
              className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
            >
              {msg.role === "system" ? (
                  <div className="flex items-center justify-center gap-2 w-full my-2">
                       {msg.tag && (
                            <span className={`text-[8px] font-mono px-1 py-0.5 rounded border uppercase
                                ${msg.tag === 'REAL' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' : 
                                msg.tag === 'MOCK' ? 'border-yellow-500/30 text-yellow-400 bg-yellow-500/10' : 
                                'border-red-500/30 text-red-400 bg-red-500/10'}`}
                            >
                                {msg.tag}
                            </span>
                        )}
                      <div className="text-xs text-white/30 font-mono text-center">
                          {msg.content}
                      </div>
                  </div>
              ) : (
                <div
                    className={`max-w-[80%] rounded-2xl px-5 py-3 ${
                    msg.role === "user"
                        ? "bg-white text-black rounded-br-sm"
                        : "bg-white/10 text-white rounded-bl-sm border border-white/5 backdrop-blur-sm"
                    }`}
                >
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                </div>
              )}
            </motion.div>
          ))}
          
          <div className="w-full">
              <TaskTracker />
          </div>

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 mx-auto w-full max-w-3xl relative">
        <div className="relative bg-white/5 border border-white/10 rounded-2xl p-2 flex items-end gap-2 backdrop-blur-xl shadow-2xl transition-all focus-within:border-white/20">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={isConnected ? "Введите команду..." : "Сервер недоступен (Socket Error)"}
            className="flex-1 bg-transparent text-white p-2 max-h-32 min-h-[44px] resize-none focus:outline-none placeholder:text-white/30 text-sm disabled:opacity-50"
            disabled={!isConnected}
            rows={1}
          />
          
          <div className="flex items-center gap-2 pb-1 pr-1">
            <button
              onClick={handleVoiceToggle}
              className={`p-2.5 rounded-xl transition-all duration-300 ${
                isRecording 
                  ? "bg-red-500/20 text-red-500 hover:bg-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.5)]" 
                  : "text-white/50 hover:text-white hover:bg-white/10"
              }`}
              title="Запись с микрофона (REAL)"
            >
              {isRecording ? (
                  <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ repeat: Infinity }}>
                      <StopCircle className="w-5 h-5" />
                  </motion.div>
              ) : (
                  <Mic className="w-5 h-5" />
              )}
            </button>
            <button
              onClick={handleSend}
              disabled={!input.trim() || !isConnected}
              className="p-2.5 rounded-xl bg-white text-black hover:bg-white/90 disabled:opacity-50 disabled:hover:bg-white transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
        <div className="text-center mt-3 text-[10px] text-white/30 font-mono">
          STRICT EXECUTION POLICY ENABLED. ALL ACTIONS ARE REAL UNLESS MARKED OTHERWISE.
        </div>
      </div>
    </div>
  );
}
