"""
Multi-Provider LLM Client
Supports: Claude (Anthropic), OpenAI, OpenRouter, DeepSeek, Ollama (local)
All providers normalized to a single chat() interface
"""

import json
import os
from typing import Optional


# ---------------------------------------------------------------------------
# Provider & Model Registry
# ---------------------------------------------------------------------------

PROVIDERS = {
    "claude": {
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com",
        "key_env": "ANTHROPIC_API_KEY",
        "models": {
            "claude-opus-4-7":       "Claude Opus 4.7 (Most Capable)",
            "claude-sonnet-4-6":     "Claude Sonnet 4.6 (Recommended)",
            "claude-haiku-4-5-20251001": "Claude Haiku 4.5 (Fast)",
        },
        "default_model": "claude-sonnet-4-6",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "models": {
            "gpt-4o":           "GPT-4o (Best)",
            "gpt-4o-mini":      "GPT-4o Mini (Fast & Cheap)",
            "gpt-4-turbo":      "GPT-4 Turbo",
            "o1-preview":       "o1-preview (Reasoning)",
            "o1-mini":          "o1-mini (Reasoning Fast)",
        },
        "default_model": "gpt-4o",
    },
    "openrouter": {
        "name": "OpenRouter (Any Model)",
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "models": {
            # ── Best for Engineering (smart + tool use) ──
            "google/gemini-2.5-flash":                      "⭐ Gemini 2.5 Flash — Fast & Smart (Recommended)",
            "anthropic/claude-sonnet-4-5":                  "⭐ Claude Sonnet 4.5 — Best Engineering",
            "deepseek/deepseek-chat":                       "⭐ DeepSeek V3 — Cheap & Very Smart",
            "deepseek/deepseek-r1":                         "⭐ DeepSeek R1 — Reasoning (like o1)",
            # ── Fast & Cheap ──
            "google/gemini-2.0-flash-001":                  "🚀 Gemini 2.0 Flash — Ultra Fast",
            "google/gemini-flash-1.5-8b":                   "🚀 Gemini 1.5 Flash 8B — Cheapest Google",
            "meta-llama/llama-3.3-70b-instruct":            "🚀 Llama 3.3 70B — Fast & Free tier",
            "meta-llama/llama-3.1-8b-instruct:free":        "🆓 Llama 3.1 8B — FREE",
            "mistralai/mistral-small-3.2-24b-instruct":     "🚀 Mistral Small 3.2 — Fast & Cheap",
            "qwen/qwen-2.5-72b-instruct":                   "🚀 Qwen 2.5 72B — Strong & Cheap",
            "qwen/qwen3-8b:free":                           "🆓 Qwen3 8B — FREE",
            # ── Premium / Most Capable ──
            "anthropic/claude-opus-4-5":                    "💎 Claude Opus 4.5 — Most Capable",
            "openai/gpt-4o":                                "💎 GPT-4o — OpenAI Best",
            "openai/gpt-4.1-mini":                          "🚀 GPT-4.1 Mini — Fast OpenAI",
            "google/gemini-pro-1.5":                        "💎 Gemini Pro 1.5",
            # ── Reasoning Models ──
            "openai/o3-mini":                               "🧠 o3-mini — OpenAI Reasoning",
            "deepseek/deepseek-r1-distill-llama-70b":       "🧠 DeepSeek R1 Distill 70B — Cheap Reasoning",
        },
        "default_model": "google/gemini-2.5-flash",
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "key_env": "DEEPSEEK_API_KEY",
        "models": {
            "deepseek-chat":     "DeepSeek Chat (V3)",
            "deepseek-reasoner": "DeepSeek R1 (Reasoning)",
        },
        "default_model": "deepseek-chat",
    },
    "ollama": {
        "name": "Ollama (Local / Free)",
        "base_url": "http://localhost:11434/v1",
        "key_env": None,
        "models": {
            "llama3.2":         "Llama 3.2 (Local)",
            "mistral":          "Mistral 7B (Local)",
            "deepseek-r1:7b":   "DeepSeek R1 7B (Local)",
            "qwen2.5:7b":       "Qwen 2.5 7B (Local)",
            "phi3":             "Phi-3 Mini (Local)",
        },
        "default_model": "llama3.2",
    },
}


# ---------------------------------------------------------------------------
# Unified Client
# ---------------------------------------------------------------------------

