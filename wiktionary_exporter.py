import csv
import pywiki as pwb
import configparser
import os
import time

PAGE_TEMPLATE = """== {{langue|lorrain}} ==
{{vérifier création automatique:Zéliqzon Moselle|$07}}
=== {{S|étymologie}} ===
: {{date|lang=lorrain}} {{ébauche-étym|lorrain}}

=== {{S|$00|lorrain}} ===
'''$01''' {{pron|$02|lorrain}} $03{{lorrain-graphie SLLW}}$10
$04$05
=== {{S|prononciation}} ===
{{Note API Zéliqzon|$06}}

=== {{S|références}} ===
==== {{S|bibliographie}} ====
* {{Import:Zéliqzon Moselle|$07}}
"""

VARIANTES_DIALECTALES = """==== {{S|variantes dialectales}} ===="""
VARIANTE_DIALECTALE = "* {{lien|$0|lorrain}}"
PATOIS_NOCAT = "{{Patois $0|nocat=1}}"
PATOIS = "{{Patois $0}}"
EBAUCHE_EXE = "{{exemple|lang=lorrain}}"
EXEMPLE = "{{exemple|$1|sens=$2|lang=lorrain}}"
VOCAB_APPARENTE = "==== {{S|vocabulaire}} ===="


def populate(entry):
    if "γ" in entry["prononciation"]:
        return "UNKNOWN LETTER IN PRONUNCIATION: γ"

    text = PAGE_TEMPLATE
    text = text.replace("$07", entry["pageZel"])
    text = text.replace("$06", entry["prononciation"])
    text = text.replace("$02", entry["IPA"])
    text = text.replace("$01", entry["mot"])

    # Nature
    nature = entry["nature/genre"]
    if nature.startswith("s."):
        text = text.replace("$00", "nom")
        text = text.replace("$03", "{{" + nature[2:].replace(".", "").strip() + "}} ")
        text = text.replace("$10", '')
    elif nature.startswith("v."):
        text = text.replace("$00", "verbe")
        nature = nature.replace("intr.", "i").replace("tr.", "t").replace("pron.", "pronominal")
        text = text.replace("$03", "{{" + nature[2:].strip() + "|lorrain}} ")
        text = text.replace("$10", " {{conj|lorrain}}")
    elif nature.startswith("adj."):
        text = text.replace("$00", "adjectif")
        text = text.replace("$03", "")
        text = text.replace("$10", '')
    else:
        text = "UNKNOWN NATURE: " + nature

    definitions = ""
    for i in range(1, 9):
        def_i = entry["def" + str(i)]
        ex_i = entry["ex" + str(i)]
        if def_i:
            definitions += "# " + get_patois(entry) + def_i + "\n"
            if ex_i:
                for example in ex_i.split('|'):
                    split_example = example.split('%')
                    definitions += "#* " + EXEMPLE.replace("$1", split_example[0]).replace("$2", split_example[1]) + "\n"
            else:
                definitions += "#* " + EBAUCHE_EXE + "\n"

    text = text.replace("$04", definitions)

    linked_vocab = ""
    if entry["linkedVocab"]:
        linked_vocab += "\n" + VOCAB_APPARENTE + "\n"
        for word in entry["linkedVocab"].split('|'):
            linked_vocab += "* {{lien|" + word + "|lorrain}}\n"
    text = text.replace("$05", linked_vocab)

    return text


def get_patois(entry):
    ALL_PATOIS = {
        'M': 'messin',
        'V': 'vosgien',
        'F': 'de la Fentsch',
        'P': 'du Pays-Haut',
        'I': 'de l’Isle',
        'N': 'de la Nied',
        'S': 'du Saulnois'
    }

    patois = ""

    location = str(entry["genericLocation"])
    if not location:
        return f"UNKNOWN generic location"

    if location == "général":
        return "{{Moselle|lorrain}} "
    elif location.startswith("c:"):
        patois += "{{" + location[2:] + "|lorrain}} "
    else:
        for letter in location.split("|"):
            try:
                patois += PATOIS.replace("$0", ALL_PATOIS[letter]) + " "
            except KeyError:
                return "UNKNOWN PATOIS"
    return patois


def is_already_present(pagename):
    response = api.request(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "revisions",
            "rvprop": "content|timestamp",
            "titles": pagename,
        }
    )
    page = response["query"]["pages"][0]
    if "missing" in page:
        return False, 0
    else:
        return True, page["revisions"][0]["timestamp"]


def do_edit(page_name: str, wikicode, basetimestamp) -> bool:
    result = api.request(
        {
            "action": "edit",
            "format": "json",
            "formatversion": "2",
            "title": page_name,
            "summary": "Import automatisé du Dictionnaire des patois romans de la Moselle de Zéliqzon",
            "basetimestamp": basetimestamp,
            "text": wikicode,
            "token": api.get_csrf_token(),
        }
    )

    return "edit" in result


if __name__ == '__main__':
    FILENAME = "data_81-83"
    words = dict()
    rows_to_work_on = []
    with open(FILENAME + ".csv", 'r', encoding="utf-8", newline='') as data_file:
        csv_reader = csv.DictReader(data_file)
        fields = csv_reader.fieldnames

        for row in csv_reader:
            if not row["def1"]:
                rows_to_work_on.append(row)
                continue
            result = populate(row)
            if "UNKNOWN" in result:
                rows_to_work_on.append(row)
                continue
            # TODO gérer les "entrées multiples" (boc, par exemple, aura nom 1, nom 2, nom 3)
            print("[" + row["mot"] + "]")
            print(result)
            if row["mot"] in words.keys():
                result = words[row["mot"]] + "\n" + result
            words.update({row["mot"]: result})

    # print(rows_to_work_on)

    print(f"OK words/NEEDWORK words: {len(words)} / {len(rows_to_work_on)}")
    with open(FILENAME + ".remaining.csv", 'w', encoding="utf-8", newline='') as remaining:
        csv_writer = csv.DictWriter(remaining, fields)

        csv_writer.writeheader()
        csv_writer.writerows(rows_to_work_on)

    words_in_existing_pages = []

    # Send to Wiktionary
    accept = input("Send to Wiktionary ? [y/n]: ")
    if accept == 'y':
        config = configparser.ConfigParser()
        res = config.read(os.path.dirname(os.path.realpath(__file__)) + "/config.ini")
        if len(res) == 0:
            raise OSError("config.ini does not exist")
        user = config.get("wiki", "user")
        password = config.get("wiki", "password")
        api = pwb.Pywiki(user, password, "https://fr.wiktionary.org/w/api.php", "user")

        for word in words:
            present, basetimestamp = is_already_present(word)
            if not present:
                do_edit(word, words[word], basetimestamp)
                print(word)
                time.sleep(1)
            else:
                # Store in "remaining"
                words_in_existing_pages.append(word)

    for word in words_in_existing_pages:
        words.pop(word)

    print(f"OK words/NEEDWORK words: {len(words)} / {len(rows_to_work_on) + len(words_in_existing_pages)}")
    print(words_in_existing_pages)

