"""Belief and value extraction for Kodak v2.

Extends v1 extraction to also tag beliefs with Schwartz values.
"""

import json
import logging
import anthropic
from typing import Optional
from dataclasses import dataclass

from client import create_message
from values import ALL_VALUES, VALUE_DEFINITIONS

logger = logging.getLogger('kodak')


# ============================================
# EXTRACTION PROMPT
# ============================================

EXTRACTION_PROMPT = """Analyze this journal entry for beliefs, opinions, assumptions, and values expressed by the user.

For each belief found, extract:
1. statement: A clear, concise statement of the belief (reword if needed for clarity)
2. confidence: How confident they seem (0.0-1.0). Look for hedging language, certainty markers.
3. source_type: Where this belief seems to come from:
   - "experience": Personal experience or observation
   - "reasoning": Logical deduction or analysis
   - "authority": Something learned from others, experts, books
   - "intuition": Gut feeling, just seems true
   - "inherited": Cultural, familial, or social default
4. topics: 1-3 topic tags (lowercase, single words or short phrases)
5. values: 0-3 Schwartz Basic Human Values this belief reflects, with mapping confidence

The 10 Schwartz values are:
- universalism: tolerance, social justice, equality, protecting nature
- benevolence: helpfulness, honesty, loyalty to close others
- tradition: respect for customs, humility, devotion
- conformity: obedience, self-discipline, politeness
- security: safety, stability, social order
- achievement: success, competence, ambition
- power: authority, wealth, social recognition
- self_direction: creativity, freedom, independence
- stimulation: excitement, novelty, challenge
- hedonism: pleasure, enjoying life

Guidelines:
- Only extract genuine beliefs, opinions, values, or assumptions
- "I had coffee today" is not a belief. "Coffee is essential for productivity" is.
- Look for underlying assumptions. "I need to work harder" assumes "effort leads to success"
- Keep beliefs ATOMIC (single ideas). Split compound beliefs.
- Quality over quantity. 0-3 beliefs per message is typical.
- Not every belief maps to a value. If unclear, use empty values array.
- mapping_confidence: How clearly this belief indicates the value (0.0-1.0)
  - 1.0: "I believe in equality for all" clearly maps to universalism
  - 0.6: "I like exploring new places" moderately suggests stimulation
  - Don't force low-confidence mappings; better to skip them

Return valid JSON only:
{
  "beliefs": [
    {
      "statement": "string",
      "confidence": 0.0-1.0,
      "source_type": "experience|reasoning|authority|intuition|inherited",
      "topics": ["topic1", "topic2"],
      "values": [
        {"name": "value_name", "weight": 1.0, "mapping_confidence": 0.8}
      ]
    }
  ],
  "reasoning": "Brief explanation of extractions"
}"""


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class ExtractedValue:
    """A value tagged to a belief."""
    name: str
    weight: float  # 1.0 = primary, 0.5 = secondary
    mapping_confidence: float


@dataclass
class ExtractedBelief:
    """A belief extracted from conversation."""
    statement: str
    confidence: float
    source_type: str
    topics: list[str]
    values: list[ExtractedValue]

    def to_dict(self) -> dict:
        return {
            'statement': self.statement,
            'confidence': self.confidence,
            'source_type': self.source_type,
            'topics': self.topics,
            'values': [
                {'name': v.name, 'weight': v.weight, 'mapping_confidence': v.mapping_confidence}
                for v in self.values
            ]
        }


@dataclass
class ExtractionResult:
    """Result of extraction from a message."""
    beliefs: list[ExtractedBelief]
    reasoning: str

    def has_beliefs(self) -> bool:
        return len(self.beliefs) > 0


# ============================================
# EXTRACTION FUNCTIONS
# ============================================

async def extract_beliefs_and_values(
    message: str,
    conversation_context: list[dict] = None,
    existing_beliefs: list[dict] = None
) -> ExtractionResult:
    """
    Extract beliefs and their associated values from a message.

    Args:
        message: The user's message to analyze
        conversation_context: Recent conversation history for context
        existing_beliefs: User's existing beliefs to avoid duplicates

    Returns:
        ExtractionResult with beliefs and reasoning
    """
    # Build context string
    context_str = ""
    if conversation_context:
        context_str = "\n\nRecent conversation:\n"
        for msg in conversation_context[-6:]:
            role = "User" if msg.get("role") == "user" else "Kodak"
            context_str += f"{role}: {msg.get('content', '')}\n"

    # Build existing beliefs context
    beliefs_str = ""
    if existing_beliefs:
        beliefs_str = "\n\nExisting beliefs (avoid duplicates):\n"
        for b in existing_beliefs[:20]:
            beliefs_str += f"- {b.get('statement', '')}\n"

    full_prompt = f"""{EXTRACTION_PROMPT}
{context_str}
{beliefs_str}

Message to analyze:
\"\"\"{message}\"\"\""""

    try:
        content = create_message(
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=1024
        )

        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)
        return _parse_extraction_result(result)

    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse extraction response: {e}")
        return ExtractionResult(beliefs=[], reasoning=f"Parse error: {e}")
    except anthropic.APIError as e:
        logger.error(f"API error during extraction: {e}")
        return ExtractionResult(beliefs=[], reasoning=f"API error: {e}")
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return ExtractionResult(beliefs=[], reasoning=f"Error: {e}")


