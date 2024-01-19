import io
import json
import locale

import psycopg2
import requests
from tkinter import *
from urllib.request import urlopen
from datetime import datetime as dt
from PIL import ImageTk, Image as Img

# Functie om een databaseverbinding te maken
def createConnection():
    with psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='Hsn35!',
        host='52.157.139.40',
        port='5432'
    ) as conn:
        return conn

# Functie om een databaseverbinding te sluiten
def closeConnection(conn):
    conn.close()

# Functie om stationnamen uit een bestand te lezen
def get_stations():
    with open('stations.txt') as file:
        return file.read().splitlines()

# Functie om faciliteiten voor een specifiek station uit de database te halen
def getFaciliteiten(station):
    with createConnection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ov_bike, elevator, toilet, park_and_ride FROM station_service "
                        "WHERE station_city=%s", [station])
            return cur.fetchone()

# Functie om een afbeelding voor een faciliteit te verkrijgen
def getFaciliteitImage(faciliteit):
    image_file = Img.open(f'Icons/{faciliteit}.png')
    image_file.resize((32, 32))
    return image_file

# Functie om weerinformatie voor een specifiek station te verkrijgen
def getWeerbericht(station):
    weather = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={station},nl&lang=nl&APPID'
                           f'=f662d7e76c05f726fed0413d66484c84')
    return json.loads(weather.content)

# Functie om een pictogram voor de weersomstandigheden te verkrijgen
def getWeerIcon(code):
    page = urlopen(f'http://openweathermap.org/img/wn/{code}.png').read()
    image = Img.open(io.BytesIO(page))
    image.resize((50, 50))
    return image

# Functie om recente beoordelingen voor een specifiek station uit de database te halen
def getRecentReviews(station):
    with createConnection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT r.bericht, r.naam FROM review AS r "
                        "INNER JOIN beoordeling AS b ON r.id = b.review_id "
                        "WHERE b.goedgekeurd = true AND station = %s "
                        "ORDER BY r.datum DESC LIMIT 5", [station])
            reviews = cur.fetchall()
            return reviews

# Functie om de huidige datum en tijd te verkrijgen
def getCurrentDate():
    locale.setlocale(locale.LC_TIME, 'nl_NL')
    return dt.strftime(dt.now(), '%A %w %B %Y, %H:%M:%S').capitalize()

# Klasse voor het scherm voor stationselectie
class SelectieScherm:
    def __init__(self, root):
        # Maak een container aan voor het selectiescherm waarin alle widgets worden geplaatst
        self.root = root
        self.root.title('Selecteer station')
        self.container = Frame(self.root, width=400, height=300)
        self.container.pack_propagate(False)
        self.container.pack(fill=BOTH, expand=True)

        # Initialiseer het selectiemenu
        stations = get_stations()
        placeholder = StringVar()
        placeholder.set(stations[0])
        self.selected_station = stations[0]

        # Initialiseer widgets
        self.title = Label(
            self.container,
            text='Selecteer uw station',
            font=('Arial', 20, 'bold')
        )
        self.subtitle = Label(
            self.container,
            text='Selecteer hier het station waarop u zich momenteel bevindt.',
            font=('Arial', 13)
        )
        self.select = OptionMenu(
            self.container,
            placeholder,
            *stations,
            command=self.set_selected_station
        )
        self.submit = Button(
            self.container,
            text='Verder',
            command=self.submit_station
        )
        self.title.pack(anchor=CENTER, pady=(90, 0))
        self.subtitle.pack(after=self.title, anchor=CENTER)
        self.select.pack(after=self.subtitle, pady=(10, 0), anchor=CENTER)
        self.submit.pack(after=self.select, anchor=CENTER)

    # Functie om het geselecteerde station in te stellen
    def set_selected_station(self, station):
        self.selected_station = station

    # Functie om het geselecteerde station in te dienen en naar het informatiescherm te gaan
    def submit_station(self):
        self.root.destroy()
        self.root = Tk()
        self.app = InfoScherm(self.root, self.selected_station)

