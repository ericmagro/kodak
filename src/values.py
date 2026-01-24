"""Schwartz Basic Human Values framework for Kodak v2."""

from dataclasses import dataclass
from typing import Optional
import math
import json
from datetime import datetime

# ============================================
# SCHWARTZ'S 10 BASIC HUMAN VALUES
# ============================================

# Higher-order dimensions
SELF_TRANSCENDENCE = "self_transcendence"
CONSERVATION = "conservation"
SELF_ENHANCEMENT = "self_enhancement"
OPENNESS_TO_CHANGE = "openness_to_change"

# The 10 values
UNIVERSALISM = "universalism"
BENEVOLENCE = "benevolence"
TRADITION = "tradition"
CONFORMITY = "conformity"
SECURITY = "security"
ACHIEVEMENT = "achievement"
POWER = "power"
SELF_DIRECTION = "self_direction"
STIMULATION = "stimulation"
HEDONISM = "hedonism"

# All values list
ALL_VALUES = [
    UNIVERSALISM, BENEVOLENCE, TRADITION, CONFORMITY, SECURITY,
    ACHIEVEMENT, POWER, SELF_DIRECTION, STIMULATION, HEDONISM
]

# Value definitions with keywords for extraction hints
VALUE_DEFINITIONS = {
    UNIVERSALISM: {
        "name": "Universalism",
        "dimension": SELF_TRANSCENDENCE,
        "description": "Tolerance, social justice, equality, protecting nature",
        "keywords": [
            "equality", "justice", "fairness", "environment", "nature",
            "tolerance", "peace", "diversity", "humanity", "world",
            "rights", "inclusive", "everyone", "society", "global"
        ]
    },
    BENEVOLENCE: {
        "name": "Benevolence",
        "dimension": SELF_TRANSCENDENCE,
        "description": "Helpfulness, honesty, loyalty to those close to you",
        "keywords": [
            "help", "honest", "loyal", "friend", "family", "care",
            "support", "trust", "kind", "generous", "love", "close",
            "relationship", "community", "giving"
        ]
    },
    TRADITION: {
        "name": "Tradition",
        "dimension": CONSERVATION,
        "description": "Respect for customs, humility, devotion",
        "keywords": [
            "tradition", "custom", "culture", "heritage", "religion",
            "respect", "humble", "devout", "ancestors", "ritual",
            "history", "values", "passed down", "roots"
        ]
    },
    CONFORMITY: {
        "name": "Conformity",
        "dimension": CONSERVATION,
        "description": "Obedience, self-discipline, politeness",
        "keywords": [
            "rules", "obey", "discipline", "polite", "proper",
            "behave", "respect", "manners", "appropriate", "norm",
            "expectations", "fit in", "follow"
        ]
    },
    SECURITY: {
        "name": "Security",
        "dimension": CONSERVATION,
        "description": "Safety, stability, social order",
        "keywords": [
            "safe", "secure", "stable", "protect", "order",
            "certain", "reliable", "predictable", "risk", "careful",
            "plan", "insurance", "steady", "consistent"
        ]
    },
    ACHIEVEMENT: {
        "name": "Achievement",
        "dimension": SELF_ENHANCEMENT,
        "description": "Success, competence, ambition",
        "keywords": [
            "success", "achieve", "accomplish", "goal", "ambition",
            "competent", "excel", "best", "win", "perform",
            "capable", "skill", "master", "improve", "hard work"
        ]
    },
    POWER: {
        "name": "Power",
        "dimension": SELF_ENHANCEMENT,
        "description": "Authority, wealth, social recognition",
        "keywords": [
            "power", "authority", "control", "influence", "wealth",
            "status", "prestige", "recognition", "leader", "dominant",
            "money", "rich", "important", "respect"
        ]
    },
    SELF_DIRECTION: {
        "name": "Self-Direction",
        "dimension": OPENNESS_TO_CHANGE,
        "description": "Creativity, freedom, independence",
        "keywords": [
            "freedom", "independent", "autonomy", "choice", "creative",
            "curious", "explore", "own way", "decide", "self",
            "unique", "original", "think for myself"
        ]
    },
    STIMULATION: {
        "name": "Stimulation",
        "dimension": OPENNESS_TO_CHANGE,
        "description": "Excitement, novelty, challenge",
        "keywords": [
            "exciting", "adventure", "new", "challenge", "thrill",
            "variety", "change", "different", "risk", "daring",
            "spontaneous", "bold", "interesting"
        ]
    },
    HEDONISM: {
        "name": "Hedonism",
        # Note: Hedonism is a bridge value between Self-Enhancement and Openness to Change
        "dimension": OPENNESS_TO_CHANGE,
        "description": "Pleasure, enjoying life",
        "keywords": [
            "pleasure", "enjoy", "fun", "happy", "comfort",
            "relax", "indulge", "treat", "satisfy", "leisure",
            "good life", "experience", "feel good"
        ]
    }
}

