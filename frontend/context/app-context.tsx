"use client";

import { createContext, useContext, useReducer, ReactNode } from "react";
import {
  ActionStep,
  AgentEvent,
  AVAILABLE_MODELS,
  Message,
  TAB,
  TOOL,
  ToolSettings,
  WebSocketConnectionState,
} from "@/typings/agent";

// Define the state interface
interface AppState {
  messages: Message[];
  isLoading: boolean;
  activeTab: TAB;
  currentActionData?: ActionStep;
  activeFileCodeEditor: string;
  currentQuestion: string;
  isCompleted: boolean;
  isStopped: boolean;
  workspaceInfo: string;
  isUploading: boolean;
  uploadedFiles: string[];
  filesContent: { [key: string]: string };
  browserUrl: string;
  isGeneratingPrompt: boolean;
  editingMessage?: Message;
  toolSettings: ToolSettings;
  selectedModel?: string;
  wsConnectionState: WebSocketConnectionState;
  socket: WebSocket | null;
  sendMessage: (payload: { type: string; content: any }) => void;
  agent?: any;
  currentModel?: string;
}

// Define action types
type AppAction =
  | { type: "SET_MESSAGES"; payload: Message[] }
  | { type: "ADD_MESSAGE"; payload: Message }
  | { type: "UPDATE_MESSAGE"; payload: Message }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ACTIVE_TAB"; payload: TAB }
  | { type: "SET_CURRENT_ACTION_DATA"; payload: ActionStep | undefined }
  | { type: "SET_ACTIVE_FILE"; payload: string }
  | { type: "SET_CURRENT_QUESTION"; payload: string }
  | { type: "SET_COMPLETED"; payload: boolean }
  | { type: "SET_STOPPED"; payload: boolean }
  | { type: "SET_WORKSPACE_INFO"; payload: string }
  | { type: "SET_IS_UPLOADING"; payload: boolean }
  | { type: "SET_UPLOADED_FILES"; payload: string[] }
  | { type: "ADD_UPLOADED_FILES"; payload: string[] }
  | { type: "SET_FILES_CONTENT"; payload: { [key: string]: string } }
  | { type: "ADD_FILE_CONTENT"; payload: { path: string; content: string } }
  | { type: "SET_BROWSER_URL"; payload: string }
  | { type: "SET_GENERATING_PROMPT"; payload: boolean }
  | { type: "SET_EDITING_MESSAGE"; payload: Message | undefined }
  | { type: "SET_TOOL_SETTINGS"; payload: AppState["toolSettings"] }
  | { type: "SET_SELECTED_MODEL"; payload: string | undefined }
  | { type: "SET_WS_CONNECTION_STATE"; payload: WebSocketConnectionState }
  | { type: "SET_AGENT"; payload: any }
  | {
      type: "HANDLE_EVENT";
      payload: {
        event: AgentEvent;
        data: Record<string, unknown>;
        workspacePath?: string;
      };
    };

// Initial state
const initialState: AppState = {
  messages: [],
  isLoading: false,
  activeTab: TAB.BROWSER,
  activeFileCodeEditor: "",
  currentQuestion: "",
  isCompleted: false,
  isStopped: false,
  workspaceInfo: "",
  isUploading: false,
  uploadedFiles: [],
  filesContent: {},
  browserUrl: "",
  isGeneratingPrompt: false,
  toolSettings: {
    deep_research: false,
    pdf: true,
    browser: true,
    thinking_tokens: 10000,
  },
  wsConnectionState: WebSocketConnectionState.CONNECTING,
  selectedModel: AVAILABLE_MODELS[0],
  socket: null,
  sendMessage: () => {},
  agent: null,
  currentModel: AVAILABLE_MODELS[0],
};

// Create the context
const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  sendMessage: (payload: { type: string; content: any }) => void;
  handleEvent: (
    data: {
      id: string;
      type: AgentEvent;
      content: Record<string, unknown>;
    },
    workspacePath?: string
  ) => void;
}>({
  state: initialState,
  dispatch: () => null,
  sendMessage: () => {},
  handleEvent: () => {},
});

