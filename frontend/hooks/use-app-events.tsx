"use client";

import { RefObject } from "react";
import { cloneDeep, debounce } from "lodash";
import { toast } from "sonner";

import { useAppContext } from "@/context/app-context";
import { AgentEvent, TOOL, ActionStep, Message, TAB } from "@/typings/agent";
import { Terminal as XTerm } from "@xterm/xterm";

export function useAppEvents({
  xtermRef,
}: {
  xtermRef: RefObject<XTerm | null>;
}) {
  const { state, dispatch } = useAppContext();

  const handleClickAction = debounce(
    (data: ActionStep | undefined, showTabOnly = false) => {
      if (!data) return;

      const actionType = data.type as string;

      if (
        [
          TOOL.WEB_SEARCH,
          TOOL.IMAGE_GENERATE,
          TOOL.IMAGE_SEARCH,
          TOOL.BROWSER_USE,
          TOOL.VISIT,
          TOOL.BROWSER_CLICK,
          TOOL.BROWSER_ENTER_TEXT,
          TOOL.BROWSER_PRESS_KEY,
          TOOL.BROWSER_GET_SELECT_OPTIONS,
          TOOL.BROWSER_SELECT_DROPDOWN_OPTION,
          TOOL.BROWSER_SWITCH_TAB,
          TOOL.BROWSER_OPEN_NEW_TAB,
          TOOL.BROWSER_VIEW,
          TOOL.BROWSER_NAVIGATION,
          TOOL.BROWSER_RESTART,
          TOOL.BROWSER_WAIT,
          TOOL.BROWSER_SCROLL_DOWN,
          TOOL.BROWSER_SCROLL_UP,
        ].includes(data.type)
      ) {
        dispatch({ type: "SET_ACTIVE_TAB", payload: TAB.BROWSER });
        dispatch({ type: "SET_CURRENT_ACTION_DATA", payload: data });
      } else if (actionType === "bash") {
        dispatch({ type: "SET_ACTIVE_TAB", payload: "terminal" as TAB });
        if (!showTabOnly) {
          setTimeout(() => {
            if (!data.data?.isResult) {
              // query
              xtermRef?.current?.writeln(
                `${data.data.tool_input?.command || ""}`
              );
            }
            // result
            if (data.data.result) {
              const lines = `${data.data.result || ""}`.split("\n");
              lines.forEach((line) => {
                xtermRef?.current?.writeln(line);
              });
              xtermRef?.current?.write("$ ");
            }
          }, 500);
        }
      } else if (actionType === "str_replace_editor") {
        dispatch({ type: "SET_ACTIVE_TAB", payload: "code" as TAB });
        dispatch({ type: "SET_CURRENT_ACTION_DATA", payload: data });
        const path = data.data.tool_input?.path || data.data.tool_input?.file;
        if (path) {
          dispatch({
            type: "SET_ACTIVE_FILE",
            payload: path.startsWith(state.workspaceInfo)
              ? path
              : `${state.workspaceInfo}/${path}`,
          });
        }
      }
    },
    50
  );

  return { handleClickAction };
}
