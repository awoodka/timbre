"""
Emotional dimensions configuration.

Each dimension describes a felt experience axis. Books are scored 0.0–1.0 on each.
This list is intentionally media-agnostic so it can extend to games, film, music, etc.
"""

EMOTIONAL_DIMENSIONS: list[dict] = [
    {
        "key": "isolation",
        "name": "Isolation / Solitude",
        "description": "The feeling of being alone, separated from others, or cut off from the world. Can be oppressive or liberating.",
    },
    {
        "key": "wonder",
        "name": "Wonder / Awe",
        "description": "A sense of amazement, discovery, or encountering something vast and incomprehensible. The feeling of the sublime.",
    },
    {
        "key": "dread",
        "name": "Dread / Unease",
        "description": "A creeping sense that something is wrong. Persistent anxiety, foreboding, or horror that builds slowly.",
    },
    {
        "key": "melancholy",
        "name": "Melancholy / Sadness",
        "description": "A gentle, pervasive sadness. Not sharp grief but a lingering emotional weight, often bittersweet.",
    },
    {
        "key": "warmth",
        "name": "Warmth / Comfort",
        "description": "Feeling safe, cared for, and emotionally held. Coziness, tenderness, and gentle affection.",
    },
    {
        "key": "tension",
        "name": "Tension / Suspense",
        "description": "Tightness and anticipation. The feeling of holding your breath, needing to know what happens next.",
    },
    {
        "key": "joy",
        "name": "Joy / Euphoria",
        "description": "Bursts of happiness, delight, or exhilaration. Moments that make you grin or feel your chest swell.",
    },
    {
        "key": "nostalgia",
        "name": "Nostalgia / Longing",
        "description": "Aching for something lost or past. A yearning for a time, place, or feeling that can't be recovered.",
    },
    {
        "key": "anger",
        "name": "Anger / Defiance",
        "description": "Rage, righteous fury, or rebellious energy. The urge to fight, resist, or tear something down.",
    },
    {
        "key": "serenity",
        "name": "Serenity / Peace",
        "description": "Deep calm and contentment. The feeling of everything being exactly as it should be, even briefly.",
    },
    {
        "key": "confusion",
        "name": "Confusion / Disorientation",
        "description": "Not understanding what's happening or what's real. Feeling lost, unmoored, or questioning your perception.",
    },
    {
        "key": "empowerment",
        "name": "Empowerment / Triumph",
        "description": "Feeling capable, victorious, or unstoppable. The thrill of overcoming, mastering, or rising above.",
    },
    {
        "key": "vulnerability",
        "name": "Vulnerability / Exposure",
        "description": "Feeling emotionally naked, unprotected, or raw. The sensation of being seen in a way that's uncomfortable.",
    },
    {
        "key": "absurdity",
        "name": "Absurdity / Dark Humor",
        "description": "The feeling that things are ridiculous, meaningless, or darkly funny. Laughter at the cosmic joke.",
    },
    {
        "key": "intimacy",
        "name": "Intimacy / Connection",
        "description": "Deep emotional closeness with another person or character. Feeling truly known and understanding someone else.",
    },
    {
        "key": "alienation",
        "name": "Alienation / Otherness",
        "description": "Feeling fundamentally different, misunderstood, or not belonging. The experience of being an outsider.",
    },
    {
        "key": "obsession",
        "name": "Obsession / Fixation",
        "description": "Being consumed by something — a person, idea, or mystery. The inability to let go or look away.",
    },
    {
        "key": "grief",
        "name": "Grief / Loss",
        "description": "The sharp, heavy pain of losing something or someone irreplaceable. Mourning and its aftermath.",
    },
    {
        "key": "hope",
        "name": "Hope / Resilience",
        "description": "The belief that things can get better, even against the odds. Quiet determination or bright optimism.",
    },
    {
        "key": "claustrophobia",
        "name": "Claustrophobia / Entrapment",
        "description": "Feeling trapped, cornered, or unable to escape. Physical or psychological confinement closing in.",
    },
    {
        "key": "vastness",
        "name": "Vastness / Cosmic Scale",
        "description": "Awareness of immense scale — of time, space, or existence. Feeling tiny against something enormous.",
    },
    {
        "key": "sensuality",
        "name": "Sensuality / Physicality",
        "description": "Heightened awareness of the body and senses. Textures, tastes, physical presence, desire, and embodiment.",
    },
    {
        "key": "moral_ambiguity",
        "name": "Moral Ambiguity / Unease",
        "description": "The discomfort of no clear right answer. Ethical gray zones where every choice has a cost.",
    },
    {
        "key": "frenetic_energy",
        "name": "Frenetic Energy / Chaos",
        "description": "Breathless pace, sensory overload, or manic intensity. The feeling of everything happening at once.",
    },
    {
        "key": "stillness",
        "name": "Stillness / Contemplation",
        "description": "Quiet, reflective moments. The feeling of time slowing down, of sitting with a thought or image.",
    },
    # --- Structural / Experiential Dimensions ---
    {
        "key": "pacing",
        "name": "Pacing",
        "description": "How fast the experience moves. 0.0 = glacially slow, meditative, lingering. 1.0 = breathless, relentless, no room to breathe.",
    },
    {
        "key": "emotional_complexity",
        "name": "Emotional Complexity",
        "description": "Whether the experience evokes a single clear emotion or many conflicting emotions simultaneously. 0.0 = one dominant feeling. 1.0 = layered, contradictory feelings at the same time.",
    },
    {
        "key": "predictability",
        "name": "Predictability / Surprise",
        "description": "Whether you can see what's coming or are constantly caught off guard. 0.0 = everything is telegraphed, the dread of knowing. 1.0 = constant twists and shocks, nothing expected.",
    },
    {
        "key": "catharsis",
        "name": "Catharsis / Resolution",
        "description": "Whether the experience provides emotional release or leaves you unresolved. 0.0 = raw, open wound, no closure. 1.0 = full emotional release, satisfaction, healing.",
    },
]

DIMENSION_KEYS = [d["key"] for d in EMOTIONAL_DIMENSIONS]
NUM_DIMENSIONS = len(EMOTIONAL_DIMENSIONS)
