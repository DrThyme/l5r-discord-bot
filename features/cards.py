import urllib
import requests
import json
import datetime
from fuzzywuzzy import process
import logging

logger = logging.getLogger('discord')


def get_card_url(command):
    logger.info("Getting a card URL for " + str(command))
    card_name = ''

    for string in command:
        if card_name != '':
            card_name += ' '
        card_name += string.lower()

    valid_name, cards_or_pack = validate_card_name(card_name)
    if valid_name:
        card_name = urllib.parse.unquote(card_name)
        card_name = card_name.replace("'", "-")
        card_name = card_name.replace(" ", "-")
        card_name = card_name.replace("!", "")
        logger.info("It's a valid card, posting the URL now")
        return "https://l5rdb.net/lcg/cards/" + cards_or_pack + "/" + card_name + ".jpg"
    else:
        message = ""
        for card, _ in cards_or_pack:
            if message != "":
                message += ", "
            message += prettify_name(card)
        logger.info("It's not a valid card, posting alternatives now")
        return "I'm sorry, honourable samurai-san, but this card is not known. \n" + \
               "Perhaps you meant one of these three? \n" + message


def validate_card_name(card_name):
    """Returns the card name or potential alternatives."""

    logger.info("Checking whether the card is an existing card")
    with open('card_db.json', 'r') as json_data:
        try:
            db_records = json.load(json_data)
        except json.decoder.JSONDecodeError:
            db_records = {}

    if db_records == {} or (datetime.datetime.strptime(db_records['last_updated'], "%Y-%m-%dT%H:%M:%S") - datetime.datetime.today()).days < 0:
        logger.info("Updating Card DB")
        r = requests.get("https://api.fiveringsdb.com/cards")
        request_data = r.json()

        db_records['last_updated'] = request_data['last_updated'][:-6]
        card_names = {}
        for card in request_data['records']:
            pack_name = card['pack_cards'][0]['pack']['id']
            card_names[card['name_canonical']] = pack_name
        db_records['cards'] = card_names
        with open('card_db.json', 'w') as outfile:
            json.dump(db_records, outfile)
            logger.info('Saved new card_db to file')

    if card_name in db_records['cards']:
        logger.info("Found card in DB")
        return True, db_records['cards'][card_name]

    logger.info("Presenting alternatives")
    potentials = process.extract(card_name, set(db_records['cards']), limit=3)
    return False, potentials


def prettify_name(cardname):
    cardname = cardname.split(" ")
    pretty = ""
    for word in cardname:
        pretty += word.capitalize() + " "

    return pretty
