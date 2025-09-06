from typing import Any
from agents import Agent, AgentHooks, RunContextWrapper, Tool
import logging


logger = logging.getLogger("AgentSystem")


# ===== 自定义 Hooks =====
class CustomAgentHooks(AgentHooks):
    def __init__(self, display_name: str = "REASONING"):
        self.event_counter = 0
        self.display_name = display_name

    async def on_start(self, context: RunContextWrapper, agent: Agent) -> None:
        self.event_counter += 1
        logger.info(f"[bold green]### ({self.display_name}) {self.event_counter}: Agent {agent.name} started[/]")

    async def on_end(self, context: RunContextWrapper, agent: Agent, output: Any) -> None:
        self.event_counter += 1
        logger.info(f"[bold green]### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended with output {output}[/]")

    async def on_handoff(self, context: RunContextWrapper, agent: Agent, source: Agent) -> None:
        self.event_counter += 1
        logger.info(f"[bold yellow]### ({self.display_name}) {self.event_counter}: Agent {source.name} handed off to {agent.name}[/]")

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool) -> None:
        self.event_counter += 1
        logger.info(f"[bold cyan]### ({self.display_name}) {self.event_counter}: Agent {agent.name} started tool {tool.name}[/]")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str) -> None:
        self.event_counter += 1
        logger.info(f"[bold cyan]### ({self.display_name}) {self.event_counter}: Agent {agent.name} ended tool {tool.name}[/]")
