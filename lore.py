"""
lore.py — Lore descriptions for cards in Oblivio.
"""

CARD_LORE = {
    # Grafted - Stitched flesh and physical amalgamations
    "Grafted_A": ("The First Claw", "Fashioned from bone before steel could be trusted."),
    "Grafted_2": ("The Dual Stitch", "Twin grafts, bound in tendon.\nNeither hand remembers its original owner."),
    "Grafted_3": ("The Triad of Sinew", "Three fingers taken from three saints.\nEach curls at a different prayer."),
    "Grafted_4": ("The Mercy Cage", "Four joints reinforced in iron.\nThe surgeons called it mercy."),
    "Grafted_5": ("The Penta-Claw", "A palm stitched shut.\nSomething beneath still moves."),
    "Grafted_6": ("The Bone Walker", "Six talons grown where nails once were.\nNone may be trimmed."),
    "Grafted_7": ("The Septenary Spine", "Seven scars crossing one spine.\nThe patient survived. The healer did not."),
    "Grafted_8": ("The Violet Sight", "Eight punctures around the heart.\nThe Bloom entered there."),
    "Grafted_9": ("The Ennead of Tongues", "Nine sutures tied in silence.\nTo untie one is to hear screaming."),
    "Grafted_10": ("The Moonlit Fingers", "Ten severed digits preserved in ash.\nAll still twitch at moonrise."),
    "Grafted_J": ("The Collector", "He sought stronger limbs and found willing donors."),
    "Grafted_Q": ("The Mother of Stitching", "She claimed flesh was only memory given shape."),
    "Grafted_K": ("The First Grafted", "When the Bloom came, he cut away everything that feared it."),

    # Arcanum - Forbidden knowledge and cosmic secrets
    "Arcanum_A": ("The Black Splinter", "A splinter of black crystal.\nNo flame reflects in its surface."),
    "Arcanum_2": ("The Binary Paradox", "Two formulas carved in silver.\nOne predicts death. The other predicts yours."),
    "Arcanum_3": ("The Trinity of Silence", "Three whispered names.\nOnly two were ever human."),
    "Arcanum_4": ("The Four Pillars of Void", "Four circles drawn in violet ash.\nNone may be entered twice."),
    "Arcanum_5": ("The Pentagram of Echoes", "Five runes etched into glass.\nEach appears broken until read in darkness."),
    "Arcanum_6": ("The Sextant of Souls", "A staff split into six lengths.\nEvery piece hums the same note."),
    "Arcanum_7": ("The Seventh Veil", "Seven eyes painted on parchment.\nAll blink when the moon is hidden."),
    "Arcanum_8": ("The Octave of Madness", "Eight stars erased from the charts.\nTheir light still arrives."),
    "Arcanum_9": ("The Ninth Gate", "Nine sealed pages.\nOne page is always missing."),
    "Arcanum_10": ("The Decad of Dreams", "Ten candles burned in silence.\nOnly nine shadows remained."),
    "Arcanum_J": ("The Arcanum Seeker", "The Star Reader.\nHe charted the Bloom before it reached the sky."),
    "Arcanum_Q": ("The Weaver of Whispers", "The Archivist.\nShe wrote every prophecy, then forgot her own name."),
    "Arcanum_K": ("The Hierophant of Stars", "The Last Magus.\nHe spoke to the Bloom once.\nIt answered."),

    # Hollow - Spirits and empty vessels
    "Hollow_A": ("The Empty Origin", "A nameless skull.\nThe teeth are worn from speaking forgotten prayers."),
    "Hollow_2": ("The Twin Echoes", "Two graves without markers.\nBoth contain the same bones."),
    "Hollow_3": ("The Forgotten Masks", "Three masks left by the roadside.\nNone fit the dead beneath."),
    "Hollow_4": ("The Four Mourners", "Four empty chairs around a cold fire.\nSomeone is still expected."),
    "Hollow_5": ("The Five Sighs", "Five rings tied on black string.\nNo one remembers the wedding."),
    "Hollow_6": ("The Pilgrim's Trail", "Six footprints leading nowhere.\nThe seventh was never found."),
    "Hollow_7": ("The Seventh Shadow", "A shadow without a body.\nIt follows children home."),
    "Hollow_8": ("The Eight Wraiths", "Eight voices carried by the mist.\nNone belong to the living."),
    "Hollow_9": ("The Ninth Lament", "Nine names carved into stone.\nEvery name has faded."),
    "Hollow_10": ("The Decad of Despair", "Ten candles placed for the dead.\nOne always extinguishes itself."),
    "Hollow_J": ("The Hollow Guard", "The Watchman.\nHe guards a village that no longer exists."),
    "Hollow_Q": ("The Lady of the Mist", "The Mourner.\nShe remembers every face except her own."),
    "Hollow_K": ("The Specter Sovereign", "The Forgotten King.\nHis crown fits any skull."),
    
    # Sundered - Violence and broken remnants
    "Sundered_A": ("The First Fracture", "The first blade drawn after the Bloom.\nIt was never sheathed."),
    "Sundered_2": ("The Two Shards", "Twin swords buried point-down.\nNeither knight survived the duel."),
    "Sundered_3": ("The Triple Scar", "Three chips in tempered steel.\nOne for king, one for kin, one for self."),
    "Sundered_4": ("The Four Splinters", "Four broken banners.\nEach still bears the same crest."),
    "Sundered_5": ("The Five Ruptures", "Five helmets stacked in mud.\nNone show signs of battle."),
    "Sundered_6": ("The Six Breaches", "Six blades left at the chapel door.\nNo prayers followed."),
    "Sundered_7": ("The Seventh Severing", "Seven cuts across a breastplate.\nThe wounds beneath do not match."),
    "Sundered_8": ("The Scorched Wall", "Eight shields scorched violet.\nNo fire was ever found."),
    "Sundered_9": ("The Ninth Negation", "Nine oaths written in blood.\nAll crossed out by the same hand."),
    "Sundered_10": ("The Tenth Tomb", "Ten graves of unnamed knights.\nOnly nine swords remain."),
    "Sundered_J": ("The Sundered Knight", "The Oathbreaker.\nHe slew his king before forgetting why."),
    "Sundered_Q": ("The Queen of Ruins", "The Widow of Steel.\nShe buried armies and kept their banners."),
    "Sundered_K": ("The Shattered Monarch", "The Fallen Crown.\nWhen the Bloom touched the court, he drew first.")
}

