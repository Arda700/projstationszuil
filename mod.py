import csv
import locale
import psycopg2
from datetime import datetime as dt

# Functie om een databaseverbinding te maken en tabellen aan te maken indien deze nog niet bestaan
def createConnection():
    with psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='Hsn35!',
            host='52.157.139.40',
            port='5432'
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE TABLE IF NOT EXISTS review (id SERIAL PRIMARY KEY, bericht VARCHAR(140) NOT NULL, "
                "naam VARCHAR(40) NOT NULL, station VARCHAR(30) NOT NULL, datum TIMESTAMP NOT NULL); "

                "CREATE TABLE IF NOT EXISTS moderator (email VARCHAR(255) PRIMARY KEY, naam VARCHAR(40) NOT NULL);"

                "CREATE TABLE IF NOT EXISTS beoordeling (review_id INTEGER PRIMARY KEY REFERENCES review, goedgekeurd "
                "BOOLEAN NOT NULL, datum TIMESTAMP NOT NULL, moderator_email VARCHAR(255) REFERENCES moderator); "
            )
        return conn

# Functie om een databaseverbinding te sluiten
def closeConnection(conn):
    conn.close()

# Functie om reviews uit een CSV-bestand in de database in te voeren
def insertReviews(conn):
    try:
        with open('reviews.csv', 'r+') as reviews_file:
            reader = csv.reader(reviews_file, delimiter=',')
            reviews = list(reader)
            reviews_file.truncate(0)

            if len(reviews) > 0:
                print('Alle reviews importeren in de database...')
                with conn.cursor() as cur:
                    for review in reviews:
                        cur.execute(
                            "INSERT INTO review (bericht, naam, station, datum) "
                            "VALUES (%s, %s, %s, %s)", review
                        )
                    conn.commit()
                    print('Klaar!\n')
            else:
                print('Geen reviews om te importeren.')
    except FileNotFoundError:
        print('Geen reviews om te importeren.')

# Functie om onbeoordeelde reviews uit de database te halen
def getReviews(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * "
            "FROM review r "
            "WHERE NOT EXISTS "
            "(SELECT * FROM beoordeling b WHERE b.review_id = r.id);"
        )
        return cur.fetchall()

# Functie om de naam van een moderator op te halen
def getModeratorName(conn, moderator_email):
    with conn.cursor() as cur:
        cur.execute("SELECT naam FROM moderator "
                    "WHERE moderator.email = %s;", [moderator_email])
        data = cur.fetchone()

        if data:
            return data[0]

# Functie om een moderator toe te voegen aan de database
def insertModerator(conn, moderator_email, moderator_naam):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO moderator (email, naam) "
                    "VALUES (%s, %s);", [moderator_email, moderator_naam])
        conn.commit()

# Functie om een beoordeling aan de database toe te voegen
def insertBeoordeling(conn, beoordeling):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO beoordeling (review_id, goedgekeurd, datum, moderator_email) "
                    "VALUES (%s, %s, %s, %s)", beoordeling)
        conn.commit()

# Maak een databaseverbinding
conn = createConnection()

# Voer reviews in de database in
insertReviews(conn)

print('Moderator login\n---------------')
while True:
    moderator_email = input('Wat is uw e-mailadres?\n')
    if len(moderator_email.strip()) == 0:
        print('Vul uw e-mailadres in.')
        continue
    else:
        moderator_naam = getModeratorName(conn, moderator_email)
        if moderator_naam:
            print(f'Welkom terug, {moderator_naam}!\n')
        else:
            while True:
                moderator_naam = input('Wat is uw naam?\n')
                if len(moderator_naam.strip()) == 0:
                    print('Vul uw naam in.')
                    continue
                else:
                    insertModerator(conn, moderator_email, moderator_naam)
                    print(f'Welkom, {moderator_naam}!\n')
                    break
        break

# Stel de lokale tijd in op Nederlands
locale.setlocale(locale.LC_TIME, 'nl_NL')

beoordelingen = ['Afkeuren', 'Goedkeuren']
antwoorden = ['afgekeurd', 'goedgekeurd']

print('Beoordeel de volgende reviews:\n------------------------------')
for review in getReviews(conn):
    print(f'{review[2]} zei op {dt.strftime(review[4], "%w %B %Y, %H:M:%S")} in {review[3]}:\n{review[1]}')

    while True:
        beoordeling_input = input('Kies een beoordeling ("Afkeuren" of "Goedkeuren"): ').strip().lower()

        if beoordeling_input not in ["afkeuren", "goedkeuren"]:
            print('Ongeldige invoer. Kies "Afkeuren" of "Goedkeuren".')
        else:
            break

    goedgekeurd = (beoordeling_input == "goedkeuren")

    beoordeling_datum = dt.now()
    beoordeling = [review[0], goedgekeurd, beoordeling_datum, moderator_email]

    insertBeoordeling(conn, beoordeling)
    print(f'Succesvol {beoordeling_input}.\n')

print(f"Alle reviews zijn beoordeeld. Bedankt {moderator_naam}!")
closeConnection(conn)