# Klasse voor het informatiescherm
class InfoScherm:
    def __init__(self, root, station):

        self.root = root
        self.root.title('Stationsinformatie')
        self.root.geometry('600x400')
        self.station = station
        self.faciliteiten = getFaciliteiten(self.station)
        self.weerbericht = getWeerbericht(self.station)
        self.reviews = getRecentReviews(self.station)


        self.container = Frame(self.root)
        self.container.pack_propagate(False)
        self.container.pack(fill=BOTH, expand=True)

        self.container.columnconfigure(0, weight=1)
        self.container.columnconfigure(1, weight=3)
        self.container.columnconfigure(2, weight=3)
        self.container.rowconfigure(0, weight=2)
        self.container.rowconfigure(1, weight=3)
        self.container.rowconfigure(2, weight=3)
        self.container.rowconfigure(3, weight=1)


        self.title_container = Frame(self.container)
        self.title_container.grid(column=0, row=0, sticky=W, padx=30)
        self.title = Label(
            self.title_container,
            text='Welkom op station:',
            font=('Arial', 16),
            foreground='black'
        )
        self.title.grid(column=0, row=0, sticky=W)
        self.currentstation = Label(
            self.title_container,
            text=self.station,
            font=('Arial', 30, 'bold'),
        )
        self.currentstation.grid(column=0, row=1)


        self.weerbericht_container = Frame(self.container)
        self.weerbericht_container.grid(column=2, row=0, sticky=E, padx=30)

        temperatuur = int(self.weerbericht["main"]["temp"]) - 273  # Kelvin naar Celsius
        weerbericht = self.weerbericht["weather"][0]

        self.weerbericht_icon_image = ImageTk.PhotoImage(getWeerIcon(weerbericht["icon"]))
        self.weerbericht_icon = Label(
            self.weerbericht_container,
            image=self.weerbericht_icon_image,
        )
        self.weerbericht_icon.grid(column=0, row=0, rowspan=2)
        self.weerbericht_temp = Label(
            self.weerbericht_container,
            text=f'{temperatuur}°',
            font=('Arial', 30, 'bold')
        )
        self.weerbericht_temp.grid(column=1, row=0)
        self.weerbericht_desc = Label(
            self.weerbericht_container,
            text=weerbericht["description"].capitalize(),
            font=('Arial', 14)
        )
        self.weerbericht_desc.grid(column=1, row=1)


        soorten_faciliteiten = ['ov_fiets', 'lift', 'toilet', 'park_and_ride']
        labels_faciliteiten = ['OV-fiets', 'Lift', 'Toilet', 'P&R']
        self.faciliteiten_container = Frame(self.container)
        self.faciliteiten_container.grid(column=0, row=1, sticky=N, pady=(40, 0))
        self.faciliteiten_container.columnconfigure(0, weight=1)
        self.faciliteiten_container.columnconfigure(1, weight=1)
        self.faciliteiten_container.columnconfigure(2, weight=1)
        self.faciliteiten_container.columnconfigure(3, weight=1)

        self.faciliteiten_list = []
        self.faciliteiten_title = Label(
            self.faciliteiten_container,
            text='Beschikbare faciliteiten:',
            font=('Arial', 16, 'bold')
        )
        self.faciliteiten_title.grid(column=0, row=0)

        for faciliteit in soorten_faciliteiten:
            if self.faciliteiten[soorten_faciliteiten.index(faciliteit)]:
                faciliteit_container = Frame(self.faciliteiten_container)
                faciliteit_container.grid(row=len(self.faciliteiten_list)+1, column=0, columnspan=2, pady=5, sticky=W)

                image = ImageTk.PhotoImage(getFaciliteitImage(faciliteit).resize((50, 50)))
                faciliteit_image = Label(faciliteit_container, width=50, height=50, image=image)
                faciliteit_image.image = image
                faciliteit_image.grid(column=0, row=0)

                faciliteit_label = Label(
                    faciliteit_container,
                    text=labels_faciliteiten[soorten_faciliteiten.index(faciliteit)],
                    font=('Arial', 14)
                )
                faciliteit_label.grid(column=1, row=0, padx=10)

                self.faciliteiten_list.append(faciliteit)


        self.reviews_container = Frame(self.container)
        self.reviews_container.grid(column=2, row=1, sticky=NW, pady=(40, 0))
        self.reviews_container.rowconfigure(0, weight=1)
        self.reviews_container.rowconfigure(1, weight=1)

        self.reviews_title = Label(
            self.reviews_container,
            text='Over dit station',
            font=('Arial', 16, 'bold'),
        )
        self.reviews_title.grid(column=0, row=0, sticky=W)
        self.reviews_list = []

        if len(self.reviews) == 0:
            no_reviews = Label(
                self.reviews_container,
                text='Geen reviews van dit station.',
                font=('Arial', 13),
            )
            no_reviews.grid(column=0, row=1, sticky=W)
        for review in self.reviews:
            review_container = Frame(self.reviews_container)
            review_container.grid(column=len(self.reviews_list) % 2, columnspan=2, row=(len(self.reviews_list) // 2)+1, sticky=NW, pady=5)

            review_bericht = Label(
                review_container,
                text=review[0],
                font=('Arial', 14),
                wraplength=120,
                justify=LEFT
            )
            review_bericht.grid(row=0, column=0, sticky=W)
            review_naam = Label(
                review_container,
                text=f'- {review[1]}',
                font=('Arial', 12, 'italic'),
                justify=LEFT
            )
            review_naam.grid(row=1, column=0, sticky=W)

            self.reviews_list.append(review)


        self.footer = Frame(self.container, width=600, height=50)
        self.footer.grid(column=0, row=3, columnspan=3, sticky=S, pady=(0, 10))

        self.datum = Label(
            self.footer,
            font=('Arial', 14),
        )
        self.datum.grid(column=0, row=0, sticky=W)

        def updateTime():

            self.datum.config(text = getCurrentDate())
            self.datum.after(1000, updateTime)
        updateTime()

# Als het script direct wordt uitgevoerd
if __name__ == "__main__":
    root = Tk()
    app = SelectieScherm(root)
    root.mainloop()
