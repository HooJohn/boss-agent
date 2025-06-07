"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { History, X, PlusCircle } from "lucide-react";

import { useDeviceId } from "@/hooks/use-device-id";
import { useAppContext } from "@/context/app-context";
import { Button } from "./ui/button";

interface HistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Session {
  id: string;
  first_message: string;
  created_at: string;
}

export default function HistoryDrawer({ isOpen, onClose }: HistoryDrawerProps) {
  const { deviceId } = useDeviceId();
  const { dispatch } = useAppContext();
  const router = useRouter();
  const [sessions, setSessions] = useState<Session[]>([]);

  const handleNewChat = () => {
    dispatch({ type: "SET_MESSAGES", payload: [] });
    dispatch({ type: "SET_CURRENT_ACTION_DATA", payload: undefined });
    dispatch({ type: "SET_COMPLETED", payload: false });
    dispatch({ type: "SET_STOPPED", payload: false });
    dispatch({ type: "SET_LOADING", payload: false });
    router.push("/");
    onClose();
  };

  useEffect(() => {
    if (isOpen && deviceId) {
      fetch(`/api/sessions/${deviceId}`)
        .then((res) => res.json())
        .then((data) => {
          setSessions(data.sessions || []);
        });
    }
  }, [isOpen, deviceId]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("zh-CN", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ x: "-100%" }}
          animate={{ x: 0 }}
          exit={{ x: "-100%" }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="fixed top-0 left-0 h-full w-80 bg-[#1e1f23] border-r border-[#3A3B3F] z-50 flex flex-col"
        >
          <div className="flex items-center justify-between p-4 border-b border-[#3A3B3F]">
            <div className="flex items-center gap-2">
              <History className="h-6 w-6 text-gray-300" />
              <h2 className="text-lg font-semibold text-white">对话历史</h2>
            </div>
            <div className="flex items-center">
              <Button variant="ghost" size="icon" onClick={handleNewChat}>
                <PlusCircle className="h-5 w-5 text-gray-400" />
              </Button>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-5 w-5 text-gray-400" />
              </Button>
            </div>
          </div>
          <div className="flex-grow overflow-y-auto p-2">
            {sessions.length > 0 ? (
              <ul>
                {sessions.map((session) => (
                  <li key={session.id} className="mb-2">
                    <Link
                      href={`/?session_id=${session.id}`}
                      onClick={onClose}
                      className="block p-3 rounded-lg hover:bg-[#2a2b30] transition-colors"
                    >
                      <p className="text-sm font-medium text-gray-100 truncate">
                        {session.first_message || "无标题对话"}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {formatDate(session.created_at)}
                      </p>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-center text-gray-500 mt-8">没有历史记录</p>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
