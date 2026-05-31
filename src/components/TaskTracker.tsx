import { CheckCircle2, Circle, Clock, AlertCircle } from "lucide-react";
import { useStore } from "../store/useStore";
import { motion, AnimatePresence } from "motion/react";

export function TaskTracker() {
  const tasks = useStore((state) => state.tasks);

  if (tasks.length === 0) return null;

  return (
    <div className="bg-black/20 rounded-xl border border-white/5 p-4 mb-6 backdrop-blur-sm">
      <h3 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-4">
        План выполнения
      </h3>
      <div className="space-y-3">
        <AnimatePresence>
          {tasks.map((task) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start gap-3"
            >
              <div className="mt-0.5 shrink-0">
                {task.status === "completed" && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                {task.status === "in-progress" && (
                  <motion.div 
                    animate={{ rotate: 360 }} 
                    transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  >
                    <Clock className="w-4 h-4 text-indigo-400" />
                  </motion.div>
                )}
                {task.status === "pending" && <Circle className="w-4 h-4 text-white/20" />}
                {task.status === "failed" && <AlertCircle className="w-4 h-4 text-red-400" />}
              </div>
              <div className={`text-sm flex-1 ${task.status === "completed" ? "text-white/60 line-through" : "text-white/90"}`}>
                {task.title}
              </div>
              <div className="shrink-0">
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border 
                    ${task.tag === 'REAL' ? 'border-emerald-500/30 text-emerald-400 bg-emerald-500/10' : 
                      task.tag === 'MOCK' ? 'border-yellow-500/30 text-yellow-400 bg-yellow-500/10' : 
                      'border-red-500/30 text-red-400 bg-red-500/10'}`}
                  >
                      {task.tag}
                  </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