# Higher-order dimension groupings
DIMENSION_VALUES = {
    SELF_TRANSCENDENCE: [UNIVERSALISM, BENEVOLENCE],
    CONSERVATION: [TRADITION, CONFORMITY, SECURITY],
    SELF_ENHANCEMENT: [ACHIEVEMENT, POWER],
    OPENNESS_TO_CHANGE: [SELF_DIRECTION, STIMULATION, HEDONISM]
}

DIMENSION_NAMES = {
    SELF_TRANSCENDENCE: "Self-Transcendence",
    CONSERVATION: "Conservation",
    SELF_ENHANCEMENT: "Self-Enhancement",
    OPENNESS_TO_CHANGE: "Openness to Change"
}


# ============================================
# VALUE PROFILE
# ============================================

@dataclass
class ValueScore:
    """A single value score with metadata."""
    value_name: str
    raw_score: float
    normalized_score: float
    belief_count: int
    last_updated: Optional[str] = None

    @property
    def display_name(self) -> str:
        return VALUE_DEFINITIONS.get(self.value_name, {}).get("name", self.value_name)

    @property
    def dimension(self) -> str:
        return VALUE_DEFINITIONS.get(self.value_name, {}).get("dimension", "unknown")


@dataclass
class ValueProfile:
    """Complete value profile for a user."""
    user_id: str
    scores: dict[str, ValueScore]
    last_updated: Optional[str] = None

    def get_top_values(self, n: int = 3) -> list[ValueScore]:
        """Get the top N values by normalized score."""
        sorted_scores = sorted(
            self.scores.values(),
            key=lambda v: v.normalized_score,
            reverse=True
        )
        return sorted_scores[:n]

    def get_low_values(self, n: int = 3) -> list[ValueScore]:
        """Get the bottom N values by normalized score."""
        sorted_scores = sorted(
            self.scores.values(),
            key=lambda v: v.normalized_score
        )
        return sorted_scores[:n]

    def get_dimension_scores(self) -> dict[str, float]:
        """Get average scores by higher-order dimension."""
        dimension_scores = {}
        for dim, values in DIMENSION_VALUES.items():
            dim_values = [self.scores[v].normalized_score for v in values if v in self.scores]
            if dim_values:
                dimension_scores[dim] = sum(dim_values) / len(dim_values)
            else:
                dimension_scores[dim] = 0.0
        return dimension_scores


# ============================================
# TEMPORAL DECAY
# ============================================

# Half-life in days (belief from 90 days ago has half the weight)
TEMPORAL_HALF_LIFE_DAYS = 90


def calculate_temporal_weight(days_ago: float) -> float:
    """
    Calculate temporal decay weight for a belief.

    Uses exponential decay with configurable half-life.
    A belief from TEMPORAL_HALF_LIFE_DAYS ago has weight 0.5.
    """
    if days_ago <= 0:
        return 1.0
    return math.pow(0.5, days_ago / TEMPORAL_HALF_LIFE_DAYS)


