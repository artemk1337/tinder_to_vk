import json


def load_json(filename):
    with open(filename, 'r', encoding='utf8') as file:
        data = json.load(file)
    return data


def save_json(filename, text):
    with open(filename, 'w', encoding='utf8') as file:
        json.dump(text, file, indent=4, ensure_ascii=False)
