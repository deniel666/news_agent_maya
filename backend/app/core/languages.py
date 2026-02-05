"""Language configuration for Maya AI News Anchor.

Supports multiple languages with locale-specific voice settings,
prompt instructions for code-switching, and review requirements.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class LanguageConfig(BaseModel):
    """Configuration for a supported language."""
    name: str
    locale: str
    heygen_locale: str
    prompt_instruction: str
    requires_external_review: bool = False

    # Optional voice configuration overrides
    voice_id: Optional[str] = None
    speech_speed: float = 1.0


# Language configurations for Maya
LANGUAGE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "en-SG": {
        "name": "English (Singapore)",
        "locale": "en-SG",
        "heygen_locale": "en-SG",
        "prompt_instruction": """Write in Malaysian/Singaporean English.
Use natural code-switching with occasional Malay words (lah, kan, alamak, syok, boleh).
Tone: Professional but warm, like a knowledgeable friend explaining business to a kedai owner.
Avoid: American idioms, overly formal British English, corporate jargon.

Example natural phrases:
- "This one quite important for your business lah"
- "Aiyo, the cost go up again"
- "Don't worry, can still make it work one"
- "This technology boleh help you save time"
""",
        "requires_external_review": False,
        "speech_speed": 1.0,
    },
    "ms-MY": {
        "name": "Bahasa Malaysia",
        "locale": "ms-MY",
        "heygen_locale": "ms-MY",
        "prompt_instruction": """Write in conversational Bahasa Malaysia.
Mix in common English business terms naturally (business, customer, sales, cash flow, online, marketing).
Tone: Mesra dan profesional, seperti kawan yang bijak.
Avoid: Formal bahasa baku, government-style language.

Contoh frasa semulajadi:
- "Ini penting untuk business anda"
- "Customer sekarang dah expect service yang lebih baik"
- "Cash flow kena jaga betul-betul"
- "Marketing online ni memang kena buat sekarang"
""",
        "requires_external_review": True,
        "speech_speed": 0.95,  # Slightly slower for clarity
    },
    "en-MY": {
        "name": "English (Malaysia)",
        "locale": "en-MY",
        "heygen_locale": "en-MY",
        "prompt_instruction": """Write in Malaysian English (Manglish style).
Use natural code-switching with Malay, Chinese, and Tamil words where appropriate.
Tone: Friendly and relatable, like chatting with a business mentor at the mamak.
Avoid: American idioms, overly formal language.

Example natural phrases:
- "Wah, this one really can help your business lah"
- "Don't play-play with cash flow ah"
- "This technology damn power one"
- "Eh, you must try this method"
""",
        "requires_external_review": False,
        "speech_speed": 1.0,
    },
}

# Supported languages list
SUPPORTED_LANGUAGES = list(LANGUAGE_CONFIGS.keys())

# Default language setting
DEFAULT_LANGUAGE = "en-SG"

# Target audience description for all prompts
TARGET_AUDIENCE = """Traditional Malaysian SME owners - kedai operators, F&B entrepreneurs,
neighborhood service providers, small retail shop owners, and local service businesses.
NOT corporate executives, tech startups, or multinational companies.

These are business owners who:
- Run family businesses or small operations with 1-20 employees
- May not be tech-savvy but are eager to learn practical skills
- Care about cash flow, customer relationships, and daily operations
- Need actionable advice, not theoretical frameworks
- Value authenticity and relate to local examples"""


def get_language_config(language_code: str) -> Dict[str, Any]:
    """Get language configuration by code.

    Args:
        language_code: Language code (e.g., 'en-SG', 'ms-MY')

    Returns:
        Language configuration dictionary
    """
    return LANGUAGE_CONFIGS.get(language_code, LANGUAGE_CONFIGS[DEFAULT_LANGUAGE])


def get_supported_languages() -> list:
    """Get list of supported language codes."""
    return list(LANGUAGE_CONFIGS.keys())


def get_language_choices() -> list:
    """Get list of language choices for UI/API.

    Returns:
        List of dicts with value and label for each language
    """
    return [
        {
            "value": code,
            "label": config["name"],
            "requires_review": config["requires_external_review"]
        }
        for code, config in LANGUAGE_CONFIGS.items()
    ]


def build_prompt_instruction(config: Dict[str, Any]) -> str:
    """Get prompt instruction from configuration.

    Args:
        config: Language configuration dictionary

    Returns:
        Prompt instruction string
    """
    return config.get("prompt_instruction", "")


def build_synthesis_prompt(
    language_code: str,
    segment_type: str,
    articles: list,
    additional_context: str = ""
) -> str:
    """Build a synthesis prompt with language-specific instructions.

    Args:
        language_code: Language code for the output
        segment_type: Type of segment (local_news, business, ai_tech)
        articles: List of article dictionaries to synthesize
        additional_context: Any additional context to include

    Returns:
        Complete prompt string for LLM
    """
    config = get_language_config(language_code)

    # Format articles for the prompt
    articles_text = ""
    for i, article in enumerate(articles, 1):
        title = article.get("title", "Untitled")
        content = article.get("content", article.get("summary", ""))[:500]
        source = article.get("source_name", "Unknown")
        articles_text += f"\n{i}. [{source}] {title}\n{content}\n"

    segment_instructions = {
        "local_news": "Focus on local developments that affect daily business operations.",
        "business": "Explain how these business trends impact small shop owners and service providers.",
        "ai_tech": "Make technology accessible - explain how SME owners can use these tools practically.",
        "general": "Provide practical insights that small business owners can apply today.",
    }

    segment_instruction = segment_instructions.get(segment_type, segment_instructions["general"])

    return f"""You are Maya, a professional AI news anchor for Malaysian small business owners.

{config['prompt_instruction']}

TARGET AUDIENCE:
{TARGET_AUDIENCE}

SEGMENT: {segment_type.upper().replace('_', ' ')}
{segment_instruction}

Focus on: What does this mean for a small business owner? What can they DO about it?

Articles to synthesize:
{articles_text}

{additional_context}

Output: 45-60 seconds of spoken content (~120-150 words)
Write in a conversational style as if speaking directly to the audience.
End with a practical tip or actionable takeaway."""


def build_intro_prompt(language_code: str, week_number: int, year: int) -> str:
    """Build intro prompt for the weekly briefing.

    Args:
        language_code: Language code for the output
        week_number: Week number
        year: Year

    Returns:
        Intro prompt string
    """
    config = get_language_config(language_code)

    return f"""You are Maya, a professional AI news anchor for Malaysian small business owners.

{config['prompt_instruction']}

Write a warm, engaging 15-20 second introduction for the Week {week_number}, {year} business news briefing.

Guidelines:
- Greet the audience warmly
- Briefly mention it's the weekly business update
- Create anticipation for what's coming
- Keep it conversational and friendly

Output: ~30-40 words of spoken content."""


def build_outro_prompt(language_code: str) -> str:
    """Build outro prompt for the weekly briefing.

    Args:
        language_code: Language code for the output

    Returns:
        Outro prompt string
    """
    config = get_language_config(language_code)

    return f"""You are Maya, a professional AI news anchor for Malaysian small business owners.

{config['prompt_instruction']}

Write a warm, encouraging 15-20 second closing for the weekly business news briefing.

Guidelines:
- Thank the audience for watching
- Encourage them to apply what they learned
- Remind them to tune in next week
- End on a positive, motivating note

Output: ~30-40 words of spoken content."""
