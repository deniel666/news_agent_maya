"""Plugin system for external agents.

This module enables loading agents from external packages, enabling:
- Third-party agent integrations
- Custom business logic modules
- Hot-reloading of agent implementations
"""

from typing import Dict, Any, Optional, List, Callable, Type
from pathlib import Path
import importlib
import importlib.util
import inspect
import logging
import sys

from pydantic import BaseModel, Field

from .config import AgentConfig, AgentType, LLMConfig
from .registry import get_registry, AgentHandler
from .state import MayaState

logger = logging.getLogger(__name__)


class PluginMetadata(BaseModel):
    """Metadata for a plugin."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    homepage: str = ""

    # Dependencies
    requires: List[str] = Field(default_factory=list)

    # Agents provided by this plugin
    agents: List[str] = Field(default_factory=list)


class PluginInfo(BaseModel):
    """Information about a loaded plugin."""
    metadata: PluginMetadata
    module_path: str
    loaded_at: str
    enabled: bool = True
    error: Optional[str] = None


class PluginManager:
    """Manages agent plugins."""

    def __init__(self, plugins_dir: Optional[str] = None):
        self.plugins_dir = Path(plugins_dir) if plugins_dir else Path("plugins")
        self._loaded_plugins: Dict[str, PluginInfo] = {}
        self._plugin_modules: Dict[str, Any] = {}

    # -------------------------------------------------------------------------
    # Plugin Discovery
    # -------------------------------------------------------------------------

    def discover_plugins(self) -> List[str]:
        """Discover available plugins in the plugins directory."""
        if not self.plugins_dir.exists():
            logger.info(f"Plugins directory not found: {self.plugins_dir}")
            return []

        plugins = []
        for path in self.plugins_dir.iterdir():
            if path.is_dir() and (path / "__init__.py").exists():
                plugins.append(path.name)
            elif path.suffix == ".py" and path.stem != "__init__":
                plugins.append(path.stem)

        return plugins

    def list_loaded_plugins(self) -> List[PluginInfo]:
        """List all loaded plugins."""
        return list(self._loaded_plugins.values())

    # -------------------------------------------------------------------------
    # Plugin Loading
    # -------------------------------------------------------------------------

    def load_plugin(self, plugin_name: str) -> PluginInfo:
        """Load a plugin by name."""
        if plugin_name in self._loaded_plugins:
            return self._loaded_plugins[plugin_name]

        plugin_path = self.plugins_dir / plugin_name

        # Try as directory first
        if plugin_path.is_dir():
            module_path = plugin_path / "__init__.py"
        else:
            module_path = self.plugins_dir / f"{plugin_name}.py"

        if not module_path.exists():
            raise FileNotFoundError(f"Plugin not found: {plugin_name}")

        try:
            # Load module
            spec = importlib.util.spec_from_file_location(
                f"maya_plugin_{plugin_name}",
                module_path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            self._plugin_modules[plugin_name] = module

            # Get metadata
            metadata = self._extract_metadata(module, plugin_name)

            # Register agents
            self._register_plugin_agents(module, metadata)

            from datetime import datetime
            info = PluginInfo(
                metadata=metadata,
                module_path=str(module_path),
                loaded_at=datetime.utcnow().isoformat(),
                enabled=True,
            )

            self._loaded_plugins[plugin_name] = info
            logger.info(f"Loaded plugin: {plugin_name} v{metadata.version}")

            return info

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            from datetime import datetime
            info = PluginInfo(
                metadata=PluginMetadata(name=plugin_name, version="unknown"),
                module_path=str(module_path),
                loaded_at=datetime.utcnow().isoformat(),
                enabled=False,
                error=str(e),
            )
            self._loaded_plugins[plugin_name] = info
            return info

    def load_all_plugins(self) -> List[PluginInfo]:
        """Load all discovered plugins."""
        plugins = self.discover_plugins()
        results = []

        for plugin_name in plugins:
            info = self.load_plugin(plugin_name)
            results.append(info)

        return results

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        if plugin_name not in self._loaded_plugins:
            return False

        info = self._loaded_plugins[plugin_name]

        # Unregister agents
        registry = get_registry()
        for agent_id in info.metadata.agents:
            registry.unregister(agent_id)

        # Remove module
        if plugin_name in self._plugin_modules:
            del self._plugin_modules[plugin_name]

        module_name = f"maya_plugin_{plugin_name}"
        if module_name in sys.modules:
            del sys.modules[module_name]

        del self._loaded_plugins[plugin_name]
        logger.info(f"Unloaded plugin: {plugin_name}")

        return True

    def reload_plugin(self, plugin_name: str) -> PluginInfo:
        """Reload a plugin (hot-reload)."""
        self.unload_plugin(plugin_name)
        return self.load_plugin(plugin_name)

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _extract_metadata(self, module: Any, plugin_name: str) -> PluginMetadata:
        """Extract metadata from a plugin module."""
        # Check for PLUGIN_METADATA constant
        if hasattr(module, "PLUGIN_METADATA"):
            meta = module.PLUGIN_METADATA
            if isinstance(meta, dict):
                return PluginMetadata(**meta)
            elif isinstance(meta, PluginMetadata):
                return meta

        # Build from module attributes
        return PluginMetadata(
            name=getattr(module, "__plugin_name__", plugin_name),
            version=getattr(module, "__version__", "0.0.1"),
            description=getattr(module, "__doc__", "") or "",
            author=getattr(module, "__author__", ""),
        )

    def _register_plugin_agents(
        self,
        module: Any,
        metadata: PluginMetadata,
    ) -> None:
        """Register agents defined in a plugin."""
        registry = get_registry()
        registered_agents = []

        # Look for agent handlers (async functions with specific signature)
        for name, obj in inspect.getmembers(module):
            if not inspect.iscoroutinefunction(obj):
                continue

            # Check if it's decorated as an agent
            if hasattr(obj, "_agent_id"):
                agent_id = obj._agent_id
                registry.register(agent_id, obj)
                registered_agents.append(agent_id)
                continue

            # Check for convention: functions starting with "agent_"
            if name.startswith("agent_"):
                agent_id = name[6:]  # Remove "agent_" prefix
                registry.register(agent_id, obj)
                registered_agents.append(agent_id)

        # Look for AGENTS dict
        if hasattr(module, "AGENTS"):
            agents_dict = module.AGENTS
            for agent_id, handler in agents_dict.items():
                registry.register(agent_id, handler)
                registered_agents.append(agent_id)

        metadata.agents = registered_agents


# =============================================================================
# PLUGIN DECORATORS
# =============================================================================

def plugin_agent(agent_id: str):
    """Decorator to mark a function as a plugin agent.

    Usage:
        @plugin_agent("my_custom_agent")
        async def my_agent(state: MayaState, config: AgentConfig) -> Dict[str, Any]:
            return {"result": "done"}
    """
    def decorator(fn: AgentHandler) -> AgentHandler:
        fn._agent_id = agent_id
        return fn
    return decorator


# =============================================================================
# PLUGIN TEMPLATE
# =============================================================================

PLUGIN_TEMPLATE = '''"""
{name} - Maya Agent Plugin

