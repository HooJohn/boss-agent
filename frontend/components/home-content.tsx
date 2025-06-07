"use client";

import { Terminal as XTerm } from "@xterm/xterm";
import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import {
  Globe,
  X,
  Share,
  Loader2,
  Settings2,
  ArrowDownToLine,
  History,
} from "lucide-react";
import Image from "next/image";
import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import dynamic from "next/dynamic";
import { Orbitron } from "next/font/google";
import { useSearchParams } from "next/navigation";

import { useDeviceId } from "@/hooks/use-device-id";
import { useSessionManager } from "@/hooks/use-session-manager";
import { useAppEvents } from "@/hooks/use-app-events";
import { useAppContext } from "@/context/app-context";

import SidebarButton from "@/components/sidebar-button";
import SettingsDrawer from "@/components/settings-drawer";
import HistoryDrawer from "@/components/history-drawer";
import ConnectionStatus from "@/components/connection-status";
import Browser from "@/components/browser";
import QuestionInput from "@/components/question-input";
import SearchBrowser from "@/components/search-browser";
import { Button } from "@/components/ui/button";
import ChatMessage from "@/components/chat-message";
import ImageBrowser from "@/components/image-browser";
import { Message, TAB, TOOL } from "@/typings/agent";

const orbitron = Orbitron({
  subsets: ["latin"],
});

