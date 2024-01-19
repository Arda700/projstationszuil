from datetime import datetime
import random

# Functie om de naam van de gebruiker op te vragen
def Naam():
    naam = input('Wat is uw naam? (niet verplicht)\n')

    if len(naam.strip()) == 0:
        naam = 'Anoniem'

    return naam

# Functie om de huidige datum en tijd op te halen
def Datum():
    return datetime.now()

# Functie om een willekeurig station uit het bestand 'stations.txt' te kiezen
def Station():
    with open('stations.txt', 'r+') as stations_file:
        stations = stations_file.read().splitlines()
        return random.choice(stations)

# Hoofdgedeelte van het script
while True:
    bericht = input('Laat hier uw bericht achter (max 140 tekens):\n')

    if len(bericht) > 140:
        print('Fout: uw bericht mag maximaal 140 tekens zijn.')
        continue
    elif len(bericht.strip()) == 0:
        print('Fout: u moet een bericht invullen.')
        continue
    else:
        # Creëer een review in het formaat 'bericht,naam,station,datum'
        review = f'{bericht},{Naam()},{Station()},{Datum()}\n'

        # Voeg de review toe aan het bestand 'reviews.csv'
        with open('reviews.csv', 'a+') as reviews_file:
            reviews_file.write(review)
            print('Gelukt! Bedankt voor uw bericht.')
            break
