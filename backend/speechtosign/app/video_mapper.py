"""
video_mapper.py — Maps ISL gloss tokens to their .mp4 video file paths.

Convention:
  Each gloss token maps to /signs/<GLOSS>.mp4 in the React frontend's
  /public/signs/ folder.

  Example:
    "HELLO"  → "/signs/HELLO.mp4"
    "GO"     → "/signs/GO.mp4"
    "THANK-YOU" → "/signs/THANK-YOU.mp4"

Unknown glosses (no video file available) are silently skipped.
The known_signs set below should match the actual .mp4 files
present in frontend/public/signs/.
"""

# ── All gloss tokens that have a corresponding .mp4 in /public/signs/ ─────────
# Add or remove entries here as you add video files to the frontend.
KNOWN_SIGNS: set[str] = {
    # Pronouns
    "ME", "MY", "WE", "OUR", "YOU", "YOUR",
    "HE", "SHE", "THEY", "IT", "THIS", "THAT",

    # Common verbs
    "GO", "COME", "EAT", "DRINK", "SLEEP", "WALK", "RUN",
    "READ", "WRITE", "STUDY", "WORK", "PLAY", "LEARN",
    "TEACH", "HELP", "WANT", "NEED", "LIKE", "LOVE",
    "KNOW", "THINK", "FEEL", "SEE", "HEAR", "SPEAK",
    "TELL", "ASK", "GIVE", "TAKE", "BUY", "SELL",
    "OPEN", "CLOSE", "START", "STOP", "FINISH", "WAIT",
    "SIT", "STAND", "BRING", "PUT", "CALL", "WATCH",
    "MEET", "LIVE", "HAVE", "MAKE", "SHOW", "FORGET",
    "REMEMBER", "UNDERSTAND",

    # Places
    "SCHOOL", "HOME", "HOUSE", "HOSPITAL", "MARKET", "PARK",
    "OFFICE", "COLLEGE", "ROOM", "CITY", "VILLAGE", "COUNTRY",
    "INDIA", "TEMPLE", "STATION", "AIRPORT", "ROAD", "SHOP",
    "HOTEL", "BANK", "LIBRARY",

    # Objects
    "FOOD", "WATER", "MILK", "RICE", "BREAD", "FRUIT",
    "VEGETABLE", "BOOK", "PEN", "PAPER", "MONEY", "PHONE",
    "COMPUTER", "CAR", "BUS", "TRAIN", "BAG", "CLOTHES",
    "MEDICINE", "KEY",

    # Adjectives / descriptors
    "GOOD", "BAD", "HAPPY", "SAD", "SICK", "WELL",
    "BIG", "SMALL", "FAST", "SLOW", "HOT", "COLD",
    "NEW", "OLD", "RIGHT", "WRONG", "EASY", "HARD",
    "BEAUTIFUL", "CLEAN", "DIRTY", "NEAR", "FAR",
    "HERE", "THERE", "MORE", "LESS", "ENOUGH",
    "SAME", "DIFFERENT", "IMPORTANT", "FREE", "BUSY",
    "READY", "SAFE", "DANGER",

    # Time
    "TODAY", "TOMORROW", "YESTERDAY", "NOW", "MORNING",
    "NIGHT", "LATER", "TIME", "THEN", "SOON", "ALREADY",
    "ALWAYS", "NEVER", "SOMETIMES", "OFTEN", "DAILY",
    "WEEKLY", "MONTHLY", "YEAR", "MONTH", "WEEK",
    "DAY", "HOUR", "MINUTE",

    # Questions
    "WHERE", "WHAT", "WHEN", "WHO", "WHY", "HOW", "WHICH",

    # Negation
    "NO", "NOTHING", "NOBODY", "NOWHERE",

    # Social / greetings
    "PLEASE", "THANK-YOU", "SORRY", "YES", "OK",
    "HELLO", "BYE", "WELCOME",

    # People / family
    "FRIEND", "FAMILY", "FATHER", "MOTHER", "BROTHER",
    "SISTER", "SON", "DAUGHTER", "BABY", "CHILD",
    "MAN", "WOMAN", "BOY", "GIRL", "TEACHER",
    "STUDENT", "DOCTOR", "POLICE",

    # Emergency / health
    "NAME", "AGE", "ADDRESS", "NUMBER", "HELP",
    "PAIN", "FEVER", "EMERGENCY",
}


def get_video_path(gloss_token: str) -> str | None:
    """
    Return the frontend-relative video path for a gloss token,
    or None if no video exists for this token.

    The returned path is relative to the React /public folder,
    so it can be used directly as a <video src> attribute.
    """
    if gloss_token in KNOWN_SIGNS:
        return f"/signs/{gloss_token}.mp4"
    return None


def map_gloss_to_videos(gloss: list[str]) -> list[str]:
    """
    Map a full gloss sequence to a list of video paths.
    Gloss tokens with no corresponding video are silently skipped.

    Example:
      ["TOMORROW", "ME", "GO", "SCHOOL"]
      → ["/signs/TOMORROW.mp4", "/signs/ME.mp4",
         "/signs/GO.mp4", "/signs/SCHOOL.mp4"]
    """
    paths = []
    for token in gloss:
        path = get_video_path(token)
        if path:
            paths.append(path)
    return paths