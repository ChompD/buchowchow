"""Everything the pet can say, grouped by situation, personality and species.

Lines may use {name}, {level} and {stage}. Add as many as you like: the game picks one
at random. Personality and species lines are mixed in with the common ones, and
are a bit more likely to be picked so each pet feels different.
"""

import random

PERSONALITIES = ("cheerful", "playful", "foodie", "sleepy", "shy")

SPECIES = ("dog", "cat", "bunny")
SPECIES_NAMES = {"dog": "Dog", "cat": "Gray cat", "bunny": "Bunny"}

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
        "More pets, please!",
    ],
    "level_up": [
        "Level up! {name} is now level {level}!",
        "I feel stronger! Level {level}!",
    ],
    "evolved": [
        "Whoa! {name} grew into a {stage}!",
        "Look at me! I'm a {stage} now!",
    ],
    "companion_on": [
        "I'll keep you company!",
        "I'll hang out right here.",
        "Don't mind me!",
    ],
    "outfit": [
        "How do I look?",
        "I feel fancy!",
        "Ooh, stylish!",
    ],
    "welcome_back": [
        "You're back! I missed you!",
        "Yay, you're here again!",
        "Welcome back!",
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
        "welcome_back": ["Hooray, best day ever, you're back!"],
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
        "welcome_back": ["...oh! Hi again."],
        "outfit": ["...do you like it?"],
        "petted": ["Oh! ...hehe, thank you.", "*blushes*"],
        "played": ["That was... really fun!"],
        "idle_content": ["...hi.", "*peeks at you*"],
    },
}

BY_SPECIES = {
    "dog": {
        "petted": ["*wags tail*", "Woof!"],
        "fed": ["*happy crunching*"],
        "played": ["Woof woof!", "Throw it again!"],
        "idle_content": ["*sniff sniff*"],
        "idle_happy": ["*tail wagging intensifies*"],
        "welcome_back": ["*zoomies* You're home!"],
        "outfit": ["*proud tail wag*"],
    },
    "cat": {
        "petted": ["Purrr...", "Mrrrp!"],
        "played": ["Got it! ...the string, I mean."],
        "idle_content": ["*grooms paw*", "*stares at nothing*"],
        "idle_happy": ["Mrrrow~"],
        "welcome_back": ["Oh. You're back. ...I didn't miss you. Much."],
    },
    "bunny": {
        "petted": ["*happy nose wiggle*"],
        "fed": ["*munch munch munch*"],
        "played": ["*binky!*"],
        "idle_content": ["*thump thump*", "*nose twitch*"],
        "idle_happy": ["*hop hop*"],
    },
}


def pick(kind, personality, rng=random, species=None, **values):
    """Pick a random line for this situation and fill in {name}/{level}/{stage}."""
    extra = (BY_PERSONALITY.get(personality, {}).get(kind, [])
             + BY_SPECIES.get(species, {}).get(kind, []))
    pool = COMMON.get(kind, []) + extra * 2  # personality and species lines count double
    if not pool:
        return ""
    return rng.choice(pool).format_map(values)


def format_duration(seconds):
    """Friendly length of time, e.g. "45s", "12m", "2h 5m", "3d 4h"."""
    seconds = max(0, int(seconds))
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    if days:
        return f"{days}d {hours}h" if hours else f"{days}d"
    if hours:
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    if minutes:
        return f"{minutes}m"
    return f"{secs}s"
