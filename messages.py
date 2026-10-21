"""Everything the pet can say, grouped by situation and personality.

Lines may use {name} and {level}. Add as many as you like: the game picks one
at random. Personality lines are mixed in with the common ones, and are a bit
more likely to be picked so each personality feels different.
"""

import random

PERSONALITIES = ("cheerful", "playful", "foodie", "sleepy", "shy")

COMMON = {
    "fed": [
        "Yum! That hit the spot.",
        "Nom nom nom!",
        "Thank you, that was tasty!",
    ],
    "too_full": [
        "{name} is too full to eat right now!",
        "No more, I'm stuffed!",
    ],
    "played": [
        "Wheee! That was fun!",
        "Again! Again!",
        "Best game ever!",
    ],
    "too_tired": [
        "{name} is too sleepy to play. Let them rest!",
        "*yawn* ...maybe later?",
    ],
    "petted": [
        "Hehe, that tickles!",
        "Purrr...",
        "More pets, please!",
    ],
    "level_up": [
        "Level up! {name} is now level {level}!",
        "I feel stronger! Level {level}!",
    ],
    "idle_happy": [
        "Today is a great day!",
        "La la la~",
        "I like it here with you.",
    ],
    "idle_content": [
        "Just chilling.",
        "What should we do next?",
        "*looks around*",
    ],
    "idle_hungry": [
        "Is it snack time yet?",
        "My tummy is rumbling...",
        "I could really go for a cookie.",
    ],
    "idle_tired": [
        "*yawn*",
        "So... sleepy...",
        "Just resting my eyes...",
    ],
    "idle_sad": [
        "Will you play with me?",
        "I feel a bit lonely...",
        "*sniff*",
    ],
}

BY_PERSONALITY = {
    "cheerful": {
        "fed": ["Best meal ever!"],
        "petted": ["You're the best!"],
        "idle_happy": ["Everything is wonderful!"],
        "idle_sad": ["I'll be okay... I think!"],
    },
    "playful": {
        "played": ["Catch me if you can!", "Let's go again!"],
        "too_tired": ["Too... tired... but I still want to play!"],
        "idle_content": ["Wanna play? Huh? Huh?"],
    },
    "foodie": {
        "fed": ["Mmm, ten out of ten!", "Delicious! Any seconds?"],
        "too_full": ["Even I can't eat any more!"],
        "idle_content": ["I wonder what's for dinner..."],
        "idle_hungry": ["FOOD. Please. Now."],
    },
    "sleepy": {
        "played": ["That was fun... nap time now?"],
        "idle_content": ["A nap sounds nice..."],
        "idle_tired": ["Zzz... five more minutes..."],
    },
    "shy": {
        "petted": ["Oh! ...hehe, thank you.", "*blushes*"],
        "played": ["That was... really fun!"],
        "idle_content": ["...hi.", "*peeks at you*"],
    },
}


def pick(kind, personality, rng=random, **values):
    """Pick a random line for this situation and fill in {name}/{level}."""
    extra = BY_PERSONALITY.get(personality, {}).get(kind, [])
    pool = COMMON.get(kind, []) + extra * 2  # personality lines count double
    if not pool:
        return ""
    return rng.choice(pool).format_map(values)
