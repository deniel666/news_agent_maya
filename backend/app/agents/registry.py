"""Agent registry for dynamic node management in Maya pipeline.

This module provides:
- Dynamic agent registration with decorators
- Automatic LLM configuration injection
- Agent execution with config-aware parameters
- Plugin system for custom agents
"""

from typing import Dict, Any, Optional, Callable, List, TypeVar, Awaitable
from functools import wraps
import asyncio
import logging

from langchain_openai import ChatOpenAI

from .config import (
    AgentConfig,
    AgentType,
    LLMConfig,
    get_config_manager,
)
from .state import MayaState

logger = logging.getLogger(__name__)

# Type for agent handler functions
AgentHandler = Callable[[MayaState, AgentConfig], Awaitable[Dict[str, Any]]]


class AgentRegistry:
    """Registry for pipeline agents with dynamic registration."""

    def __init__(self):
        self._handlers: Dict[str, AgentHandler] = {}
        self._llm_cache: Dict[str, ChatOpenAI] = {}

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def register(
        self,
        agent_id: str,
        handler: Optional[AgentHandler] = None,
    ) -> Callable:
        """Register an agent handler function.

        Can be used as a decorator or called directly:

        # As decorator
        @registry.register("my_agent")
        async def my_agent_handler(state: MayaState, config: AgentConfig) -> Dict[str, Any]:
            ...

        # Direct registration
        registry.register("my_agent", my_handler_function)
        """
        def decorator(fn: AgentHandler) -> AgentHandler:
            self._handlers[agent_id] = fn
            logger.info(f"Registered agent handler: {agent_id}")
            return fn

        if handler is not None:
            return decorator(handler)
        return decorator

    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent handler."""
        if agent_id in self._handlers:
            del self._handlers[agent_id]
            logger.info(f"Unregistered agent handler: {agent_id}")
            return True
        return False

    def get_handler(self, agent_id: str) -> Optional[AgentHandler]:
        """Get registered handler for an agent."""
        return self._handlers.get(agent_id)

    def list_registered(self) -> List[str]:
        """List all registered agent IDs."""
        return list(self._handlers.keys())

    def is_registered(self, agent_id: str) -> bool:
        """Check if an agent is registered."""
        return agent_id in self._handlers

    # -------------------------------------------------------------------------
    # LLM Management
    # -------------------------------------------------------------------------

    def get_llm(self, config: LLMConfig, cache_key: Optional[str] = None) -> ChatOpenAI:
        """Get or create an LLM instance with the given configuration.

        Uses caching to reuse LLM instances with the same configuration.
        """
        from ..core.config import settings

        # Create a cache key from the config if not provided
        if cache_key is None:
            cache_key = f"{config.model}_{config.temperature}_{config.max_tokens}"

        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = ChatOpenAI(
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                top_p=config.top_p,
                frequency_penalty=config.frequency_penalty,
                presence_penalty=config.presence_penalty,
                api_key=settings.openai_api_key,
            )

        return self._llm_cache[cache_key]

    def clear_llm_cache(self) -> None:
        """Clear the LLM instance cache."""
        self._llm_cache.clear()

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    async def execute(
        self,
        agent_id: str,
        state: MayaState,
        config_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an agent with the current state and configuration.

        Args:
            agent_id: ID of the agent to execute
            state: Current pipeline state
            config_override: Optional overrides for agent config

        Returns:
            Dictionary of state updates from the agent
        """
        # Get agent configuration
        config_manager = get_config_manager()
        agent_config = config_manager.get_agent(agent_id)

        if agent_config is None:
            raise ValueError(f"Agent not found in configuration: {agent_id}")

        if not agent_config.enabled:
            logger.info(f"Agent {agent_id} is disabled, skipping execution")
            return {}

        # Apply config overrides
        if config_override:
            config_data = agent_config.model_dump()
            config_data.update(config_override)
            agent_config = AgentConfig(**config_data)

        # Get handler
        handler = self._handlers.get(agent_id)
        if handler is None:
            # Check for custom handler in config manager
            handler = config_manager.get_custom_handler(agent_id)

        if handler is None:
            raise ValueError(f"No handler registered for agent: {agent_id}")

        # Execute with timeout
        logger.info(f"Executing agent: {agent_id} (timeout: {agent_config.timeout_seconds}s)")

        try:
            result = await asyncio.wait_for(
                handler(state, agent_config),
                timeout=agent_config.timeout_seconds
            )
            logger.info(f"Agent {agent_id} completed successfully")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Agent {agent_id} timed out after {agent_config.timeout_seconds}s")
            return {"error": f"Agent {agent_id} timed out"}

        except Exception as e:
            logger.error(f"Agent {agent_id} failed: {str(e)}")
            return {"error": str(e)}

    async def execute_parallel(
        self,
        agent_ids: List[str],
        state: MayaState,
    ) -> Dict[str, Any]:
        """Execute multiple agents in parallel and merge results.

        Args:
            agent_ids: List of agent IDs to execute in parallel
            state: Current pipeline state

        Returns:
            Merged dictionary of all agent state updates
        """
        tasks = [
            self.execute(agent_id, state)
            for agent_id in agent_ids
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge results
        merged = {}
        for agent_id, result in zip(agent_ids, results):
            if isinstance(result, Exception):
                logger.error(f"Agent {agent_id} raised exception: {result}")
                merged["error"] = str(result)
            elif isinstance(result, dict):
                merged.update(result)

        return merged


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


# =============================================================================
# DECORATOR HELPERS
# =============================================================================

def agent(agent_id: str):
    """Decorator to register an agent handler.

    Usage:
        @agent("my_agent")
        async def my_agent_handler(state: MayaState, config: AgentConfig) -> Dict[str, Any]:
            # Access LLM if configured
            if config.llm_config:
                llm = get_registry().get_llm(config.llm_config)
                # Use llm...

            return {"output_field": result}
    """
    def decorator(fn: AgentHandler) -> AgentHandler:
        registry = get_registry()
        registry.register(agent_id, fn)
        return fn
    return decorator


def with_llm(fn: AgentHandler) -> AgentHandler:
    """Decorator that injects LLM instance into handler if configured.

    Usage:
        @agent("my_synthesizer")
        @with_llm
        async def my_synthesizer(state: MayaState, config: AgentConfig, llm: ChatOpenAI = None):
            if llm:
                response = await llm.ainvoke(...)
    """
    @wraps(fn)
    async def wrapper(state: MayaState, config: AgentConfig) -> Dict[str, Any]:
        llm = None
        if config.llm_config:
            llm = get_registry().get_llm(config.llm_config, cache_key=config.id)
        return await fn(state, config, llm=llm)
    return wrapper


def with_mcp_tools(fn: AgentHandler) -> AgentHandler:
    """Decorator that injects MCP tools into handler if configured.

    This decorator provides MCP tool calling capabilities to agents.
    Tools are injected as callable async functions that the agent can use.

    Prefers Composio when configured (500+ tools via single endpoint),
    falls back to legacy MCP servers otherwise.

    Usage:
        @agent("research")
        @with_mcp_tools
        async def research_agent(
            state: MayaState,
            config: AgentConfig,
            mcp_tools: Dict[str, Callable] = None
        ) -> Dict[str, Any]:
            # Use MCP tools if available
            if mcp_tools and "get_trending_keywords" in mcp_tools:
                trending = await mcp_tools["get_trending_keywords"](geo="MY")
                if trending.get("success"):
                    # Process trending topics...

            return {"raw_articles": articles}
    """
    @wraps(fn)
    async def wrapper(state: MayaState, config: AgentConfig) -> Dict[str, Any]:
        mcp_tools: Dict[str, Callable] = {}
        thread_id = state.get("thread_id", "")

        try:
            from app.mcp.registry import get_mcp_registry

            registry = get_mcp_registry()

            # Try Composio first (preferred - 500+ tools via single endpoint)
            if registry.composio_enabled:
                try:
                    composio_client = await registry.get_composio_client()
                    if composio_client:
                        # Discover tools if not already done
                        if not composio_client.list_tools():
                            await composio_client.discover_tools()

                        for tool_name in composio_client.list_tools():
                            async def create_composio_caller(tname: str):
                                async def call_tool(**kwargs):
                                    return await registry.call_composio_tool(
                                        tool_name=tname,
                                        arguments=kwargs,
                                        agent_id=config.id if config else None,
                                        thread_id=thread_id,
                                    )
                                return call_tool

                            mcp_tools[tool_name] = await create_composio_caller(tool_name)

                        logger.info(f"Injected {len(mcp_tools)} Composio tools for agent {config.id if config else 'unknown'}")

                except Exception as e:
                    logger.warning(f"Composio tools injection failed: {e}")

            # Fall back to legacy MCP servers if configured and Composio didn't provide tools
            if config and config.uses_mcp() and not mcp_tools:
                for server_id in config.get_mcp_servers():
                    client = await registry.get_client(server_id)
                    if client:
                        for tool_name in client.list_tools():
                            async def create_tool_caller(sid: str, tname: str):
                                async def call_tool(**kwargs):
                                    return await registry.call_tool(
                                        server_id=sid,
                                        tool_name=tname,
                                        arguments=kwargs,
                                        agent_id=config.id,
                                        thread_id=thread_id,
                                    )
                                return call_tool

                            mcp_tools[tool_name] = await create_tool_caller(server_id, tool_name)

                logger.info(f"Injected {len(mcp_tools)} legacy MCP tools for agent {config.id}")

        except ImportError:
            logger.warning("MCP module not available, skipping MCP tools injection")
        except Exception as e:
            logger.error(f"Error injecting MCP tools: {e}")

        return await fn(state, config, mcp_tools=mcp_tools)

    return wrapper


# =============================================================================
# NODE WRAPPER FOR LANGGRAPH
# =============================================================================

def create_node_function(agent_id: str) -> Callable[[MayaState], Awaitable[Dict[str, Any]]]:
    """Create a LangGraph node function for an agent.

    This wraps the agent execution to be compatible with LangGraph's
    expected function signature.
    """
    async def node_function(state: MayaState) -> Dict[str, Any]:
        registry = get_registry()
        return await registry.execute(agent_id, state)

    # Set function name for LangGraph
    node_function.__name__ = agent_id
    return node_function


def create_parallel_node(agent_ids: List[str]) -> Callable[[MayaState], Awaitable[Dict[str, Any]]]:
    """Create a LangGraph node that executes multiple agents in parallel."""
    async def parallel_node(state: MayaState) -> Dict[str, Any]:
        registry = get_registry()
        return await registry.execute_parallel(agent_ids, state)

    parallel_node.__name__ = f"parallel_{'_'.join(agent_ids)}"
    return parallel_node