def days_since(timestamp_str: str) -> float:
    """Calculate days since a timestamp string."""
    try:
        if 'T' in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(timestamp_str)
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        delta = now - dt
        return delta.total_seconds() / (24 * 60 * 60)
    except (ValueError, TypeError):
        return 0.0


# ============================================
# VALUE DERIVATION
# ============================================

@dataclass
class BeliefValueMapping:
    """Mapping from a belief to values."""
    belief_id: str
    belief_statement: str
    belief_confidence: float
    belief_timestamp: str
    values: list[tuple[str, float, float]]  # (value_name, weight, mapping_confidence)


def calculate_belief_contribution(
    belief_confidence: float,
    mapping_confidence: float,
    weight: float,
    days_ago: float
) -> float:
    """
    Calculate a belief's contribution to a value score.

    contribution = belief_confidence × mapping_confidence × weight × temporal_decay
    """
    temporal_weight = calculate_temporal_weight(days_ago)
    return belief_confidence * mapping_confidence * weight * temporal_weight


def normalize_value_scores(raw_scores: dict[str, float]) -> dict[str, float]:
    """
    Normalize value scores relative to user's own max.

    The strongest value becomes 1.0, others scale proportionally.
    """
    if not raw_scores:
        return {}

    max_score = max(raw_scores.values())
    if max_score == 0:
        return {k: 0.0 for k in raw_scores}

    return {k: v / max_score for k, v in raw_scores.items()}


def aggregate_value_profile(
    belief_mappings: list[BeliefValueMapping]
) -> dict[str, tuple[float, float, int]]:
    """
    Aggregate belief-value mappings into a value profile.

    Returns dict of value_name -> (raw_score, normalized_score, belief_count)
    """
    raw_scores: dict[str, float] = {v: 0.0 for v in ALL_VALUES}
    belief_counts: dict[str, int] = {v: 0 for v in ALL_VALUES}

    for mapping in belief_mappings:
        days_ago = days_since(mapping.belief_timestamp)

        for value_name, weight, mapping_confidence in mapping.values:
            if value_name in raw_scores:
                contribution = calculate_belief_contribution(
                    mapping.belief_confidence,
                    mapping_confidence,
                    weight,
                    days_ago
                )
                raw_scores[value_name] += contribution
                belief_counts[value_name] += 1

    normalized = normalize_value_scores(raw_scores)

    return {
        v: (raw_scores[v], normalized.get(v, 0.0), belief_counts[v])
        for v in ALL_VALUES
    }


# ============================================
# NARRATIVE GENERATION
# ============================================

def generate_value_narrative(profile: ValueProfile) -> str:
    """
    Generate a narrative description of a user's value profile.

    This is what users see when they run /values.
    """
    top_values = profile.get_top_values(3)
    low_values = profile.get_low_values(2)

    if not top_values or all(v.normalized_score == 0 for v in top_values):
        return (
            "I don't have enough information yet to describe your values.\n\n"
            "Keep journaling, and patterns will emerge over time."
        )

    lines = ["**What you seem to value most:**\n"]

    for i, value in enumerate(top_values):
        if value.normalized_score < 0.3:
            continue

        definition = VALUE_DEFINITIONS.get(value.value_name, {})
        description = definition.get("description", "")

        if i == 0:
            lines.append(
                f"You often come back to themes of **{value.display_name.lower()}** — "
                f"{description.lower()}.\n"
            )
        else:
            lines.append(
                f"**{value.display_name}** also matters to you — {description.lower()}.\n"
            )

    # Add contrast with low values if there's enough data
    meaningful_lows = [v for v in low_values if v.normalized_score < 0.3 and v.belief_count > 0]
    if meaningful_lows and top_values[0].normalized_score > 0.5:
        low_value = meaningful_lows[0]
        lines.append(
            f"\nYou show less emphasis on **{low_value.display_name.lower()}** — "
            f"this doesn't come up as often in what you share."
        )

    return "\n".join(lines)


