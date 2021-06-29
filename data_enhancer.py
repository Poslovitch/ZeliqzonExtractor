import re
import csv


def parse_begin_section(l: str) -> str:
    return re.findall(r'<section begin=\"([^0-9]+)\"', l, re.UNICODE)[0]


def parse_end_section(l: str) -> str:
    return re.findall(r'<section end=\"([^0-9]+)\"', l, re.UNICODE)[0]


def find_and_replace_template(l: str, template: str) -> str:
    return re.sub(rf'{{{{{template}\|([^0-9\|]*)\|([^0-9\}}]+)}}}}', analyse_group, l)


def analyse_group(match_obj):
    if match_obj.group(2) is not None:
        return match_obj.group(2)


def pronunciation_to_IPA(pronunciation: str) -> str:
    TRADUCTOR = {
        'aⁱ': 'aj',
        'āᵒ': 'ɒ',
        'ā': 'aː',
        'ǟ': 'æː',
        'ä': 'æ',
        'ȩ': 'ə',
        'ę': 'ɛ',
        'ēⁱ': 'ej',
        'ē': 'eː',
        'œ̨': 'œ',
        'œ̄': 'øː',
        'œ': 'ø',
        'y': 'j',
        'ǖ': 'yː',
        'ü': 'y',
        'ū': 'uː',
        'ī': 'iː',
        's̆': 'ʃ',
        'ñ': 'ɲ',
        'ǫ': 'ɔ',
        'ōᵘ': 'oːw',
        'ō': 'oː',
        'õ': 'ɔ̃',
        'ã': 'ɑ̃',
        'ẽ': 'ɛ̃'
    }
    for key in TRADUCTOR:
        pronunciation = pronunciation.replace(key, TRADUCTOR[key])

    pronunciation = re.sub(r"[A-Z][a-z-é]*|général", "", pronunciation)

    # Getting rid of any useless ','
    pronunciation = pronunciation.replace(' ,', ',').strip()
    pronunciation = re.sub(r"[,]{2,}", ",", pronunciation)
    pronunciation = re.sub(r",$", "", pronunciation)

    return pronunciation


