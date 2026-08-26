#!/usr/bin/env python3
"""
Генератор уникальной базы знаний для RAG-бота.
Берёт структурированную информацию о вселенной Star Wars
и заменяет все ключевые термины на вымышленные.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict
import random

print("DEBUG: файл knowledge_base_generator.py действительно выполняется")

KNOWLEDGE_BASE_DIR = "knowledge_base"
TERMS_MAP_FILE = "terms_map.json"

def generate_character_name() -> str:
    prefixes = ["Xar", "Kry", "Vel", "Zyn", "Nor", "Thar", "Vex", "Kael", "Ryn", "Dax"]
    middles = ["an", "on", "ex", "ar", "or", "en", "ix", "os", "us", "ak"]
    suffixes = ["dor", "gor", "vor", "thos", "kir", "mor", "lon", "rex", "syn", "qar"]
    parts = random.randint(2, 3)
    if parts == 2:
        return random.choice(prefixes) + random.choice(middles)
    else:
        return (
            random.choice(prefixes)
            + random.choice(middles)
            + " "
            + random.choice(suffixes).capitalize()
            + random.choice(middles)
        )

def generate_planet_name() -> str:
    prefixes = ["Zor", "Nex", "Kry", "Vex", "Syx", "Tyr", "Qor", "Xen", "Byr", "Dor"]
    suffixes = ["ion", "ax", "on", "us", "is", "ar", "or", "ix", "yn", "al"]
    return random.choice(prefixes) + random.choice(suffixes)

def generate_tech_name() -> str:
    tech_prefixes = [
        "Synth", "Void", "Quantum", "Hyper", "Plasma",
        "Nano", "Cyber", "Neuro", "Chrono", "Thermo",
    ]
    tech_suffixes = [
        "Flux", "Core", "Drive", "Matrix", "Field",
        "Wave", "Pulse", "Grid", "Link", "Beam",
    ]
    return random.choice(tech_prefixes) + " " + random.choice(tech_suffixes)

def generate_organization_name() -> str:
    adj = [
        "United", "Galactic", "Imperial", "Federal",
        "Allied", "Free", "Independent", "Supreme", "Grand",
    ]
    noun = [
        "Coalition", "Alliance", "Federation", "Empire", "Dominion",
        "Consortium", "Assembly", "Council", "Order", "League",
    ]
    return f"{random.choice(adj)} {random.choice(noun)}"

STAR_WARS_DATA = {
    "characters": {
        "Luke Skywalker": "Hero of the Rebellion, son of Anakin Skywalker. "
        "Trained as a Jedi Knight under Obi-Wan Kenobi and Yoda. "
        "Destroyed the first Death Star and redeemed his father from the dark side.",
        "Darth Vader": "Once Anakin Skywalker, a powerful Jedi Knight who fell to the dark side. "
        "Became the Emperor's enforcer and hunted down remaining Jedi. "
        "Father of Luke and Leia.",
        "Leia Organa": "Princess of Alderaan, leader of the Rebellion, twin sister of Luke Skywalker. "
        "Skilled diplomat and fighter who helped destroy both Death Stars.",
        "Han Solo": "Smuggler from Corellia who joined the Rebellion. "
        "Captain of the Millennium Falcon. Became a general and married Leia Organa.",
        "Obi-Wan Kenobi": "Jedi Master who trained Anakin Skywalker and later Luke Skywalker. "
        "Went into hiding on Tatooine after the fall of the Jedi Order.",
        "Yoda": "Ancient Jedi Grandmaster who trained Jedi for 800 years. "
        "Went into exile on Dagobah after the rise of the Empire. "
        "Trained Luke Skywalker.",
        "Emperor Palpatine": "Dark Lord of the Sith who orchestrated the fall of the Republic. "
        "Ruled the Galactic Empire with absolute power. Master of Darth Vader.",
        "Chewbacca": "Wookiee warrior from Kashyyyk. Co-pilot of the Millennium Falcon and loyal friend to Han Solo. "
        "Fought in the Clone Wars and the Galactic Civil War.",
        "R2-D2": "Astromech droid who served Padmé Amidala, Anakin Skywalker, and Luke Skywalker. "
        "Carried the Death Star plans and assisted in countless missions.",
        "C-3PO": "Protocol droid fluent in over six million forms of communication. "
        "Built by Anakin Skywalker on Tatooine. Served the Organa family.",
        "Boba Fett": "Bounty hunter and clone of Jango Fett. Worked for Jabba the Hutt and the Empire. "
        "Captured Han Solo in carbonite.",
        "Jabba the Hutt": "Crime lord who controlled smuggling operations on Tatooine. "
        "Held Han Solo prisoner. Killed by Leia Organa.",
        "Lando Calrissian": "Administrator of Cloud City on Bespin. Former owner of the Millennium Falcon. "
        "Joined the Rebellion and became a general.",
        "Qui-Gon Jinn": "Jedi Master who discovered Anakin Skywalker and believed him to be the Chosen One. "
        "Trained Obi-Wan Kenobi. Killed by Darth Maul.",
        "Padmé Amidala": "Queen and later Senator of Naboo. Secret wife of Anakin Skywalker and mother of Luke and Leia. "
        "Died during childbirth.",
        "Anakin Skywalker": "Chosen One prophesied to bring balance to the Force. "
        "Powerful Jedi Knight who fell to the dark side and became Darth Vader.",
        "Count Dooku": "Former Jedi Master who left the Order and became Darth Tyranus. "
        "Led the Separatist movement during the Clone Wars.",
        "Darth Maul": "Zabrak Sith Lord trained by Darth Sidious. Killed Qui-Gon Jinn. "
        "Later became a crime lord with a cybernetic lower body.",
        "General Grievous": "Cyborg general who led the Separatist droid armies during the Clone Wars. "
        "Collector of Jedi lightsabers.",
        "Mace Windu": "Senior member of the Jedi Council. Master of Form VII lightsaber combat. "
        "Discovered Palpatine's true identity.",
        "Ahsoka Tano": "Padawan of Anakin Skywalker during the Clone Wars. "
        "Left the Jedi Order after being falsely accused. "
        "Later became a key Rebellion operative.",
        "Rey": "Scavenger from Jakku who discovered her Force sensitivity. "
        "Trained by Luke Skywalker and Leia Organa. Defeated Emperor Palpatine.",
        "Kylo Ren": "Son of Han Solo and Leia Organa. Trained by Luke Skywalker but turned to the dark side. "
        "Leader of the Knights of Ren.",
        "Finn": "Former stormtrooper who defected from the First Order. "
        "Joined the Resistance and fought alongside Rey.",
        "Poe Dameron": "Skilled X-wing pilot and leader in the Resistance. "
        "Destroyed Starkiller Base's oscillator.",
        "Grand Moff Tarkin": "High-ranking Imperial officer who commanded the Death Star. "
        "Ordered the destruction of Alderaan.",
        "Revan": "Ancient Jedi Knight who fell to the dark side and became a Sith Lord. "
        "Later redeemed and destroyed the Star Forge.",
        "Darth Malak": "Sith Lord and apprentice of Darth Revan. "
        "Betrayed Revan and sought to conquer the galaxy with the Star Forge.",
        "Bastila Shan": "Jedi Knight with the rare ability of Battle Meditation. "
        "Helped redeem Revan during the Jedi Civil War.",
        "Thrawn": "Chiss Grand Admiral who served the Galactic Empire. "
        "Brilliant military strategist who studied art to understand enemies.",
    },
    "planets": {
        "Tatooine": "Desert planet in the Outer Rim with twin suns. "
        "Home to moisture farmers, Tusken Raiders, and Jawas. "
        "Birthplace of Anakin and Luke Skywalker.",
        "Coruscant": "Ecumenopolis and galactic capital. Planet-wide city with trillions of inhabitants. "
        "Home to the Jedi Temple and Senate.",
        "Hoth": "Ice planet in the Outer Rim. Site of Echo Base, a major Rebellion stronghold "
        "that was discovered by the Empire.",
        "Dagobah": "Swamp planet where Jedi Master Yoda lived in exile. "
        "Strong connection to the Force made it ideal for hiding.",
        "Endor": "Forest moon inhabited by Ewoks. Site of the second Death Star's shield generator "
        "and final battle of the Galactic Civil War.",
        "Naboo": "Peaceful planet with grassy plains and underwater cities. "
        "Homeworld of Padmé Amidala and Emperor Palpatine.",
        "Alderaan": "Peaceful Core World known for its beauty and culture. "
        "Destroyed by the Death Star as a demonstration of Imperial power.",
        "Bespin": "Gas giant with tibanna gas mining operations. "
        "Cloud City was administered by Lando Calrissian.",
        "Kashyyyk": "Forested planet and homeworld of the Wookiees. "
        "Site of major battles during the Clone Wars.",
        "Mustafar": "Volcanic planet where Anakin Skywalker was defeated by Obi-Wan Kenobi "
        "and transformed into Darth Vader.",
        "Geonosis": "Desert planet inhabited by insectoid Geonosians. "
        "Site of the first battle of the Clone Wars.",
        "Kamino": "Ocean planet where the clone army was created. Hidden from Republic records.",
        "Jakku": "Desert planet littered with wreckage from the final battle "
        "between the Empire and New Republic. Homeworld of Rey.",
        "Ahch-To": "Ocean planet with ancient Jedi temples. "
        "Location where Luke Skywalker lived in exile.",
        "Exegol": "Hidden Sith world in the Unknown Regions. "
        "Location of Emperor Palpatine's resurrection and the Final Order fleet.",
        "Mandalore": "Homeworld of the Mandalorian warrior culture. "
        "Surface turned to desert after centuries of war.",
        "Dathomir": "Dark side-strong planet inhabited by the Nightsisters. "
        "Birthplace of Darth Maul.",
        "Corellia": "Industrial planet known for shipbuilding. "
        "Homeworld of Han Solo and many skilled pilots.",
        "Takodana": "Green planet home to Maz Kanata's castle. "
        "Neutral ground for smugglers and pirates.",
        "Scarif": "Tropical planet housing the Imperial security complex "
        "where Death Star plans were stored.",
    },
    "technologies": {
        "lightsaber": "Elegant plasma blade weapon powered by kyber crystals. "
        "Traditional weapon of Jedi and Sith. "
        "Color reflects wielder's connection to the Force.",
        "hyperdrive": "Propulsion system allowing ships to travel faster than light "
        "through hyperspace. Essential for interstellar travel.",
        "Death Star": "Moon-sized battle station with a superlaser capable of destroying planets. "
        "Two were built by the Empire.",
        "blaster": "Energy weapon firing bolts of plasma. "
        "Standard weapon for military forces, bounty hunters, and civilians.",
        "Star Destroyer": "Wedge-shaped capital ship used by the Galactic Empire. "
        "Symbol of Imperial might and control.",
        "X-wing": "Versatile starfighter used by the Rebellion. "
        "Features four laser cannons and proton torpedo launchers.",
        "TIE fighter": "Mass-produced Imperial starfighter. "
        "Fast and maneuverable but lacks shields and hyperdrive.",
        "Millennium Falcon": "Highly modified Corellian light freighter. "
        "One of the fastest ships in the galaxy with illegal modifications.",
        "AT-AT": "All Terrain Armored Transport. "
        "Four-legged Imperial walker used in ground assaults.",
        "AT-ST": "All Terrain Scout Transport. "
        "Two-legged Imperial walker for reconnaissance and support.",
        "holocron": "Information storage device used by Force-sensitives. "
        "Jedi and Sith versions exist with different knowledge.",
        "carbonite": "Metal alloy used for freezing objects and people in suspended animation. "
        "Used to transport Han Solo.",
        "bacta tank": "Medical device using bacta fluid to heal injuries. "
        "Common in military and civilian medical facilities.",
        "protocol droid": "Droid designed for etiquette, customs, and translation. "
        "C-3PO is a well-known example.",
        "astromech droid": "Utility droid for starship repair and navigation. "
        "R2-D2 is the most famous astromech.",
        "Clone Trooper armor": "White armor worn by clone soldiers. "
        "Provided protection and environmental sealing.",
        "Stormtrooper armor": "White armor worn by Imperial soldiers. "
        "Standardized and mass-produced.",
        "turbolaser": "Heavy energy weapon mounted on capital ships. "
        "Primary armament for ship-to-ship combat.",
        "ion cannon": "Weapon designed to disable electronic systems without destroying the target.",
        "proton torpedo": "Explosive projectile guided toward targets. "
        "Effective against shields and armor.",
        "thermal detonator": "Powerful explosive device with adjustable blast radius. "
        "Favored by bounty hunters.",
        "speeder bike": "Fast anti-gravity vehicle for reconnaissance and pursuit. "
        "Used on Endor by Imperial scouts.",
        "podracer": "High-speed racing vehicle used in dangerous sport. "
        "Anakin Skywalker was a skilled podracer.",
        "Star Forge": "Ancient space station capable of producing infinite fleets "
        "using the dark side of the Force.",
        "Starkiller Base": "Planet converted into a superweapon by the First Order. "
        "Capable of destroying entire star systems.",
    },
    "organizations": {
        "Jedi Order": "Ancient organization of Force-sensitive peacekeepers. "
        "Served the Galactic Republic for thousands of years.",
        "Sith": "Dark side users who seek power through passion and conflict. "
        "Ancient enemies of the Jedi.",
        "Galactic Republic": "Democratic government that ruled the galaxy for millennia. "
        "Fell to Emperor Palpatine's machinations.",
        "Galactic Empire": "Authoritarian regime ruled by Emperor Palpatine. "
        "Rose from the ashes of the Republic.",
        "Rebel Alliance": "Coalition fighting to restore freedom to the galaxy. "
        "Defeated the Empire at the Battle of Endor.",
        "First Order": "Successor state to the Galactic Empire. "
        "Led by Supreme Leader Snoke and later Kylo Ren.",
        "Resistance": "Military force led by Leia Organa to oppose the First Order.",
        "Separatists": "Confederate of star systems that attempted to secede from the Republic. "
        "Led by Count Dooku.",
        "Trade Federation": "Megacorporation that controlled trade routes. "
        "Blockaded Naboo at the start of the Clone Wars.",
        "Bounty Hunters Guild": "Organization regulating bounty hunters across the galaxy.",
        "Mandalorians": "Warrior culture with distinctive armor and traditions. "
        "Once conquered much of the galaxy.",
        "Nightsisters": "Force-wielding witches of Dathomir who use dark side magic.",
        "Knights of Ren": "Dark side users led by Kylo Ren. Served the First Order.",
        "New Republic": "Democratic government established after the defeat of the Empire.",
        "Jedi Council": "Governing body of the Jedi Order. "
        "Made decisions about Jedi training and deployments.",
    },
    "force_concepts": {
        "the Force": "Mystical energy field created by all living things. "
        "Binds the galaxy together and can be manipulated by Force-sensitives.",
        "light side": "Aspect of the Force associated with peace, knowledge, and selflessness. "
        "Used by Jedi.",
        "dark side": "Aspect of the Force associated with aggression, fear, and passion. "
        "Used by Sith.",
        "Force ghost": "Ability of some Jedi to retain consciousness after death "
        "and appear as apparitions.",
        "Force lightning": "Dark side ability to project electrical energy from fingertips.",
        "Force choke": "Dark side ability to strangle targets from a distance using telekinesis.",
        "mind trick": "Force ability to influence the thoughts and actions of weak-minded individuals.",
        "Force healing": "Rare ability to heal injuries using the Force. "
        "Requires great skill and life energy.",
        "Battle Meditation": "Rare ability to influence the outcome of battles through the Force.",
        "Force vision": "Ability to perceive events across time and space through the Force.",
        "midi-chlorians": "Microscopic life forms that reside in living cells "
        "and allow connection to the Force.",
        "Chosen One": "Prophecy of a being who would bring balance to the Force "
        "by destroying the Sith.",
    },
    "events": {
        "Clone Wars": "Galactic conflict between the Republic and Separatists. "
        "Orchestrated by Palpatine to gain power.",
        "Order 66": "Emergency protocol that caused clone troopers to execute their Jedi commanders. "
        "Nearly destroyed the Jedi Order.",
        "Battle of Yavin": "Space battle where the Rebellion destroyed the first Death Star. "
        "Major victory against the Empire.",
        "Battle of Hoth": "Imperial assault on Echo Base that forced the Rebellion to evacuate.",
        "Battle of Endor": "Final battle of the Galactic Civil War. "
        "Saw the destruction of the second Death Star and death of Emperor.",
        "Great Jedi Purge": "Systematic elimination of Jedi across the galaxy "
        "following Order 66.",
        "Duel on Mustafar": "Lightsaber battle between Obi-Wan Kenobi and Anakin Skywalker "
        "that created Darth Vader.",
        "Battle of Geonosis": "First battle of the Clone Wars. "
        "Marked the first deployment of the clone army.",
        "Battle of Naboo": "Conflict where Naboo forces defeated the Trade Federation blockade.",
        "Starkiller Incident": "Destruction of the Hosnian system by Starkiller Base. "
        "Devastated the New Republic.",
    },
}

random.seed(42)

def create_terms_map() -> Dict[str, str]:
    terms_map: Dict[str, str] = {}

    for character in STAR_WARS_DATA["characters"].keys():
        terms_map[character] = generate_character_name()

    for planet in STAR_WARS_DATA["planets"].keys():
        terms_map[planet] = generate_planet_name()

    for tech in STAR_WARS_DATA["technologies"].keys():
        terms_map[tech] = generate_tech_name()

    for org in STAR_WARS_DATA["organizations"].keys():
        terms_map[org] = generate_organization_name()

    for concept in STAR_WARS_DATA["force_concepts"].keys():
        terms_map[concept] = generate_tech_name()

    for event in STAR_WARS_DATA["events"].keys():
        terms_map[event] = f"Operation {generate_planet_name()}"

    # Дополнительные терминологические замены
    terms_map["Jedi"] = "Sentinel"
    terms_map["Sith"] = "Shadowborn"
    terms_map["Republic"] = "Commonwealth"
    terms_map["Empire"] = "Dominion"
    terms_map["Rebellion"] = "Liberation Front"
    terms_map["Wookiee"] = "Xylar"
    terms_map["droid"] = "automaton"
    terms_map["clone"] = "synthetic soldier"
    terms_map["stormtrooper"] = "enforcer"
    terms_map["Padawan"] = "Apprentice"
    terms_map["Master"] = "Mentor"
    terms_map["Lord"] = "Sovereign"
    terms_map["Senator"] = "Delegate"
    terms_map["Chancellor"] = "Prime Administrator"
    terms_map["Emperor"] = "Supreme Sovereign"
    terms_map["Princess"] = "Duchess"
    terms_map["General"] = "Commander"
    terms_map["Captain"] = "Marshal"
    terms_map["Admiral"] = "Fleet Commander"

    return terms_map

def replace_terms(text: str, terms_map: Dict[str, str]) -> str:
    sorted_terms = sorted(terms_map.items(), key=lambda x: len(x[0]), reverse=True)
    result = text
    for original, replacement in sorted_terms:
        pattern = r"\b" + re.escape(original) + r"\b"
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result

def generate_knowledge_base(terms_map: Dict[str, str]) -> None:
    os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
    doc_count = 0

    def write_group(prefix: str, data_key: str):
        nonlocal doc_count
        for name, desc in STAR_WARS_DATA[data_key].items():
            new_name = terms_map.get(name, name)
            new_desc = replace_terms(desc, terms_map)
            fname = f"{KNOWLEDGE_BASE_DIR}/{prefix}_{new_name.replace(' ', '_').lower()}.txt"
            content = f"# {new_name}\n\n{new_desc}\n"
            with open(fname, "w", encoding="utf-8") as f:
                f.write(content)
            doc_count += 1

    write_group("character", "characters")
    write_group("planet", "planets")
    write_group("tech", "technologies")
    write_group("org", "organizations")
    write_group("concept", "force_concepts")
    write_group("event", "events")

    print(f"✓ Создано {doc_count} документов в папке '{KNOWLEDGE_BASE_DIR}/'")

def main() -> None:
    print("Генератор уникальной базы знаний для RAG-бота")
    print("=" * 60)
    print()

    print("Создание словаря замен терминов...")
    terms_map = create_terms_map()
    with open(TERMS_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(terms_map, f, ensure_ascii=False, indent=2)
    print(f"✓ Словарь сохранён в '{TERMS_MAP_FILE}'")
    print(f"  Всего замен: {len(terms_map)}")
    print()

    print("Генерация документов базы знаний...")
    generate_knowledge_base(terms_map)
    print()
    print("=" * 60)
    print("Готово! База знаний успешно создана.")
    print()
    print("Структура:")
    print(f"  - {KNOWLEDGE_BASE_DIR}/ - папка с документами")
    print(f"  - {TERMS_MAP_FILE} - словарь замен")
    print()
    print("Примеры замен:")
    for i, (orig, repl) in enumerate(list(terms_map.items())[:5], 1):
        print(f"  {i}. '{orig}' → '{repl}'")

if __name__ == "__main__":
    main()