class LLMClient:
    """
    Single interface for all LLM providers.
    Uses Anthropic SDK for Claude, OpenAI SDK (compatible) for all others.
    """

    def __init__(self, provider: str = "claude", model: Optional[str] = None,
                 api_key: Optional[str] = None):
        self.provider = provider
        self.provider_config = PROVIDERS.get(provider, PROVIDERS["claude"])
        self.model = model or self.provider_config["default_model"]
        self.api_key = api_key or self._load_key()
        self._client = None
        self._init_client()

    def _load_key(self) -> str:
        env_var = self.provider_config.get("key_env")
        if env_var:
            return os.getenv(env_var, "")
        return "ollama"  # Ollama doesn't need a key

    def _init_client(self):
        if self.provider == "claude":
            self._init_claude()
        else:
            self._init_openai_compatible()

    def _init_claude(self):
        try:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
            self._type = "claude"
        except ImportError:
            raise ImportError("Run: pip install anthropic")

    def _init_openai_compatible(self):
        try:
            from openai import OpenAI
            kwargs = {"base_url": self.provider_config["base_url"]}
            if self.provider == "ollama":
                kwargs["api_key"] = "ollama"
            elif self.provider == "openrouter":
                kwargs["api_key"] = self.api_key
                kwargs["default_headers"] = {
                    "HTTP-Referer": "https://che-design-agent.local",
                    "X-Title": "ChE Design Agent"
                }
            else:
                kwargs["api_key"] = self.api_key
            self._client = OpenAI(**kwargs)
            self._type = "openai_compatible"
        except ImportError:
            raise ImportError("Run: pip install openai")

    def chat(self, messages: list, system_prompt: str, tools: list,
             max_tokens: int = 8096) -> dict:
        """
        Unified chat call. Returns:
        {"text": str, "tool_calls": [{"name": str, "input": dict, "id": str}]}
        """
        if self._type == "claude":
            return self._chat_claude(messages, system_prompt, tools, max_tokens)
        else:
            return self._chat_openai(messages, system_prompt, tools, max_tokens)

    # ------------------------------------------------------------------
    # Claude (Anthropic SDK)
    # ------------------------------------------------------------------

    def _chat_claude(self, messages, system_prompt, tools, max_tokens) -> dict:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )
        text = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "name": block.name,
                    "input": block.input,
                    "id": block.id,
                    "raw_block": block,
                })
        return {"text": text, "tool_calls": tool_calls, "raw": response}

    def _make_tool_result_claude(self, tool_id: str, result: str) -> dict:
        return {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": tool_id, "content": result}]
        }

    # ------------------------------------------------------------------
    # OpenAI-compatible (OpenAI, OpenRouter, DeepSeek, Ollama)
    # ------------------------------------------------------------------

    def _chat_openai(self, messages, system_prompt, tools, max_tokens) -> dict:
        oai_messages = [{"role": "system", "content": system_prompt}] + [
            self._convert_msg_to_oai(m) for m in messages
        ]
        oai_tools = [self._convert_tool_to_oai(t) for t in tools] if tools else None

        kwargs = {
            "model": self.model,
            "messages": oai_messages,
            "max_tokens": max_tokens,
        }
        if oai_tools:
            kwargs["tools"] = oai_tools
            kwargs["tool_choice"] = "auto"

        response = self._client.chat.completions.create(**kwargs)
        msg = response.choices[0].message

        text = msg.content or ""
        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append({
                    "name": tc.function.name,
                    "input": args,
                    "id": tc.id,
                    "raw_block": tc,
                })
        return {"text": text, "tool_calls": tool_calls, "raw": response}

    def _convert_msg_to_oai(self, msg: dict) -> dict:
        role = msg["role"]
        content = msg["content"]
        # Handle tool result messages (Anthropic format → OpenAI format)
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    return {
                        "role": "tool",
                        "tool_call_id": item["tool_use_id"],
                        "content": item["content"],
                    }
            # Assistant message with tool_use blocks
            text_parts = [b.text for b in content if hasattr(b, "type") and b.type == "text"]
            tool_calls = []
            for b in content:
                if hasattr(b, "type") and b.type == "tool_use":
                    tool_calls.append({
                        "id": b.id,
                        "type": "function",
                        "function": {"name": b.name, "arguments": json.dumps(b.input)},
                    })
            oai_msg = {"role": role, "content": " ".join(text_parts) or None}
            if tool_calls:
                oai_msg["tool_calls"] = tool_calls
            return oai_msg
        return {"role": role, "content": content}

    def _convert_tool_to_oai(self, tool: dict) -> dict:
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            }
        }

    def _make_tool_result_openai(self, tool_id: str, result: str, messages: list):
        messages.append({
            "role": "tool",
            "tool_call_id": tool_id,
            "content": result,
        })

    # ------------------------------------------------------------------
    # Follow-up after tool call (provider-aware)
    # ------------------------------------------------------------------

    def follow_up(self, messages: list, system_prompt: str, tools: list,
                  max_tokens: int = 8096) -> dict:
        return self.chat(messages, system_prompt, tools, max_tokens)

    @property
    def provider_name(self) -> str:
        return self.provider_config["name"]

    @property
    def model_name(self) -> str:
        models = self.provider_config.get("models", {})
        return models.get(self.model, self.model)