def generate_value_change_narrative(
    current_profile: ValueProfile,
    previous_profile: ValueProfile,
    period_description: str = "the past month"
) -> Optional[str]:
    """
    Generate narrative about how values have shifted.

    Returns None if no significant changes.
    """
    SIGNIFICANCE_THRESHOLD = 0.15
    changes = []

    for value_name in ALL_VALUES:
        current = current_profile.scores.get(value_name)
        previous = previous_profile.scores.get(value_name)

        if not current or not previous:
            continue

        diff = current.normalized_score - previous.normalized_score

        if abs(diff) >= SIGNIFICANCE_THRESHOLD:
            changes.append((value_name, diff, current.display_name))

    if not changes:
        return None

    lines = [f"**How your values are shifting ({period_description}):**\n"]

    # Sort by absolute change
    changes.sort(key=lambda x: abs(x[1]), reverse=True)

    for value_name, diff, display_name in changes[:3]:
        if diff > 0:
            lines.append(
                f"Your emphasis on **{display_name.lower()}** has increased. "
                f"Recent entries mention these themes more than before.\n"
            )
        else:
            lines.append(
                f"**{display_name}** has decreased slightly — "
                f"fewer mentions compared to before.\n"
            )

    return "\n".join(lines)


# ============================================
# COMPARISON
# ============================================

@dataclass
class ValueComparison:
    """Comparison between two value profiles."""
    user_a_id: str
    user_b_id: str
    overall_similarity: float  # 0.0 to 1.0
    shared_top_values: list[str]
    key_differences: list[tuple[str, float, float]]  # (value, score_a, score_b)
    complementary_values: list[str]  # Values one has high, other has low


def compare_value_profiles(
    profile_a: ValueProfile,
    profile_b: ValueProfile
) -> ValueComparison:
    """
    Compare two value profiles.

    Returns similarity score and analysis of shared/different values.
    """
    # Calculate cosine similarity of normalized scores
    scores_a = [profile_a.scores.get(v, ValueScore(v, 0, 0, 0)).normalized_score for v in ALL_VALUES]
    scores_b = [profile_b.scores.get(v, ValueScore(v, 0, 0, 0)).normalized_score for v in ALL_VALUES]

    dot_product = sum(a * b for a, b in zip(scores_a, scores_b))
    magnitude_a = math.sqrt(sum(a * a for a in scores_a))
    magnitude_b = math.sqrt(sum(b * b for b in scores_b))

    if magnitude_a == 0 or magnitude_b == 0:
        similarity = 0.0
    else:
        similarity = dot_product / (magnitude_a * magnitude_b)

    # Find shared top values
    top_a = {v.value_name for v in profile_a.get_top_values(3)}
    top_b = {v.value_name for v in profile_b.get_top_values(3)}
    shared_top = list(top_a & top_b)

    # Find key differences (high for one, low for other)
    differences = []
    complementary = []

    for value_name in ALL_VALUES:
        score_a = profile_a.scores.get(value_name, ValueScore(value_name, 0, 0, 0)).normalized_score
        score_b = profile_b.scores.get(value_name, ValueScore(value_name, 0, 0, 0)).normalized_score

        diff = abs(score_a - score_b)
        if diff > 0.3:
            differences.append((value_name, score_a, score_b))

            # Check if complementary (one high, one low)
            if (score_a > 0.6 and score_b < 0.3) or (score_b > 0.6 and score_a < 0.3):
                complementary.append(value_name)

    differences.sort(key=lambda x: abs(x[1] - x[2]), reverse=True)

    return ValueComparison(
        user_a_id=profile_a.user_id,
        user_b_id=profile_b.user_id,
        overall_similarity=similarity,
        shared_top_values=shared_top,
        key_differences=differences[:5],
        complementary_values=complementary
    )