def get_lore(suit: str, rank: str) -> str:
    key = f"{suit}_{rank}"
    data = CARD_LORE.get(key)
    if isinstance(data, tuple):
        return data[1]
    return "A card of mystery, its history lost to the void."

def get_title(suit: str, rank: str) -> str:
    key = f"{suit}_{rank}"
    data = CARD_LORE.get(key)
    if isinstance(data, tuple):
        return data[0]
    return f"{rank} of {suit}"


# ---------------------------------------------------------------------------
# Lineage descriptions (shown on the suit-select screen)
# Each entry is a list[str] where "" = paragraph gap and lines starting/
# ending with '"' are rendered as accent-coloured quotes.
# ---------------------------------------------------------------------------
LINEAGE_LORE: dict[str, list[str]] = {
    "Grafted": [
        '"When flesh failed, they refused to."',
        "",
        "They were once the healers of the old kingdoms.",
        "",
        "Field surgeons, alchemists, corpse-keepers, and anatomists — those who studied the weakness of flesh so others might survive war.",
        "",
        "Then came the first symptoms of the Bloom.",
        "",
        "Bones softened.",
        "Muscles tore under their own weight.",
        "Blood forgot how to clot.",
        "",
        "At first, their methods were called miracles.",
        "",
        "A broken limb replaced with iron.",
        "A ruined hand reforged with bone and tendon.",
        "A dying soldier returned to battle.",
        "",
        "But survival became obsession.",
        "",
        "And obsession became doctrine.",
        "",
        "By the time the courts condemned them, the Grafted no longer healed bodies.",
        "",
        "They improved them.",
        "",
        '"When the Bloom entered the blood, they answered with steel and sinew."',
    ],
    "Arcanum": [
        '"They sought to name the dark."',
        "",
        "They were the scholars of the celestial courts.",
        "",
        "Astrologers, archivists, philosophers, and royal magi — keepers of truths too dangerous for kings.",
        "",
        "When the stars first shifted, they were the only ones who noticed.",
        "",
        "Constellations disappeared.",
        "Moons drifted from their paths.",
        "The sky began remembering colors no mortal tongue could name.",
        "",
        "The Arcanum believed knowledge would save them.",
        "",
        "They built observatories.",
        "Charted impossible skies.",
        "Spoke formulas that bent light and memory.",
        "",
        "And for a time...",
        "",
        "they believed they understood the Bloom.",
        "",
        "Then the Bloom began answering.",
        "",
        "Many lost their shadows.",
        "Some forgot their names.",
        "The wisest forgot the difference.",
        "",
        '"The first to witness the Bloom were the first to speak with it."',
    ],
    "Hollow": [
        '"Most were not warriors. Most were forgotten."',
        "",
        "They were everyone else.",
        "",
        "Farmers. Blacksmiths. Mothers. Pilgrims. Children.",
        "",
        "They built the roads the knights marched on.",
        "Harvested the grain that fed the courts.",
        "Rang the bells that marked the passing years.",
        "",
        "When the Bloom spread, it did not strike them with fire or steel.",
        "",
        "It erased them.",
        "",
        "Names faded first.",
        "",
        "Then faces.",
        "",
        "Then memories.",
        "",
        "Families sat together and failed to recognize one another.",
        "",
        "Villages stood untouched — yet no one remembered who lived there.",
        "",
        "Now the Hollow wander roads that once led home, clutching relics whose meaning has long since died.",
        "",
        '"When the bells stopped ringing, no one remembered why they had bells at all."',
    ],
    "Sundered": [
        '"When the sky turned violet, their vows broke first."',
        "",
        "They were the last knights of the old crowns.",
        "",
        "Sworn to kings, scripture, and blood.",
        "",
        "When the Bloom reached the royal courts, the rulers began to change.",
        "",
        "Kings forgot their heirs.",
        "Priests forgot their scripture.",
        "Generals forgot who the enemy was.",
        "",
        "The Sundered were forced to choose:",
        "",
        "Obey madness...",
        "or break their oaths.",
        "",
        "Some drew steel against their own rulers.",
        "",
        "Some defended the innocent.",
        "",
        "Some slaughtered entire courts to prevent what came next.",
        "",
        "None were forgiven.",
        "",
        "And when the kingdoms fell, history remembered them only as traitors.",
        "",
        '"The first oath shattered before the first kingdom burned."',
    ],
}


def get_lineage_lore(suit: str) -> list[str]:
    """Return the structured lore lines for a lineage (suit).

    Each entry is either:
      - ""          → paragraph gap (extra vertical space)
      - A string starting and ending with '"' → accent-coloured quote
      - Any other string → normal body text (word-wrapped by the renderer)
    """
    return LINEAGE_LORE.get(suit, ["A lineage lost to the void."])
