import requests
import json


API_ENDPOINT = "https://fr.wikisource.org/w/api.php"


def get_page_content(session: requests.Session, page: int) -> str:
    payload = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": "Page:Zéliqzon - Dictionnaire des patois romans de la Moselle, œuvre complète, 1924.djvu/" + str(page),
        "formatversion": "2",
        "rvprop": "content",
        "rvslots": "main"
    }
    request_result = session.post(API_ENDPOINT, data=payload)
    return json.loads(request_result.text)["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    START = 81
    END = 139
    with requests.Session() as s:
            s.headers.update({'User-Agent': 'User:Poslovitch'})
            lines = ""
            for i in range(START, END+1):
                print(i)
                content = get_page_content(s, i)
                lines += content

            lines = lines.replace('<section', '\n<section').replace('/>', '/>\n')  # add additional newlines

            with open(f"data_{START}-{END}.txt", 'w', encoding='utf-8') as printout:
                printout.writelines(lines)

