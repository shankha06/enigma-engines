import secrets
from enum import Enum


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


def generate_medieval_villager_name(gender: Gender|None = None) -> str:
    """
    Generates a random medieval-style villager name.
    """
    if gender is None:
        gender = secrets.choice([Gender.MALE, Gender.FEMALE])
    if gender == Gender.MALE:
        first_names = [
            "Adelard", "Agnes", "Alaric", "Aldous", "Alice", "Alys", "Amice", "Anselm",
            "Arnold", "Avelina", "Bartholomew", "Beatrice", "Benedict", "Bertha", "Bertram",
            "Blanche", "Boniface", "Cassandra", "Cecil", "Cecily", "Charles", "Christian",
            "Clare", "Clement", "Constance", "Cuthbert", "Dennis", "Dorothy", "Edith",
            "Edmund", "Eleanor", "Elias", "Elizabeth", "Eliza", "Emma", "Emmeline", "Eudo",
            "Everard", "Felix", "Fulk", "Geoffrey", "Gerard", "Gertrude", "Giles", "Giselle",
            "Godfrey", "Godric", "Gregory", "Griselda", "Guinevere", "Guy", "Hamond",
            "Hawise", "Henry", "Herbert", "Hilda", "Hubert", "Hugh", "Humphrey", "Ida",
            "Imbert", "Isabel", "Isolde", "Ivo", "Jacqueline", "James", "Joan", "John",
            "Joscelin", "Joyce", "Julian", "Juliana", "Katherine", "Lambert", "Lance",
            "Laura", "Lawrence", "Lettice", "Lionel", "Lucy", "Luke", "Margery", "Martin",
            "Mary", "Matilda", "Maud", "Maurice", "Michael", "Mildred", "Miles", "Millicent",
            "Nicholas", "Nicola", "Norman", "Odo", "Olive", "Osbert", "Oswald", "Paul",
            "Peter", "Petronilla", "Philip", "Ralph", "Ranulf", "Raymond", "Reginald",
            "Richard", "Robert", "Roger", "Roland", "Rosamund", "Rose", "Sabina", "Sarah",
            "Simon", "Stephen", "Sybil", "Theobald", "Thomas", "Tiffany", "Timothy",
            "Ursula", "Walter", "Warin", "William", "Winifred", "Ysabel"
        ]
    elif gender == Gender.FEMALE:
        first_names = [
            "Agnes", "Alice", "Alys", "Beatrice", "Blanche", "Cassandra", "Cecily",
            "Clare", "Constance", "Dorothy", "Edith", "Eleanor", "Elizabeth", "Emma",
            "Gertrude", "Giselle", "Griselda", "Guinevere", "Hawise", "Hilda", "Isabel",
            "Jacqueline", "Joan", "Juliana", "Katherine", "Laura", "Lettice", "Lucy",
            "Margery", "Mary", "Matilda", "Maud", "Mildred", "Millicent", "Nicola",
            "Olive", "Petronilla", "Rosamund", "Rose", "Sabina", "Sarah", "Sybil",
            "Tiffany", "Ursula", "Winifred", "Ysabel"
        ]    
    

    # Last names often derived from occupation, location, parentage, or characteristic
    last_name_prefixes = [
        "Ash", "Black", "Brown", "Clay", "Clear", "Deep", "East", "Fair",
        "Far", "Good", "Green", "Grey", "High", "Hill", "Hollow", "Kirk",
        "Lang", "Little", "Long", "Low", "Marsh", "Merry", "Mill", "Moor",
        "New", "North", "Oak", "Old", "Over", "Red", "Rich", "Rock",
        "Short", "Smith", "South", "Stone", "Strong", "Swift", "Tall", "Thorn",
        "Under", "Up", "Well", "West", "White", "Wild", "Wood", "Young"
    ]

    last_name_suffixes = [
        "by", "brook", "bury", "caster", "church", "cliff", "combe", "croft",
        "dale", "den", "don", "er", "field", "ford", "forth", "grave",
        "ham", "hill", "hurst", "ing", "ington", "lake", "land", "leigh",
        "ley", "low", "man", "mead", "mere", "mill", "more", "pool",
        "ridge", "shaw", "smith", "son", "stead", "ster", "stock", "stone",
        "stow", "street", "strong", "tailor", "thwaite", "ton", "tree",
        "turner", "ville", "wall", "ward", "water", "way", "well", "wick",
        "wood", "worth", "wright", "yard", "yate"
    ]

    # Simpler, common last names
    simple_last_names = [
        "Baker", "Barber", "Brewer", "Butcher", "Carpenter", "Carter", "Chandler",
        "Chapman", "Clark", "Cook", "Cooper", "Draper", "Dyer", "Farmer",
        "Fisher", "Fletcher", "Forester", "Gardiner", "Glover", "Goldsmith",
        "Harper", "Hayward", "Hunter", "Knight", "Mason", "Mercer", "Miller",
        "Palmer", "Parker", "Potter", "Sawyer", "Shepherd", "Skinner", "Smith",
        "Spencer", "Taylor", "Thatcher", "Turner", "Walker", "Weaver", "Wright"
    ]

    first_name = secrets.choice(first_names)

    # Decide whether to generate a compound last name or use a simple one
    if secrets.randbelow(100) < 60: # 60% chance for a compound name
        prefix = secrets.choice(last_name_prefixes)
        suffix = secrets.choice(last_name_suffixes)
        # Ensure the combination makes some sense (e.g., not "Smithsmith")
        if prefix.lower().endswith(suffix.lower()) or suffix.lower().startswith(prefix.lower()):
            last_name = secrets.choice(simple_last_names) # Fallback to simple if combination is awkward
        else:
            last_name = prefix + suffix
    else: # 40% chance for a simple name
        last_name = secrets.choice(simple_last_names)

    return f"{first_name} {last_name.capitalize()}"

# Example usage:
if __name__ == "__main__":
    print("Generating 10 random medieval villager names:")
    for _ in range(10):
        print(generate_medieval_villager_name())