def _parse_extraction_result(raw: dict) -> ExtractionResult:
    """Parse raw JSON into structured ExtractionResult."""
    beliefs = []

    for b in raw.get("beliefs", []):
        # Parse values
        values = []
        for v in b.get("values", []):
            name = v.get("name", "").lower().replace("-", "_").replace(" ", "_")
            # Validate it's a real Schwartz value
            if name in ALL_VALUES:
                values.append(ExtractedValue(
                    name=name,
                    weight=float(v.get("weight", 1.0)),
                    mapping_confidence=float(v.get("mapping_confidence", 0.5))
                ))

        # Only include values with reasonable confidence
        values = [v for v in values if v.mapping_confidence >= 0.4]

        beliefs.append(ExtractedBelief(
            statement=b.get("statement", ""),
            confidence=float(b.get("confidence", 0.5)),
            source_type=b.get("source_type", "experience"),
            topics=b.get("topics", []),
            values=values[:3]  # Max 3 values per belief
        ))

    return ExtractionResult(
        beliefs=beliefs,
        reasoning=raw.get("reasoning", "")
    )


# ============================================
# BATCH EXTRACTION (for session close)
# ============================================

async def extract_from_session(
    messages: list[dict],
    existing_beliefs: list[dict] = None
) -> ExtractionResult:
    """
    Extract beliefs from an entire session's messages.

    This is called at session close to do a final extraction pass.
    """
    # Combine user messages for analysis
    user_messages = [
        msg.get('content', '')
        for msg in messages
        if msg.get('role') == 'user'
    ]

    if not user_messages:
        return ExtractionResult(beliefs=[], reasoning="No user messages")

    combined = "\n\n".join(user_messages)

    return await extract_beliefs_and_values(
        message=combined,
        conversation_context=messages,
        existing_beliefs=existing_beliefs
    )


# ============================================
# STANDALONE VALUE TAGGING
# ============================================

async def tag_belief_with_values(
    belief_statement: str,
    belief_context: str = None
) -> list[ExtractedValue]:
    """
    Tag an existing belief with Schwartz values.

    Use this for beliefs extracted without values, or for re-tagging.
    """
    prompt = f"""Analyze this belief statement and identify which Schwartz Basic Human Values it reflects.

The 10 Schwartz values:
- universalism: tolerance, social justice, equality, protecting nature
- benevolence: helpfulness, honesty, loyalty to close others
- tradition: respect for customs, humility, devotion
- conformity: obedience, self-discipline, politeness
- security: safety, stability, social order
- achievement: success, competence, ambition
- power: authority, wealth, social recognition
- self_direction: creativity, freedom, independence
- stimulation: excitement, novelty, challenge
- hedonism: pleasure, enjoying life

Belief: "{belief_statement}"
{f'Context: {belief_context}' if belief_context else ''}

Return 0-3 values this belief most clearly reflects. Only include values where the mapping is reasonably clear.

Return JSON only:
{{
  "values": [
    {{"name": "value_name", "weight": 1.0, "mapping_confidence": 0.8}}
  ]
}}"""

    try:
        content = create_message(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=256
        )

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)

        values = []
        for v in result.get("values", []):
            name = v.get("name", "").lower().replace("-", "_").replace(" ", "_")
            if name in ALL_VALUES:
                values.append(ExtractedValue(
                    name=name,
                    weight=float(v.get("weight", 1.0)),
                    mapping_confidence=float(v.get("mapping_confidence", 0.5))
                ))

        return [v for v in values if v.mapping_confidence >= 0.4][:3]

    except Exception as e:
        logger.warning(f"Failed to tag belief with values: {e}")
        return []


# ============================================
# UTILITIES
# ============================================

def format_belief_for_display(belief: ExtractedBelief) -> str:
    """Format a belief for user display."""
    return f"*\"{belief.statement}\"*"


def format_beliefs_for_close(beliefs: list[ExtractedBelief], max_display: int = 2) -> str:
    """Format extracted beliefs for session close display."""
    if not beliefs:
        return ""

    # Take most confident beliefs
    sorted_beliefs = sorted(beliefs, key=lambda b: b.confidence, reverse=True)
    to_display = sorted_beliefs[:max_display]

    if len(to_display) == 1:
        return f"I noticed something worth remembering:\n{format_belief_for_display(to_display[0])}"
    else:
        lines = ["I noticed a couple things worth remembering:"]
        for b in to_display:
            lines.append(format_belief_for_display(b))
        return "\n".join(lines)