export default function HomeContent() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const xtermRef = useRef<XTerm | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const { state, dispatch, sendMessage, handleEvent } = useAppContext();
  const { handleClickAction } = useAppEvents({ xtermRef });
  const searchParams = useSearchParams();

  const { deviceId } = useDeviceId();

  const { sessionId, isLoadingSession, isReplayMode, setSessionId } =
    useSessionManager({
      searchParams,
      handleEvent,
    });

  const { socket } = state;

  useEffect(() => {
    if (state.currentActionData) {
      handleClickAction(state.currentActionData);
    }
  }, [state.currentActionData, handleClickAction]);

  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [state.messages, autoScroll]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const element = e.currentTarget;
    const isAtBottom = element.scrollHeight - element.scrollTop === element.clientHeight;
    setAutoScroll(isAtBottom);
  };

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
      setAutoScroll(true);
    }
  };

  const handleEnhancePrompt = () => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      toast.error("WebSocket connection is not open. Please try again.");
      return;
    }
    dispatch({ type: "SET_GENERATING_PROMPT", payload: true });
    sendMessage({
      type: "enhance_prompt",
      content: {
        model_name: state.selectedModel,
        text: state.currentQuestion,
        files: state.uploadedFiles?.map((file) => `.${file}`),
        tool_args: {
          thinking_tokens: 0,
        },
      },
    });
  };

  const handleQuestionSubmit = async (newQuestion: string, searchMode: string, fileTypeFilter?: string[], pathFilter?: string) => {
    if (!newQuestion.trim() || state.isLoading) return;

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      toast.error("WebSocket connection is not open. Please try again.");
      dispatch({ type: "SET_LOADING", payload: false });
      return;
    }

    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_CURRENT_QUESTION", payload: "" });
    dispatch({ type: "SET_COMPLETED", payload: false });
    dispatch({ type: "SET_STOPPED", payload: false });

    if (!sessionId) {
      const id = `${state.workspaceInfo}`.split("/").pop();
      if (id) {
        setSessionId(id);
      }
    }

    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: newQuestion,
      timestamp: Date.now(),
    };

    dispatch({
      type: "ADD_MESSAGE",
      payload: newUserMessage,
    });

    if (!sessionId) {
      sendMessage({
        type: "init_agent",
        content: {
          model_name: state.selectedModel,
          tool_args: state.toolSettings,
        },
      });
    }

    sendMessage({
      type: "query",
      content: {
        text: newQuestion,
        resume: state.messages.length > 0,
        files: state.uploadedFiles?.map((file) => `.${file}`),
        search_mode: searchMode,
        file_type_filter: fileTypeFilter,
        path_filter: pathFilter,
      },
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleQuestionSubmit((e.target as HTMLTextAreaElement).value, "all");
    }
  };

  const parseJson = (jsonString: string) => {
    try {
      return JSON.parse(jsonString);
    } catch {
      return null;
    }
  };

  const handleEditMessage = (newQuestion: string) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      toast.error("WebSocket connection is not open. Please try again.");
      dispatch({ type: "SET_LOADING", payload: false });
      return;
    }

    socket.send(
      JSON.stringify({
        type: "edit_query",
        content: {
          text: newQuestion,
          files: state.uploadedFiles?.map((file) => `.${file}`),
        },
      })
    );

    const editIndex = state.messages.findIndex(
      (m) => m.id === state.editingMessage?.id
    );

    if (editIndex >= 0) {
      const updatedMessages = [...state.messages.slice(0, editIndex + 1)];
      updatedMessages[editIndex] = {
        ...updatedMessages[editIndex],
        content: newQuestion,
      };

      dispatch({
        type: "SET_MESSAGES",
        payload: updatedMessages,
      });
    }

    dispatch({ type: "SET_COMPLETED", payload: false });
    dispatch({ type: "SET_STOPPED", payload: false });
    dispatch({ type: "SET_LOADING", payload: true });
    dispatch({ type: "SET_EDITING_MESSAGE", payload: undefined });
  };

  const getRemoteURL = (path: string | undefined) => {
    if (!path || !state.workspaceInfo) return "";
    const workspaceId = state.workspaceInfo.split("/").pop();
    return `${process.env.NEXT_PUBLIC_API_URL}/workspace/${workspaceId}/${path}`;
  };

  const handleCancelQuery = () => {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      toast.error("WebSocket connection is not open.");
      return;
    }

    socket.send(
      JSON.stringify({
        type: "cancel",
        content: {},
      })
    );
    dispatch({ type: "SET_LOADING", payload: false });
    dispatch({ type: "SET_STOPPED", payload: true });
  };

  const isBrowserTool = useMemo(
    () =>
      [
        TOOL.BROWSER_VIEW,
        TOOL.BROWSER_CLICK,
        TOOL.BROWSER_ENTER_TEXT,
        TOOL.BROWSER_PRESS_KEY,
        TOOL.BROWSER_GET_SELECT_OPTIONS,
        TOOL.BROWSER_SELECT_DROPDOWN_OPTION,
        TOOL.BROWSER_SWITCH_TAB,
        TOOL.BROWSER_OPEN_NEW_TAB,
        TOOL.BROWSER_WAIT,
        TOOL.BROWSER_SCROLL_DOWN,
        TOOL.BROWSER_SCROLL_UP,
        TOOL.BROWSER_NAVIGATION,
        TOOL.BROWSER_RESTART,
      ].includes(state.currentActionData?.type as TOOL),
    [state.currentActionData]
  );

  return (
    <div className="flex flex-col h-full w-full flex-grow">
      <SettingsDrawer
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
      <HistoryDrawer
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
      />
      {isLoadingSession ? (
        <div className="flex flex-col items-center justify-center p-8">
          <Loader2 className="h-8 w-8 text-white animate-spin mb-4" />
          <p className="text-white text-lg">正在加载...</p>
        </div>
      ) : (
        <div className="w-full grid grid-cols-12 gap-4 flex-1 h-full overflow-hidden">
          <div 
            className="col-span-9 bg-[#1e1f23] border border-[#3A3B3F] rounded-2xl flex flex-col"
          >
            <div className="flex justify-between items-center mb-4">
              <Button variant="ghost" size="icon" onClick={() => setIsHistoryOpen(true)}>
                <History className="h-5 w-5 text-gray-400" />
              </Button>
              <Button variant="ghost" size="icon" onClick={() => setIsSettingsOpen(true)}>
                <Settings2 className="h-5 w-5 text-gray-400" />
              </Button>
            </div>
            <div 
              className="flex-grow overflow-y-auto"
              onScroll={handleScroll}
              ref={chatContainerRef}
            >
              <ChatMessage
                key={sessionId}
                handleClickAction={handleClickAction}
                isReplayMode={isReplayMode}
                messagesEndRef={messagesEndRef}
                setCurrentQuestion={(value) =>
                  dispatch({ type: "SET_CURRENT_QUESTION", payload: value })
                }
                handleKeyDown={handleKeyDown}
                handleQuestionSubmit={handleQuestionSubmit}
                handleEnhancePrompt={handleEnhancePrompt}
                handleCancel={handleCancelQuery}
                handleEditMessage={handleEditMessage}
              />
            </div>
            {!autoScroll && (
              <div className="sticky bottom-4 flex justify-center mt-2">
                <Button 
                  variant="outline" 
                  className="flex items-center gap-2 bg-[#2a2b30] hover:bg-[#3a3b40]"
                  onClick={scrollToBottom}
                >
                  <ArrowDownToLine className="h-4 w-4" />
                  回到最新消息
                </Button>
              </div>
            )}
          </div>
          
          <div className="col-span-3 bg-[#1e1f23] border border-[#3A3B3F] p-4 rounded-2xl flex flex-col">
            <div className="pb-4 bg-neutral-850 flex items-center justify-between">
              <div className="flex gap-x-4">
                <Button
                  className={`cursor-pointer hover:!bg-black ${
                    state.activeTab === TAB.BROWSER
                      ? "bg-gradient-skyblue-lavender !text-black"
                      : ""
                  }`}
                  variant="outline"
                  onClick={() =>
                    dispatch({
                      type: "SET_ACTIVE_TAB",
                      payload: TAB.BROWSER,
                    })
                  }
                >
                  <Globe className="size-4" /> 浏览器
                </Button>
              </div>
              <ConnectionStatus />
            </div>
            <div className="flex-grow overflow-y-auto">
              <Browser
                className={
                  state.currentActionData?.type === TOOL.VISIT || isBrowserTool
                    ? ""
                    : "hidden"
                }
                url={
                  state.currentActionData?.data?.tool_input?.url ||
                  state.browserUrl
                }
                screenshot={
                  isBrowserTool
                    ? (state.currentActionData?.data.result as string)
                    : undefined
                }
                raw={
                  state.currentActionData?.type === TOOL.VISIT
                    ? (state.currentActionData?.data?.result as string)
                    : undefined
                }
              />
              <SearchBrowser
                className={
                  state.currentActionData?.type === TOOL.WEB_SEARCH
                    ? ""
                    : "hidden"
                }
                keyword={state.currentActionData?.data.tool_input?.query}
                search_results={
                  state.currentActionData?.type === TOOL.WEB_SEARCH &&
                  state.currentActionData?.data?.result
                    ? parseJson(
                        state.currentActionData?.data?.result as string
                      )
                    : undefined
                }
              />
              <ImageBrowser
                className={
                  state.currentActionData?.type === TOOL.IMAGE_GENERATE ||
                  state.currentActionData?.type === TOOL.IMAGE_SEARCH
                    ? ""
                    : "hidden"
                }
                url={
                  state.currentActionData?.data.tool_input
                    ?.output_filename ||
                  state.currentActionData?.data.tool_input?.query
                }
                images={
                  state.currentActionData?.type === TOOL.IMAGE_SEARCH
                    ? parseJson(
                        state.currentActionData?.data?.result as string
                      )?.map(
                        (item: { image_url: string }) => item?.image_url
                      )
                    : [
                        getRemoteURL(
                          state.currentActionData?.data.tool_input
                            ?.output_filename
                        ),
                      ]
                }
              />
              {!state.currentActionData && (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <p>浏览器视图</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
