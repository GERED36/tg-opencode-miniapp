"""Model database with parameters and context limits for popular models."""

from dataclasses import dataclass


@dataclass
class ModelInfo:
    model_id: str
    name: str
    parameters: str  # e.g., "7B", "13B", "70B", "Unknown"
    context_limit: int  # in tokens
    provider: str
    supports_text: bool = True
    supports_image: bool = False
    supports_video: bool = False
    supports_file: bool = False


# Popular models database - extracted from opencode models --verbose
MODELS_DB: list[ModelInfo] = [
    # OpenCode models
    ModelInfo("opencode/big-pickle", "Big Pickle", "Unknown", 200000, "opencode", True, False, False, False),
    ModelInfo("opencode/deepseek-v4-flash-free", "DeepSeek V4 Flash Free", "Unknown", 128000, "opencode", True, False, False, False),
    ModelInfo("opencode/mimo-v2.5-free", "MiMo V2.5 Free", "Unknown", 1048576, "opencode", True, False, False, False),
    ModelInfo("opencode/nemotron-3-ultra-free", "Nemotron 3 Ultra Free", "Unknown", 131072, "opencode", True, False, False, False),
    ModelInfo("opencode/north-mini-code-free", "North Mini Code Free", "Unknown", 32000, "opencode", True, False, False, False),

    # Google Gemini models
    ModelInfo("google/gemini-2.5-flash", "Gemini 2.5 Flash", "Unknown", 1048576, "google", True, True, True, True),
    ModelInfo("google/gemini-2.5-pro", "Gemini 2.5 Pro", "Unknown", 1048576, "google", True, True, True, True),
    ModelInfo("google/gemini-3-flash-preview", "Gemini 3 Flash Preview", "Unknown", 1048576, "google", True, True, True, True),
    ModelInfo("google/gemini-3.1-flash-lite", "Gemini 3.1 Flash Lite", "Unknown", 1048576, "google", True, True, False, False),
    ModelInfo("google/gemini-3.5-flash", "Gemini 3.5 Flash", "Unknown", 1048576, "google", True, True, True, True),

    # OpenAI models
    ModelInfo("openai/gpt-3.5-turbo", "GPT-3.5 Turbo", "Unknown", 16385, "openai", True, False, False, False),
    ModelInfo("openai/gpt-4", "GPT-4", "Unknown", 8192, "openai", True, False, False, False),
    ModelInfo("openai/gpt-4-turbo", "GPT-4 Turbo", "Unknown", 128000, "openai", True, True, False, False),
    ModelInfo("openai/gpt-4o", "GPT-4o", "Unknown", 128000, "openai", True, True, False, True),
    ModelInfo("openai/gpt-4o-mini", "GPT-4o Mini", "Unknown", 128000, "openai", True, True, False, False),
    ModelInfo("openai/gpt-5", "GPT-5", "Unknown", 128000, "openai", True, True, False, True),
    ModelInfo("openai/gpt-5-mini", "GPT-5 Mini", "Unknown", 128000, "openai", True, True, False, True),
    ModelInfo("openai/gpt-5.1", "GPT-5.1", "Unknown", 128000, "openai", True, True, False, True),
    ModelInfo("openai/gpt-5.2", "GPT-5.2", "Unknown", 128000, "openai", True, True, False, True),
    ModelInfo("openai/gpt-5.4", "GPT-5.4", "Unknown", 128000, "openai", True, True, False, True),
    ModelInfo("openai/gpt-5.5", "GPT-5.5", "Unknown", 128000, "openai", True, True, False, True),
    ModelInfo("openai/o1", "o1", "Unknown", 200000, "openai", True, True, False, False),
    ModelInfo("openai/o3", "o3", "Unknown", 200000, "openai", True, True, False, False),
    ModelInfo("openai/o3-mini", "o3 Mini", "Unknown", 200000, "openai", True, False, False, False),
    ModelInfo("openai/o4-mini", "o4 Mini", "Unknown", 200000, "openai", True, True, False, False),

    # Anthropic Claude models (via OpenRouter)
    ModelInfo("openrouter/anthropic/claude-3-haiku", "Claude 3 Haiku", "Unknown", 200000, "openrouter", True, True, False, False),
    ModelInfo("openrouter/anthropic/claude-3.5-haiku", "Claude 3.5 Haiku", "Unknown", 200000, "openrouter", True, True, False, False),
    ModelInfo("openrouter/anthropic/claude-sonnet-4", "Claude Sonnet 4", "Unknown", 200000, "openrouter", True, True, False, False),
    ModelInfo("openrouter/anthropic/claude-opus-4", "Claude Opus 4", "Unknown", 200000, "openrouter", True, True, False, False),
    ModelInfo("openrouter/anthropic/claude-opus-4.5", "Claude Opus 4.5", "Unknown", 200000, "openrouter", True, True, False, False),
    ModelInfo("openrouter/anthropic/claude-opus-4.8", "Claude Opus 4.8", "Unknown", 200000, "openrouter", True, True, False, False),

    # DeepSeek models (via OpenRouter)
    ModelInfo("openrouter/deepseek/deepseek-chat", "DeepSeek Chat", "Unknown", 64000, "openrouter", True, False, False, False),
    ModelInfo("openrouter/deepseek/deepseek-r1", "DeepSeek R1", "Unknown", 64000, "openrouter", True, False, False, False),
    ModelInfo("openrouter/deepseek/deepseek-v3.2", "DeepSeek V3.2", "Unknown", 64000, "openrouter", True, False, False, False),
    ModelInfo("openrouter/deepseek/deepseek-v4-flash", "DeepSeek V4 Flash", "Unknown", 128000, "openrouter", True, False, False, False),
    ModelInfo("openrouter/deepseek/deepseek-v4-pro", "DeepSeek V4 Pro", "Unknown", 128000, "openrouter", True, False, False, False),

    # Meta Llama models (via OpenRouter)
    ModelInfo("openrouter/meta-llama/llama-3-70b-instruct", "Llama 3 70B", "70B", 8192, "openrouter", True, False, False, False),
    ModelInfo("openrouter/meta-llama/llama-3.1-70b-instruct", "Llama 3.1 70B", "70B", 131072, "openrouter", True, True, False, False),
    ModelInfo("openrouter/meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B", "70B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/meta-llama/llama-4-maverick", "Llama 4 Maverick", "Unknown", 1048576, "openrouter", True, True, False, False),
    ModelInfo("openrouter/meta-llama/llama-4-scout", "Llama 4 Scout", "Unknown", 1048576, "openrouter", True, True, False, False),

    # Qwen models (via OpenRouter)
    ModelInfo("openrouter/qwen/qwen3-235b-a22b", "Qwen3 235B", "235B", 131072, "openrouter", True, True, False, False),
    ModelInfo("openrouter/qwen/qwen3-32b", "Qwen3 32B", "32B", 131072, "openrouter", True, True, False, False),
    ModelInfo("openrouter/qwen/qwen3-coder", "Qwen3 Coder", "Unknown", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/qwen/qwen3.5-397b-a17b", "Qwen3.5 397B", "397B", 131072, "openrouter", True, True, False, False),

    # Mistral models (via OpenRouter)
    ModelInfo("openrouter/mistralai/mistral-large", "Mistral Large", "Unknown", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/mistralai/mistral-medium-3", "Mistral Medium 3", "Unknown", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/mistralai/codestral-2508", "Codestral 2508", "Unknown", 262144, "openrouter", True, False, False, False),

    # xAI Grok models (via OpenRouter)
    ModelInfo("openrouter/x-ai/grok-4.20", "Grok 4.20", "Unknown", 2000000, "openrouter", True, True, False, True),
    ModelInfo("openrouter/x-ai/grok-4.3", "Grok 4.3", "Unknown", 1000000, "openrouter", True, True, False, True),

    # NVIDIA models (via OpenRouter)
    ModelInfo("openrouter/nvidia/nemotron-3-ultra-550b-a55b", "Nemotron 3 Ultra 550B", "550B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/nvidia/nemotron-3-super-120b-a12b", "Nemotron 3 Super 120B", "120B", 131072, "openrouter", True, False, False, False),

    # MiniMax models (via OpenRouter)
    ModelInfo("openrouter/minimax/minimax-m1", "MiniMax M1", "Unknown", 1000000, "openrouter", True, False, False, False),
    ModelInfo("openrouter/minimax/minimax-m2.5", "MiniMax M2.5", "Unknown", 1000000, "openrouter", True, False, False, False),

    # Xiaomi MiMo models (via OpenRouter)
    ModelInfo("openrouter/xiaomi/mimo-v2-flash", "MiMo V2 Flash", "Unknown", 262144, "openrouter", True, False, False, False),
    ModelInfo("openrouter/xiaomi/mimo-v2.5", "MiMo V2.5", "Unknown", 1048576, "openrouter", True, True, True, True),
    ModelInfo("openrouter/xiaomi/mimo-v2.5-pro", "MiMo V2.5 Pro", "Unknown", 1048576, "openrouter", True, False, False, False),

    # Moonshot Kimi models (via OpenRouter)
    ModelInfo("openrouter/moonshotai/kimi-k2", "Kimi K2", "Unknown", 131072, "openrouter", True, True, False, False),
    ModelInfo("openrouter/moonshotai/kimi-k2.5", "Kimi K2.5", "Unknown", 131072, "openrouter", True, True, False, False),
    ModelInfo("openrouter/moonshotai/kimi-k2.7-code", "Kimi K2.7 Code", "Unknown", 131072, "openrouter", True, False, False, False),

    # Zhipu GLM models (via OpenRouter)
    ModelInfo("openrouter/z-ai/glm-5", "GLM-5", "Unknown", 202752, "openrouter", True, False, False, False),
    ModelInfo("openrouter/z-ai/glm-5.1", "GLM-5.1", "Unknown", 202752, "openrouter", True, False, False, False),

    # OpenRouter Free models
    ModelInfo("openrouter/cognitivecomputations/dolphin-mistral-24b-venice-edition:free", "Dolphin Mistral 24B Free", "24B", 32768, "openrouter", True, False, False, False),
    ModelInfo("openrouter/google/gemma-4-26b-a4b-it:free", "Gemma 4 26B Free", "26B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/google/gemma-4-31b-it:free", "Gemma 4 31B Free", "31B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/liquid/lfm-2.5-1.2b-instruct:free", "LFM 2.5 1.2B Instruct Free", "1.2B", 32768, "openrouter", True, False, False, False),
    ModelInfo("openrouter/liquid/lfm-2.5-1.2b-thinking:free", "LFM 2.5 1.2B Thinking Free", "1.2B", 32768, "openrouter", True, False, False, False),
    ModelInfo("openrouter/meta-llama/llama-3.2-3b-instruct:free", "Llama 3.2 3B Free", "3B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/meta-llama/llama-3.3-70b-instruct:free", "Llama 3.3 70B Free", "70B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/nex-agi/nex-n2-pro:free", "Nex N2 Pro Free", "Unknown", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/nousresearch/hermes-3-llama-3.1-405b:free", "Hermes 3 405B Free", "405B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/nvidia/nemotron-3-nano-30b-a3b:free", "Nemotron 3 Nano 30B Free", "30B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "Nemotron 3 Nano Omni Free", "30B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/nvidia/nemotron-3-super-120b-a12b:free", "Nemotron 3 Super 120B Free", "120B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/nvidia/nemotron-3-ultra-550b-a55b:free", "Nemotron 3 Ultra 550B Free", "550B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/nvidia/nemotron-3.5-content-safety:free", "Nemotron 3.5 Content Safety Free", "Unknown", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/nvidia/nemotron-nano-12b-v2-vl:free", "Nemotron Nano 12B VL Free", "12B", 131072, "openrouter", True, True, False, False),
    ModelInfo("openrouter/nvidia/nemotron-nano-9b-v2:free", "Nemotron Nano 9B Free", "9B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/openai/gpt-oss-120b:free", "GPT OSS 120B Free", "120B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/openai/gpt-oss-20b:free", "GPT OSS 20B Free", "20B", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/poolside/laguna-m.1:free", "Laguna M.1 Free", "Unknown", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/poolside/laguna-xs.2:free", "Laguna XS.2 Free", "Unknown", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/qwen/qwen3-coder:free", "Qwen3 Coder Free", "Unknown", 131072, "openrouter", True, False, False, False),
    ModelInfo("openrouter/qwen/qwen3-next-80b-a3b-instruct:free", "Qwen3 Next 80B Free", "80B", 131072, "openrouter", True, False, False, False),
]


def get_model_by_id(model_id: str) -> ModelInfo | None:
    """Get model info by model ID."""
    for model in MODELS_DB:
        if model.model_id == model_id:
            return model
    return None


def search_models(query: str) -> list[ModelInfo]:
    """Search models by name or ID."""
    query_lower = query.lower()
    return [
        m for m in MODELS_DB
        if query_lower in m.model_id.lower() or query_lower in m.name.lower()
    ]


def get_models_by_provider(provider: str) -> list[ModelInfo]:
    """Get all models from a specific provider."""
    return [m for m in MODELS_DB if m.provider == provider.lower()]


def format_context_limit(tokens: int) -> str:
    """Format context limit in human-readable format."""
    if tokens >= 1000000:
        return f"{tokens / 1000000:.1f}M"
    elif tokens >= 1000:
        return f"{tokens // 1000}K"
    return str(tokens)


def get_free_models() -> list[ModelInfo]:
    """Get all free models (containing 'free' in ID or name)."""
    return [
        m for m in MODELS_DB
        if "free" in m.model_id.lower() or "free" in m.name.lower()
    ]


def format_capabilities(model: ModelInfo) -> str:
    """Format model capabilities as emoji string."""
    caps = []
    if model.supports_text:
        caps.append("📝")
    if model.supports_image:
        caps.append("🖼")
    if model.supports_video:
        caps.append("🎬")
    if model.supports_file:
        caps.append("📁")
    return " ".join(caps) if caps else "❌"
