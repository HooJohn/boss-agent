import asyncio

from typing import Any, Optional
from boss_agent.browser.browser import Browser
from boss_agent.tools.base import ToolImplOutput
from boss_agent.tools.browser_tools import BrowserTool, utils
from boss_agent.llm.message_history import MessageHistory


class BrowserClickTool(BrowserTool):
    name = "browser_click"
    description = "Click on an element on the current browser page"
    input_schema = {
        "type": "object",
        "properties": {
            "coordinate_x": {
                "type": "number",
                "description": "X coordinate of click position",
            },
            "coordinate_y": {
                "type": "number",
                "description": "Y coordinate of click position",
            },
        },
        "required": ["coordinate_x", "coordinate_y"],
    }

    def __init__(self, browser: Browser):
        super().__init__(browser)

    async def _run(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        coordinate_x = tool_input.get("coordinate_x")
        coordinate_y = tool_input.get("coordinate_y")

        if not coordinate_x or not coordinate_y:
            msg = (
                "Must provide both coordinate_x and coordinate_y to click on an element"
            )
            return ToolImplOutput(tool_output=msg, tool_result_message=msg)

        page = await self.browser.get_current_page()
        initial_pages = len(self.browser.context.pages) if self.browser.context else 0

        await page.mouse.click(coordinate_x, coordinate_y)
        await asyncio.sleep(1)
        msg = f"Clicked at coordinates {coordinate_x}, {coordinate_y}"

        if self.browser.context and len(self.browser.context.pages) > initial_pages:
            new_tab_msg = "New tab opened - switching to it"
            msg += f" - {new_tab_msg}"
            await self.browser.switch_to_tab(-1)
            await asyncio.sleep(0.1)

        state = await self.browser.update_state()
        state = await self.browser.handle_pdf_url_navigation()

        return utils.format_screenshot_tool_output(state.screenshot, msg)