{description}
"""

from typing import Dict, Any
from app.agents.state import MayaState
from app.agents.config import AgentConfig
from app.agents.plugins import plugin_agent

# Plugin metadata
PLUGIN_METADATA = {{
    "name": "{name}",
    "version": "0.1.0",
    "description": "{description}",
    "author": "{author}",
}}


@plugin_agent("{agent_id}")
async def {agent_function}(state: MayaState, config: AgentConfig = None) -> Dict[str, Any]:
    """
    {description}

    Args:
        state: Current pipeline state
        config: Agent configuration

    Returns:
        Dictionary of state updates
    """
    # TODO: Implement your agent logic here

    return {{
        "status": "completed",
    }}
'''


def create_plugin_template(
    name: str,
    description: str = "A custom Maya agent plugin",
    author: str = "",
    output_dir: Optional[str] = None,
) -> str:
    """Create a plugin template file."""
    agent_id = name.lower().replace(" ", "_").replace("-", "_")
    agent_function = f"agent_{agent_id}"

    content = PLUGIN_TEMPLATE.format(
        name=name,
        description=description,
        author=author,
        agent_id=agent_id,
        agent_function=agent_function,
    )

    if output_dir:
        output_path = Path(output_dir) / f"{agent_id}.py"
        output_path.write_text(content)
        return str(output_path)

    return content


# =============================================================================
# GLOBAL MANAGER
# =============================================================================

_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(plugins_dir: Optional[str] = None) -> PluginManager:
    """Get global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager(plugins_dir)
    return _plugin_manager
