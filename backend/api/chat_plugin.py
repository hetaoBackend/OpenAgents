import base64
import copy
import json
import os
import random
import traceback
from typing import Dict, List, Union

import requests
from flask import Response, request, stream_with_context
from retrying import retry

from backend.api.language_model import get_llm
from backend.app import app
from backend.main import message_id_register, message_pool, logger
from backend.utils.streaming import single_round_chat_with_agent_streaming
from backend.schemas import OVERLOAD, NEED_CONTINUE_MODEL, DEFAULT_USER_ID
from backend.main import api_key_pool
from real_agents.adapters.llm import BaseLanguageModel
from real_agents.adapters.agent_helpers import AgentExecutor, Tool
from real_agents.adapters.callbacks.agent_streaming import \
    AgentStreamingStdOutCallbackHandler
from real_agents.adapters.data_model import DataModel, JsonDataModel
from real_agents.adapters.interactive_executor import initialize_plugin_agent
from real_agents.adapters.memory import ConversationReActBufferMemory
from real_agents.plugins_agent.plugins.utils import load_all_plugins_elements
from real_agents.plugins_agent.plugins.tool_selector import ToolSelector
from real_agents.plugins_agent import PluginExecutor

# The plugins list
global plugins
plugins = []

# Set up the tool selector for automatically selecting plugins
try:
    tool_selector = ToolSelector(tools_list=plugins, mode="embedding", api_key_pool=api_key_pool)
except Exception as e:
    print(e, "The auto selection feature of plugins agent will return random elements.")
    tool_selector = None

# Load plugin info and icon image
for plugin_type, plugin_info in load_all_plugins_elements().items():
    plugins.append(
        {
            "id": plugin_type,
            "name": plugin_type,
            "name_for_human": plugin_info["meta_info"]["manifest"]["name_for_human"],
            "description": plugin_info["description"],
            "icon": "",
            "require_api_key": plugin_info["need_auth"],
        }
    )