def generate_comparison_narrative(comparison: ValueComparison) -> str:
    """Generate narrative description of a value comparison."""
    lines = []

    # Overall similarity
    if comparison.overall_similarity > 0.8:
        lines.append("**Very similar value profiles.** You prioritize many of the same things.\n")
    elif comparison.overall_similarity > 0.6:
        lines.append("**Fairly aligned.** You share some core values with notable differences.\n")
    elif comparison.overall_similarity > 0.4:
        lines.append("**Mixed alignment.** You have some common ground but different priorities.\n")
    else:
        lines.append("**Different priorities.** Your value profiles diverge significantly.\n")

    # Shared top values
    if comparison.shared_top_values:
        shared_names = [VALUE_DEFINITIONS[v]["name"] for v in comparison.shared_top_values]
        lines.append(f"**Shared priorities:** {', '.join(shared_names)}\n")

    # Key differences
    if comparison.key_differences:
        lines.append("\n**Notable differences:**")
        for value_name, score_a, score_b in comparison.key_differences[:3]:
            name = VALUE_DEFINITIONS[value_name]["name"]
            if score_a > score_b:
                lines.append(f"- You emphasize **{name}** more")
            else:
                lines.append(f"- They emphasize **{name}** more")

    return "\n".join(lines)


# ============================================
# EXPORT / IMPORT (File-Based Sharing)
# ============================================

# Export schema version for forwards compatibility
EXPORT_SCHEMA_VERSION = "1.0"


@dataclass
class ExportedValueProfile:
    """A value profile packaged for sharing."""
    display_name: str  # How the sharer wants to be identified
    exported_at: str
    schema_version: str
    values: dict[str, float]  # value_name -> normalized_score
    included_beliefs: list[str]  # Optional list of belief statements shared
    dimension_scores: dict[str, float]  # Higher-order dimension averages


def create_export_data(
    profile: ValueProfile,
    display_name: str,
    included_values: list[str] = None,
    included_beliefs: list[str] = None
) -> dict:
    """
    Create export data from a value profile.

    Args:
        profile: The user's value profile
        display_name: How the user wants to be identified in the export
        included_values: Which values to include (None = all)
        included_beliefs: Optional list of belief statements to include

    Returns:
        Dictionary ready for JSON export
    """
    # Filter values if specified
    if included_values is None:
        included_values = ALL_VALUES

    values_dict = {}
    for value_name in included_values:
        score = profile.scores.get(value_name)
        if score:
            values_dict[value_name] = round(score.normalized_score, 3)

    # Calculate dimension scores for included values only
    dimension_scores = {}
    for dim, dim_values in DIMENSION_VALUES.items():
        included_dim_values = [v for v in dim_values if v in included_values]
        if included_dim_values:
            dim_total = sum(
                profile.scores.get(v, ValueScore(v, 0, 0, 0)).normalized_score
                for v in included_dim_values
            )
            dimension_scores[dim] = round(dim_total / len(included_dim_values), 3)

    return {
        "kodak_export": True,
        "schema_version": EXPORT_SCHEMA_VERSION,
        "display_name": display_name,
        "exported_at": datetime.now().isoformat(),
        "values": values_dict,
        "dimension_scores": dimension_scores,
        "included_beliefs": included_beliefs or []
    }


def export_to_json(
    profile: ValueProfile,
    display_name: str,
    included_values: list[str] = None,
    included_beliefs: list[str] = None
) -> str:
    """Export a value profile as JSON string."""
    data = create_export_data(profile, display_name, included_values, included_beliefs)
    return json.dumps(data, indent=2)