def extract_examples_from_definition(definition):
    all_examples_from_def = re.findall(r"(— )*''([^0-9']*~[^0-9']*)'', ([^0-9\n;]*)[.;]", definition)
    for k in range(len(all_examples_from_def)):
        all_examples_from_def[k] = all_examples_from_def[k][1] + "%" + all_examples_from_def[k][2]
    return '|'.join(all_examples_from_def), re.sub(r"(— )*''([^0-9']*~[^0-9']*)'', ([^0-9\n;]*)[.;]", "", definition)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    FILENAME = "data_81-83"

    # Reading through the file to find all the entries and their data
    entries = dict()
    with open(FILENAME + ".txt", 'r', encoding="utf-8") as data_file:

        current_entry = ''
        for line in data_file:
            if "<section begin=" in line:
                current_entry = parse_begin_section(line)
            elif "<section end=" in line:
                ending_entry = parse_end_section(line)
                if ending_entry == current_entry:
                    current_entry = ''
                else:
                    print(f"Mismatch: begin={current_entry}, end={ending_entry}")  # In case there are some mistakes
            else:
                if current_entry in entries.keys():
                    entries[current_entry] += line
                else:
                    entries[current_entry] = line

        entries.pop('')  # Delete the "empty" entry, which contains all the useless stuff
        print(f"Found {len(entries)} entries.")

    # Data sanitization time !
    for entry in entries:
        value = entries[entry]
        value = value.strip()  # Stripping the string of any trailing stuff

        # Applying the various templates
        value = find_and_replace_template(value, "abr")  # {{abr}}
        value = find_and_replace_template(value, "erratum")  # {{erratum}}
        value = find_and_replace_template(value, "corr")  # {{corr}}
        # FIXME : Bāchon

        entries[entry] = value  # And back into the dict!

    # Data csvisation time !

    CSV_COLUMNS = ['pageZel', 'mot', 'prononciation', 'IPA', 'nature/genre', "genericLocation", 'linkedVocab',
                   'def1', 'ex1', 'def2', 'ex2', 'def3', 'ex3', 'def4', 'ex4', 'def5', 'ex5', 'def6', 'ex6', 'def7', 'ex7', 'def8', 'ex8']
    csved = []

    for entry in entries:
        text = entries[entry]
        # split into as many entries as needed
        # Find the various times the entry appears
        pattern = re.compile(rf"\n+({re.escape(entry)})[, -]", re.UNICODE)
        r = pattern.search(text)
        end_indices = []
        if not r:
            print(f"Could not find the expected entry {entry} in : '{text}'.")
        while r:
            end_indices.append(r.end())
            r = pattern.search(text, r.end() + 1)

        for i in range(len(end_indices)):
            def_line = ''
            if i+1 < len(end_indices):
                def_line = text[end_indices[i]:(end_indices[i+1]-len(entry)-1)]
            else:
                def_line = text[end_indices[i]:]

            # extract pronunciation from the def_line
            pron = re.findall(r"\[''([, ()]|[^0-9]+)\]", def_line, re.UNICODE)
            genericLocation = ''
            if len(pron) > 0:
                def_line = def_line[len(pron[0]) + 6:]  # keep only the remaining part of the def_line
                pron = pron[0]  # we only keep one thing - so we turn pron to str
                pron = pron.replace('\n', '')
                pron = pron.replace("''", '').replace("..", "")  # Get rid of the .., they have no meanings in the wikt

                # Try to extract the pronunciation "area" ONLY IF THERE'S ONLY ONE PRONUNCIATION
                matches = re.findall(r"(?:[A-Z][a-z]*(?:, )*)+|général", pron, re.UNICODE)
                if len(matches) == 1:
                    genericLocation = matches[0]
                    pron = pron.replace(genericLocation, '').strip()  # Remove the location from the pron
                    genericLocation = genericLocation.replace(', ', '|').strip()  # Make it more easily parseable
                    genericLocation = re.sub(r"[A-Z][a-z]+", lambda match_obj: "c:" + match_obj.group(0), genericLocation)  # That should be a city so prefix it with "c:"
            else:
                pron = ''

            # extract genre from the def_line
            genre = ''
            if '—' in def_line:
                split_def_line = def_line.split('—', maxsplit=1)
                genre = split_def_line[0].strip()
                def_line = split_def_line[1].strip()
            elif not def_line.startswith("voir"):
                print(f"There is no '—' in the def line of {entry}")

            # Extract the DPRMLs and put them in linkedVocab
            DPRML_REGEX = r"{{DPRML\|(?:[^0-9}]+\|)*([^0-9}]+)}}"
            matches = re.findall(DPRML_REGEX, def_line, re.UNICODE)
            linkedVocab = '|'.join(matches).replace(', ', '|').lower()  # FIXME Handle for n. pr?

            # Turn them into proper "links"
            def_line = re.sub(DPRML_REGEX, lambda match_obj: "[[" + match_obj.group(1).lower() + "]]", def_line)  # FIXME Handle for n. pr?

            # Remove the "Voir X" links from the def line
            def_line = re.sub(r"Voir (?:\[\[[^0-9,.]+\]\](?:, |.)*)+", '', def_line)

            # split each entry by its ', '
            for word in entry.split(', '):
                # if genre is "n. pr." keep it uppercase
                if genre and genre != "n. pr.":
                    word = word.lower()

                # Split the various definitions
                def_lines = re.split(r"[0-9]° ", def_line)
                while len(def_lines) > 0 and not def_lines[0]:  # if the first one is empty
                    def_lines.pop(0)

                # Extract the examples and remove them from the definition lines
                # We're also doing some additional sanitization on the def lines
                all_examples = []
                for z in range(len(def_lines)):
                    examples, new_def_line = extract_examples_from_definition(def_lines[z])

                    # Sanitize the definition line and replace it
                    new_def_line = new_def_line.replace('\n', '')
                    new_def_line = new_def_line.strip()
                    def_lines[z] = new_def_line

                    # Replace ~ in examples
                    word_in_examples = re.sub(r" \(([^0-9]+)\)", "", word, re.UNICODE).strip()  # The word we replace the tilde with
                    examples = examples.replace("~", "'''" + word_in_examples + "'''")

                    all_examples.append(examples)

                # put the (è), (au), (an), (so) etc. before the word
                r = re.search(r" \(([^0-9]+)\)", word, re.UNICODE)
                if r:
                    word = word[r.start() + 2:r.end() - 1] + ' ' + word[:r.start()]

                csv_entry = {
                    CSV_COLUMNS[0]: entry,
                    CSV_COLUMNS[1]: word,
                    CSV_COLUMNS[2]: pron,
                    CSV_COLUMNS[3]: pronunciation_to_IPA(pron),
                    CSV_COLUMNS[4]: genre,
                    CSV_COLUMNS[5]: genericLocation,
                    CSV_COLUMNS[6]: linkedVocab
                }

                # Add all the definitions
                for j in range(0, len(def_lines)):
                    csv_entry.update({CSV_COLUMNS[(2*j)+7]: def_lines[j]})
                    csv_entry.update({CSV_COLUMNS[(2*j+1)+7]: all_examples[j]})

                # add to the csv
                csved.append(csv_entry)

    print(f"Found {len(csved)} actual 'words'.")

    with open(FILENAME + ".csv", 'w', encoding='utf-8', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for item in csved:
            writer.writerow(item)
