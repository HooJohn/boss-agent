"use client";

import { motion } from "framer-motion";
import { Check, CircleStop, Pencil } from "lucide-react";

import Action from "@/components/action";
import Markdown from "@/components/markdown";
import QuestionInput from "@/components/question-input";
import { ActionStep, Message } from "@/typings/agent";
import { Button } from "./ui/button";
import EditQuestion from "./edit-question";
import { useAppContext } from "@/context/app-context";

interface ChatMessageProps {
  isReplayMode: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  handleClickAction: (
    data: ActionStep | undefined,
    showTabOnly?: boolean
  ) => void;
  setCurrentQuestion: (value: string) => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  handleQuestionSubmit: (question: string, searchMode: string, fileTypeFilter?: string[], pathFilter?: string) => void;
  handleEnhancePrompt: () => void;
  handleCancel: () => void;
  handleEditMessage: (newQuestion: string) => void;
}

const ChatMessage = ({
  messagesEndRef,
  isReplayMode,
  handleClickAction,
  setCurrentQuestion,
  handleKeyDown,
  handleQuestionSubmit,
  handleEnhancePrompt,
  handleCancel,
  handleEditMessage,
}: ChatMessageProps) => {
  const { state, dispatch } = useAppContext();

  const isLatestUserMessage = (
    message: Message,
    allMessages: Message[]
  ): boolean => {
    const userMessages = allMessages.filter((msg) => msg.role === "user");
    return (
      userMessages.length > 0 &&
      userMessages[userMessages.length - 1].id === message.id
    );
  };

  const handleSetEditingMessage = (message?: Message) => {
    dispatch({ type: "SET_EDITING_MESSAGE", payload: message });
  };

  return (
    <div className="col-span-4 flex flex-col h-full">
      <motion.div
        className="p-4 pt-0 w-full flex-grow overflow-y-auto relative"
        initial={{ opacity: 0 }}
        style={{ height: 'calc(100% - 80px)' }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.3 }}
      >
        {state.messages.map((message, index) => (
          <motion.div
            key={`${message.id}-${index}`}
            className={`mb-4 ${
              message.role === "user" ? "text-right" : "text-left"
            } ${message.role === "user" && !message.files && "mb-8"}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index, duration: 0.3 }}
          >
            {message.content && (
              <motion.div
                className={`inline-block text-left rounded-lg ${
                  message.role === "user"
                    ? "bg-[#35363a] p-3 max-w-[80%] text-white border border-[#3A3B3F] shadow-sm whitespace-pre-wrap"
                    : "text-white"
                } ${
                  state.editingMessage?.id === message.id
                    ? "w-full max-w-none"
                    : ""
                }`}
                initial={{ scale: 0.9 }}
                animate={{ scale: 1 }}
                transition={{
                  type: "spring",
                  stiffness: 500,
                  damping: 30,
                }}
              >
                {message.role === "user" ? (
                  <div>
                    {state.editingMessage?.id === message.id ? (
                      <EditQuestion
                        editingMessage={message.content}
                        handleCancel={() => handleSetEditingMessage(undefined)}
                        handleEditMessage={handleEditMessage}
                      />
                    ) : (
                      <div className="relative group">
                        <div className="text-left">{message.content}</div>
                        {isLatestUserMessage(message, state.messages) &&
                          !isReplayMode && (
                            <div className="absolute -bottom-[45px] -right-[20px] opacity-0 group-hover:opacity-100 transition-opacity">
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-xs cursor-pointer hover:!bg-transparent"
                                onClick={() => {
                                  handleSetEditingMessage(message);
                                }}
                              >
                                <Pencil className="size-3 mr-1" />
                              </Button>
                            </div>
                          )}
                      </div>
                    )}
                  </div>
                ) : (
                  <Markdown>{message.content}</Markdown>
                )}
              </motion.div>
            )}

            {message.action && (
              <motion.div
                className="mt-2"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index, duration: 0.3 }}
              >
                <Action
                  workspaceInfo={state.workspaceInfo}
                  type={message.action.type}
                  value={message.action.data}
                  onClick={() => handleClickAction(message.action, true)}
                />
              </motion.div>
            )}
          </motion.div>
        ))}

        {state.isLoading && (
          <motion.div
            className="mb-4 text-left"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 30,
            }}
          >
            <motion.div
              className="inline-block p-3 text-left rounded-lg bg-neutral-800/90 text-white backdrop-blur-sm"
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              transition={{
                type: "spring",
                stiffness: 400,
                damping: 25,
              }}
            >
              <div className="flex items-center gap-3">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-white rounded-full animate-[dot-bounce_1.2s_ease-in-out_infinite_0ms]" />
                  <div className="w-2 h-2 bg-white rounded-full animate-[dot-bounce_1.2s_ease-in-out_infinite_200ms]" />
                  <div className="w-2 h-2 bg-white rounded-full animate-[dot-bounce_1.2s_ease-in-out_infinite_400ms]" />
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}

        {state.isCompleted && (
          <div className="flex gap-x-2 items-center bg-[#25BA3B1E] text-green-600 text-sm p-2 rounded-full">
            <Check className="size-4" />
            <span>任务已完成。</span>
          </div>
        )}

        {state.isStopped && (
          <div className="flex gap-x-2 items-center bg-[#ffbf361f] text-yellow-300 text-sm p-2 rounded-full">
            <CircleStop className="size-4" />
            <span>任务已停止，发送新消息以继续。</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </motion.div>
      <motion.div
        className="mt-auto"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.3 }}
      >
        <QuestionInput
          hideSettings
          className="p-4 pb-0 w-full max-w-none"
          textareaClassName="h-30 w-full"
          placeholder="请输入您的问题或指令..."
          value={state.currentQuestion}
          setValue={setCurrentQuestion}
          handleKeyDown={handleKeyDown}
          handleSubmit={(question, searchMode) => handleQuestionSubmit(question, searchMode)}
          handleEnhancePrompt={handleEnhancePrompt}
          handleCancel={handleCancel}
        />
      </motion.div>
    </div>
  );
};

export default ChatMessage;