def parse_import_data(json_str: str) -> Optional[ExportedValueProfile]:
    """
    Parse and validate imported value profile data.

    Returns None if invalid.
    """
    try:
        data = json.loads(json_str)

        # Validate it's a Kodak export
        if not data.get("kodak_export"):
            return None

        # Validate schema version
        schema = data.get("schema_version", "1.0")
        if not schema.startswith("1."):
            # Future-proof: only accept 1.x versions
            return None

        # Validate required fields
        if "values" not in data or "display_name" not in data:
            return None

        # Validate value names
        values = data["values"]
        for value_name in values.keys():
            if value_name not in ALL_VALUES:
                # Skip unknown values (forwards compatibility)
                pass

        return ExportedValueProfile(
            display_name=data["display_name"],
            exported_at=data.get("exported_at", ""),
            schema_version=schema,
            values={k: v for k, v in values.items() if k in ALL_VALUES},
            included_beliefs=data.get("included_beliefs", []),
            dimension_scores=data.get("dimension_scores", {})
        )

    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def imported_to_profile(imported: ExportedValueProfile) -> ValueProfile:
    """Convert an imported profile to a ValueProfile for comparison."""
    scores = {}
    for value_name, score in imported.values.items():
        scores[value_name] = ValueScore(
            value_name=value_name,
            raw_score=0.0,  # Not available from import
            normalized_score=score,
            belief_count=0,  # Not available from import
            last_updated=imported.exported_at
        )

    # Fill in missing values with zeros
    for value_name in ALL_VALUES:
        if value_name not in scores:
            scores[value_name] = ValueScore(
                value_name=value_name,
                raw_score=0.0,
                normalized_score=0.0,
                belief_count=0
            )

    return ValueProfile(
        user_id=f"imported:{imported.display_name}",
        scores=scores,
        last_updated=imported.exported_at
    )


def generate_comparison_with_import_narrative(
    your_profile: ValueProfile,
    imported: ExportedValueProfile
) -> str:
    """
    Generate comparison narrative between your profile and an imported one.

    This is the main function for /compare-file display.
    """
    # Convert import to profile for comparison
    their_profile = imported_to_profile(imported)
    comparison = compare_value_profiles(your_profile, their_profile)

    lines = [f"**Comparing your values with {imported.display_name}**\n"]

    # Overall alignment
    similarity_pct = int(comparison.overall_similarity * 100)
    if comparison.overall_similarity > 0.8:
        lines.append(f"**{similarity_pct}% aligned** — You prioritize very similar things.\n")
    elif comparison.overall_similarity > 0.6:
        lines.append(f"**{similarity_pct}% aligned** — You share core values with some differences.\n")
    elif comparison.overall_similarity > 0.4:
        lines.append(f"**{similarity_pct}% aligned** — Some common ground, but different priorities.\n")
    else:
        lines.append(f"**{similarity_pct}% aligned** — Your priorities are quite different.\n")

    # Shared top values
    if comparison.shared_top_values:
        shared_names = [VALUE_DEFINITIONS[v]["name"] for v in comparison.shared_top_values]
        lines.append(f"**You both prioritize:** {', '.join(shared_names)}\n")

    # Your unique priorities
    your_top = set(v.value_name for v in your_profile.get_top_values(3) if v.normalized_score > 0.5)
    their_top = set(v for v, s in imported.values.items() if s > 0.5)

    your_unique = your_top - their_top
    their_unique = their_top - your_top

    if your_unique:
        unique_names = [VALUE_DEFINITIONS[v]["name"] for v in your_unique]
        lines.append(f"**You emphasize more:** {', '.join(unique_names)}")

    if their_unique:
        unique_names = [VALUE_DEFINITIONS[v]["name"] for v in their_unique]
        lines.append(f"**They emphasize more:** {', '.join(unique_names)}")

    # Show their shared beliefs if any
    if imported.included_beliefs:
        lines.append(f"\n**Some beliefs they shared:**")
        for belief in imported.included_beliefs[:3]:
            lines.append(f"• *\"{belief[:80]}{'...' if len(belief) > 80 else ''}\"*")

    return "\n".join(lines)
