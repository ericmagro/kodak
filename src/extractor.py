"""Belief extraction using Claude API."""

import json
import anthropic
from typing import Optional

# Initialize client (will use ANTHROPIC_API_KEY env var)
client = anthropic.Anthropic()

EXTRACTION_PROMPT = """Analyze this message for beliefs, opinions, assumptions, and values expressed by the user.

For each belief found, extract:
1. statement: A clear, concise statement of the belief (reword if needed for clarity)
2. confidence: How confident they seem (0.0-1.0). Look for hedging language, certainty markers, etc.
3. source_type: Where this belief seems to come from:
   - "experience": Personal experience or observation
   - "reasoning": Logical deduction or analysis
   - "authority": Something they learned from others, experts, books, etc.
   - "intuition": Gut feeling, just seems true to them
   - "inherited": Cultural, familial, or social default
4. topics: 1-3 topic tags (lowercase, single words or short phrases)

Guidelines:
- Only extract genuine beliefs, opinions, values, or assumptions—not factual statements or descriptions
- "I had coffee today" is not a belief. "Coffee is essential for productivity" is.
- Look for underlying assumptions too. "I need to work harder" might assume "success comes from effort"
- If someone says "I think X but I'm not sure", that's a belief with low confidence
- Don't over-extract. Quality over quantity. 0-3 beliefs per message is typical.
- If there are no beliefs in the message, return an empty array.

IMPORTANT - Keep beliefs ATOMIC (single ideas):
- BAD: "Deep understanding of both the field and people is necessary for high-leverage work"
- GOOD: Split into two beliefs:
  1. "Deep technical knowledge is necessary for high-leverage work"
  2. "Understanding the people in a field is necessary for high-leverage work"
- Each belief should express ONE clear idea, not multiple ideas joined together
- Compound beliefs with "and", "both", "as well as" should usually be split

Return valid JSON only, no other text:
{
  "beliefs": [
    {
      "statement": "string",
      "confidence": 0.0-1.0,
      "source_type": "experience|reasoning|authority|intuition|inherited",
      "topics": ["topic1", "topic2"]
    }
  ],
  "reasoning": "Brief explanation of why you extracted these (or why none)"
}"""


async def extract_beliefs(
    message: str,
    conversation_context: list[dict] = None,
    existing_beliefs: list[dict] = None
) -> dict:
    """
    Extract beliefs from a message.

    Args:
        message: The user's message to analyze
        conversation_context: Recent conversation history for context
        existing_beliefs: User's existing beliefs to check for updates/contradictions

    Returns:
        Dict with 'beliefs' list and 'reasoning' explanation
    """
    context_str = ""
    if conversation_context:
        context_str = "\n\nRecent conversation context:\n"
        for msg in conversation_context[-10:]:
            role = "User" if msg["role"] == "user" else "Kodak"
            context_str += f"{role}: {msg['content']}\n"

    beliefs_str = ""
    if existing_beliefs:
        beliefs_str = "\n\nBeliefs already recorded for this user:\n"
        for b in existing_beliefs[:30]:
            beliefs_str += f"- {b['statement']}\n"
        beliefs_str += "\nAvoid re-extracting beliefs that are essentially the same. But do note if a new statement contradicts or updates an existing belief."

    full_prompt = f"""{EXTRACTION_PROMPT}
{context_str}
{beliefs_str}

Message to analyze:
\"\"\"{message}\"\"\""""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": full_prompt}]
        )

        # Parse the JSON response
        content = response.content[0].text

        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)
        return result

    except json.JSONDecodeError as e:
        return {"beliefs": [], "reasoning": f"Failed to parse extraction: {e}"}
    except anthropic.APIError as e:
        return {"beliefs": [], "reasoning": f"API error: {e}"}


async def generate_response(
    message: str,
    system_prompt: str,
    conversation_history: list[dict] = None
) -> str:
    """
    Generate a conversational response.

    Args:
        message: The user's message
        system_prompt: The full system prompt (including personality)
        conversation_history: Recent conversation history

    Returns:
        The assistant's response text
    """
    messages = []

    if conversation_history:
        for msg in conversation_history[-20:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    messages.append({"role": "user", "content": message})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text

    except anthropic.RateLimitError:
        return "Hmm, I need a quick breather—lots of good conversations happening right now. Try again in a moment?"

    except anthropic.APIConnectionError:
        return "I seem to have lost my train of thought for a second. Could you try that again?"

    except anthropic.APIError:
        return "My mind went blank there for a moment. Mind saying that again?"


async def find_belief_relations(
    new_belief: dict,
    existing_beliefs: list[dict]
) -> list[dict]:
    """
    Find relationships between a new belief and existing beliefs.

    Returns list of relation dicts with source_id, target_id, relation_type, strength
    """
    if not existing_beliefs:
        return []

    beliefs_list = "\n".join([
        f"[{b['id']}] {b['statement']}"
        for b in existing_beliefs[:30]
    ])

    prompt = f"""Given this new belief:
"{new_belief['statement']}"

And these existing beliefs:
{beliefs_list}

Identify any meaningful relationships between the new belief and existing ones.
Relationship types:
- supports: The new belief provides evidence/support for an existing one
- contradicts: The new belief is in tension with an existing one
- assumes: The new belief rests on an existing one as a foundation
- derives_from: The new belief is a logical consequence of an existing one
- relates_to: General topical relationship

Return valid JSON only:
{{
  "relations": [
    {{
      "target_id": "uuid of existing belief",
      "relation_type": "supports|contradicts|assumes|derives_from|relates_to",
      "strength": 0.0-1.0,
      "explanation": "brief explanation"
    }}
  ]
}}

Only include meaningful, clear relationships. Empty array is fine if none found."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.content[0].text
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)
        return result.get("relations", [])

    except (json.JSONDecodeError, anthropic.APIError):
        return []


async def summarize_beliefs(beliefs: list[dict], topic: str = None) -> str:
    """
    Generate a natural language summary of beliefs.

    Args:
        beliefs: List of belief dicts
        topic: Optional topic to focus on

    Returns:
        A readable summary string
    """
    if not beliefs:
        if topic:
            return f"No beliefs recorded about {topic} yet."
        return "No beliefs recorded yet."

    beliefs_text = "\n".join([
        f"- {b['statement']} (confidence: {b.get('confidence', 0.5):.0%}, source: {b.get('source_type', 'unknown')})"
        for b in beliefs
    ])

    topic_clause = f" about {topic}" if topic else ""

    prompt = f"""Summarize these beliefs{topic_clause} in a natural, readable way.
Don't just list them—synthesize them into a coherent picture of how this person thinks.
Note any patterns, themes, or interesting tensions.
Keep it concise (2-4 paragraphs max).

Beliefs:
{beliefs_text}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    except anthropic.APIError as e:
        # Fallback to simple list
        return "Your beliefs:\n" + "\n".join([f"- {b['statement']}" for b in beliefs])