// Reducer function
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case "SET_MESSAGES":
      return { ...state, messages: action.payload };
    case "ADD_MESSAGE":
      return { ...state, messages: [...state.messages, action.payload] };
    case "UPDATE_MESSAGE":
      const newMessages = state.messages.map((message) =>
        message.id === action.payload.id ? action.payload : message
      );
      // Find the message that holds the current action data
      const currentActionMessage = state.messages.find(
        (msg) => msg.action === state.currentActionData
      );
      // Check if the message being updated is the one that contains the current action
      const shouldUpdateAction = currentActionMessage?.id === action.payload.id;
      return {
        ...state,
        messages: newMessages,
        currentActionData: shouldUpdateAction
          ? action.payload.action
          : state.currentActionData,
      };
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    case "SET_ACTIVE_TAB":
      return { ...state, activeTab: action.payload };
    case "SET_CURRENT_ACTION_DATA":
      return { ...state, currentActionData: action.payload };
    case "SET_ACTIVE_FILE":
      return { ...state, activeFileCodeEditor: action.payload };
    case "SET_CURRENT_QUESTION":
      return { ...state, currentQuestion: action.payload };
    case "SET_COMPLETED":
      return { ...state, isCompleted: action.payload };
    case "SET_STOPPED":
      return { ...state, isStopped: action.payload };
    case "SET_WORKSPACE_INFO":
      return { ...state, workspaceInfo: action.payload };
    case "SET_IS_UPLOADING":
      return { ...state, isUploading: action.payload };
    case "SET_UPLOADED_FILES":
      return { ...state, uploadedFiles: action.payload };
    case "ADD_UPLOADED_FILES":
      return {
        ...state,
        uploadedFiles: [...state.uploadedFiles, ...action.payload],
      };
    case "SET_FILES_CONTENT":
      return { ...state, filesContent: action.payload };
    case "ADD_FILE_CONTENT":
      return {
        ...state,
        filesContent: {
          ...state.filesContent,
          [action.payload.path]: action.payload.content,
        },
      };
    case "SET_BROWSER_URL":
      return { ...state, browserUrl: action.payload };
    case "SET_GENERATING_PROMPT":
      return { ...state, isGeneratingPrompt: action.payload };
    case "SET_EDITING_MESSAGE":
      return { ...state, editingMessage: action.payload };
    case "SET_TOOL_SETTINGS":
      return { ...state, toolSettings: action.payload };
    case "SET_SELECTED_MODEL":
      return { ...state, selectedModel: action.payload };
    case "SET_WS_CONNECTION_STATE":
      return { ...state, wsConnectionState: action.payload };
    case "SET_AGENT":
      return { ...state, agent: action.payload };
    default:
      return state;
  }
}

import { useWebSocket } from "@/hooks/use-websocket";
import { useDeviceId } from "@/hooks/use-device-id";
import { cloneDeep } from "lodash";
import { toast } from "sonner";

