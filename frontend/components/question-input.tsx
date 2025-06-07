import { motion } from "framer-motion";
import {
  ArrowUp,
  Loader2,
  Settings2,
  Plus,
} from "lucide-react";
import { useState, useEffect, useRef } from "react";
import Image from "next/image";

import SettingsDrawer from "./settings-drawer";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";
import { Button } from "./ui/button";
import { Textarea } from "./ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { useAppContext } from "@/context/app-context";

interface QuestionInputProps {
  hideSettings?: boolean;
  className?: string;
  textareaClassName?: string;
  placeholder?: string;
  value: string;
  setValue: (value: string) => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  handleSubmit: (question: string, searchMode: string) => void;
  isDisabled?: boolean;
  handleEnhancePrompt?: () => void;
  handleCancel?: () => void;
}

const QuestionInput = ({
  hideSettings,
  className,
  textareaClassName,
  placeholder,
  value,
  setValue,
  handleKeyDown,
  handleSubmit,
  isDisabled,
  handleEnhancePrompt,
  handleCancel,
}: QuestionInputProps) => {
  const { state } = useAppContext();
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [searchMode, setSearchMode] = useState("all");

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);

  return (
    <motion.div
      key="input-view"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -10 }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 30,
        mass: 1,
      }}
      className={`w-full max-w-2xl z-50 ${className}`}
    >
      {!hideSettings && (
        <SettingsDrawer
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
        />
      )}

      <div className="relative flex flex-col bg-[#35363a] border border-[#ffffff0f] rounded-xl shadow-[0px_0px_10px_0px_rgba(0,0,0,0.02)]">
        <Textarea
          className={`w-full p-4 pr-16 pb-[72px] rounded-xl !text-lg focus:ring-0 resize-none !placeholder-gray-400 !bg-[#35363a] border-[#ffffff0f] shadow-[0px_0px_10px_0px_rgba(0,0,0,0.02)] min-h-[120px] max-h-[300px] ${textareaClassName}`}
          placeholder={
            placeholder ||
            "输入您的问题或指令..."
          }
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          ref={textareaRef}
        />
        <div className="flex justify-between items-center p-2 border-t border-[#ffffff0f]">
          <div className="flex items-center gap-x-2">
            {!hideSettings && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="hover:bg-gray-700/50 size-10 rounded-full"
                    onClick={() => setIsSettingsOpen(true)}
                    disabled={state.isLoading}
                  >
                    <Settings2 className="size-5 text-gray-400" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>设置</TooltipContent>
              </Tooltip>
            )}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="hover:bg-gray-700/50 size-10 rounded-full"
                  onClick={handleEnhancePrompt}
                  disabled={
                    state.isGeneratingPrompt ||
                    !value.trim() ||
                    isDisabled ||
                    state.isLoading
                  }
                >
                  {state.isGeneratingPrompt ? (
                    <Loader2 className="size-5 text-gray-400 animate-spin" />
                  ) : (
                    <Image
                      src="/icons/AI.svg"
                      alt="Logo"
                      width={24}
                      height={24}
                    />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>优化指令</TooltipContent>
            </Tooltip>
          </div>

          <div className="flex items-center gap-x-2">
            <Select value={searchMode} onValueChange={setSearchMode}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="搜索模式" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">内外网都搜</SelectItem>
                <SelectItem value="internal">仅内网</SelectItem>
                <SelectItem value="external">仅外网</SelectItem>
              </SelectContent>
            </Select>
            {state.isLoading && handleCancel ? (
              <Button
                onClick={handleCancel}
                className="cursor-pointer size-10 font-bold p-0 !bg-black rounded-full hover:scale-105 active:scale-95 transition-transform"
              >
                <div className="size-3 rounded-xs bg-white" />
              </Button>
            ) : (
              <Button
                disabled={
                  !value.trim() ||
                  isDisabled ||
                  state.isLoading
                }
                onClick={() => handleSubmit(value, searchMode)}
                className="cursor-pointer !border !border-red p-4 size-10 font-bold bg-gradient-skyblue-lavender rounded-full hover:scale-105 active:scale-95 transition-transform"
              >
                <ArrowUp className="size-5" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default QuestionInput;
