import csv

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
EBAUCHE_EXE = "{{ébauche-exe|lorrain}}"
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


if __name__ == '__main__':
    FILENAME = "first_subset"
    words = dict()
    rows_to_work_on = []
    with open(FILENAME + ".csv", 'r', encoding="utf-8", newline='') as data_file:
        csv_reader = csv.DictReader(data_file)
        fields = csv_reader.fieldnames

        for row in csv_reader:
            if not row["def1"]:
                rows_to_work_on.append(row)
                continue
            print("[" + row["mot"] + "]")
            result = populate(row)
            if "UNKNOWN" in result:
                rows_to_work_on.append(row)
                continue
            # TODO gérer les "entrées multiples" (boc, par exemple, aura nom 1, nom 2, nom 3)
            print(result)
            if row["mot"] in words.keys():
                result = words[row["mot"]] + "\n" + result
            words.update({row["mot"]: result})

    # print(rows_to_work_on)

    with open(FILENAME + ".remaining.csv", 'w', encoding="utf-8", newline='') as remaining:
        csv_writer = csv.DictWriter(remaining, fields)

        csv_writer.writeheader()
        csv_writer.writerows(rows_to_work_on)

    print(f"OK words/NEEDWORK words: {len(words)} / {len(rows_to_work_on)}")