// Context provider component
export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  const { deviceId } = useDeviceId();

  const handleEvent = (
    data: {
      id: string;
      type: AgentEvent;
      content: Record<string, unknown>;
    },
    workspacePath?: string
  ) => {
    switch (data.type) {
      case AgentEvent.USER_MESSAGE:
        dispatch({
          type: "ADD_MESSAGE",
          payload: {
            id: data.id,
            role: "user",
            content: data.content.text as string,
            timestamp: Date.now(),
          },
        });
        break;

      case AgentEvent.PROMPT_GENERATED:
        dispatch({ type: "SET_GENERATING_PROMPT", payload: false });
        dispatch({
          type: "SET_CURRENT_QUESTION",
          payload: data.content.result as string,
        });
        break;

      case AgentEvent.PROCESSING:
        dispatch({ type: "SET_LOADING", payload: true });
        break;

      case AgentEvent.WORKSPACE_INFO:
        dispatch({
          type: "SET_WORKSPACE_INFO",
          payload: data.content.path as string,
        });
        break;

      case AgentEvent.AGENT_THINKING:
        dispatch({
          type: "ADD_MESSAGE",
          payload: {
            id: data.id,
            role: "assistant",
            content: data.content.text as string,
            timestamp: Date.now(),
          },
        });
        break;

      case AgentEvent.TOOL_CALL:
        if (data.content.tool_name === TOOL.SEQUENTIAL_THINKING) {
          dispatch({
            type: "ADD_MESSAGE",
            payload: {
              id: data.id,
              role: "assistant",
              content: (data.content.tool_input as { thought: string })
                .thought as string,
              timestamp: Date.now(),
            },
          });
        } else if (data.content.tool_name === TOOL.MESSAGE_USER) {
          dispatch({
            type: "ADD_MESSAGE",
            payload: {
              id: data.id,
              role: "assistant",
              content: (data.content.tool_input as { text: string })
                .text as string,
              timestamp: Date.now(),
            },
          });
        } else {
          const message: Message = {
            id: data.id,
            role: "assistant",
            action: {
              type: data.content.tool_name as TOOL,
              data: data.content,
            },
            timestamp: Date.now(),
          };
          const url = (data.content.tool_input as { url: string })
            ?.url as string;
          if (url) {
            dispatch({ type: "SET_BROWSER_URL", payload: url });
          }
          dispatch({ type: "ADD_MESSAGE", payload: message });
          dispatch({
            type: "SET_CURRENT_ACTION_DATA",
            payload: message.action,
          });
        }
        break;

      case AgentEvent.FILE_EDIT:
        // const messages = [...state.messages];
        // const lastMessage = cloneDeep(messages[messages.length - 1]);
        // NOTE: This logic is commented out because `str_replace_editor` does not exist in the TOOL enum
        // and causes a type error. This needs further investigation to determine the correct tool name.
        // if (
        //   lastMessage?.action &&
        //   lastMessage.action.type === "str_replace_editor"
        // ) {
        //   lastMessage.action.data.content = data.content.content as string;
        //   lastMessage.action.data.path = data.content.path as string;
        //   const workspace = workspacePath || state.workspaceInfo;
        //   const filePath = (data.content.path as string)?.includes(workspace)
        //     ? (data.content.path as string)
        //     : `${workspace}/${data.content.path}`;
        //   dispatch({
        //     type: "ADD_FILE_CONTENT",
        //     payload: {
        //       path: filePath,
        //       content: data.content.content as string,
        //     },
        //   });
        //   dispatch({
        //     type: "UPDATE_MESSAGE",
        //     payload: lastMessage,
        //   });
        // }
        break;

      case AgentEvent.BROWSER_USE:
        // Commented out in original code
        break;

      case AgentEvent.TOOL_RESULT:
        if (data.content.tool_name === TOOL.BROWSER_USE) {
          dispatch({
            type: "ADD_MESSAGE",
            payload: {
              id: data.id,
              role: "assistant",
              content: data.content.result as string,
              timestamp: Date.now(),
            },
          });
        } else {
          if (
            data.content.tool_name !== TOOL.SEQUENTIAL_THINKING &&
            data.content.tool_name !== TOOL.PRESENTATION &&
            data.content.tool_name !== TOOL.MESSAGE_USER &&
            data.content.tool_name !== TOOL.RETURN_CONTROL_TO_USER
          ) {
            const messages = [...state.messages];
            const lastMessage = cloneDeep(messages[messages.length - 1]);

            if (
              lastMessage?.action &&
              lastMessage.action?.type === data.content.tool_name
            ) {
              lastMessage.action.data.result = `${data.content.result}`;
              if (
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
                ].includes(data.content.tool_name as TOOL)
              ) {
                lastMessage.action.data.result =
                  data.content.result && Array.isArray(data.content.result)
                    ? data.content.result.find((item) => item.type === "image")
                        ?.source?.data
                    : undefined;
              }
              lastMessage.action.data.isResult = true;

              dispatch({
                type: "UPDATE_MESSAGE",
                payload: lastMessage,
              });
            } else {
              dispatch({
                type: "ADD_MESSAGE",
                payload: { ...lastMessage, action: data.content as ActionStep },
              });
            }
          }
        }
        break;

      case AgentEvent.AGENT_RESPONSE:
        dispatch({
          type: "ADD_MESSAGE",
          payload: {
            id: Date.now().toString(),
            role: "assistant",
            content: data.content.text as string,
            timestamp: Date.now(),
          },
        });
        dispatch({ type: "SET_COMPLETED", payload: true });
        dispatch({ type: "SET_LOADING", payload: false });
        break;

      case AgentEvent.UPLOAD_SUCCESS:
        dispatch({ type: "SET_IS_UPLOADING", payload: false });

        // Update the uploaded files state
        const newFiles = data.content.files as {
          path: string;
          saved_path: string;
        }[];
        const paths = newFiles.map((f) => f.path);
        dispatch({ type: "ADD_UPLOADED_FILES", payload: paths });
        break;

      case "error":
        toast.error(data.content.message as string);
        dispatch({ type: "SET_IS_UPLOADING", payload: false });
        dispatch({ type: "SET_LOADING", payload: false });
        dispatch({ type: "SET_GENERATING_PROMPT", payload: false });
        break;
    }
  };

  const { socket, sendMessage } = useWebSocket(
    deviceId,
    false,
    handleEvent,
    dispatch
  );

  const value = {
    state: { ...state, socket, sendMessage },
    dispatch,
    sendMessage,
    handleEvent,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

// Custom hook to use the context
export function useAppContext() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
}
