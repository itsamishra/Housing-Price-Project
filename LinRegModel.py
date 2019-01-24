import psycopg2.extras
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup as soup
from time import sleep
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from pickle import dump, load


class LinRegModel:
    # Constructor
    def __init__(self):
        # Dict that holds price-prediction model for each of 4 locations
        self.models = {}

    # --------------------------------------------------------------
    # "Public" Methods (can be called directly by user)-------------
    # --------------------------------------------------------------

    # Loads model from local environment
    def load_model(self):
        locations = ['vancouver', 'toronto', 'new york city', 'san francisco']
        for location in locations:
            model = load(open(f'lin_reg_model_{location.replace(" ", "_")}.pickle', "rb"))
            self.models[location] = model

        # print(self.models)
        # print(self.models["toronto"].predict([[9000, 4, 4]]))

    # Trains model, then saves to local environment
    def train_model(self):
        df = self.load_all_data_as_dataframe()

        # Creates model for each of 4 locations
        locations = ['vancouver', 'toronto', 'new york city', 'san francisco']
        for location in locations:
            location_df = df[df["location"] == location]
            square_footage = location_df["square_footage"]
            num_bed = location_df["num_bed"]
            num_bath = location_df["num_bath"]
            price_usd = location_df["price_usd"]

            # Creates feature array
            feature_array = np.stack((square_footage, num_bed, num_bath), -1).astype(float)

            # Generates linear regression model
            lin_reg = LinearRegression()
            lin_reg.fit(feature_array, price_usd)

            # Saves model locally
            dump(lin_reg, open(f'lin_reg_model_{location.replace(" ", "_")}.pickle', "wb"))

    # Gets new data to save in Heroku Postgres
    def get_new_data(self):
        van_url = '''https://www.rew.ca/properties/areas/vancouver-bc'''
        tor_url = '''https://www.zolo.ca/toronto-real-estate/'''
        nyc_url = '''https://www.realtor.com/realestateandhomes-search/New-York-City_NY/'''
        sf_url = '''https://zephyrre.com/properties/'''

        self.get_van_data_rew(van_url)
        self.get_tor_data_zolo(tor_url)
        self.get_nyc_data_realtor(nyc_url)
        self.get_sf_data_zephyrre(sf_url)

    # Predicts price of house in given location with given features
    def predict_price(self, location, features):
        return self.models[location].predict([features])

    # --------------------------------------------------------------
    # "Private" Methods (should never be called directly by user)---
    # --------------------------------------------------------------

    # Scrapes https://www.rew.ca/properties/areas/vancouver-bc to get vancouver house data
    def get_van_data_rew(self, url):
        # List of all names (i.e. primary keys) currently in database
        name_list = self.get_all_names_from_database()

        # Builds base URL
        url = url + "/page/"
        pages = [n for n in range(1, 26)]

        # List that will contain all features extracted from website
        all_features = []

        # Iterates over all pages of website
        for page_num in pages:
            # Builds this page's URL
            page_url = url + str(page_num)

            # Creates soup of current page
            req = Request(page_url, data=None, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})
            client = urlopen(req)
            page_html = client.read()
            page_soup = soup(page_html, "html.parser")

            # Finds all listings on current page
            listings_on_page = page_soup.findAll("article", {"class": "listing listing--branded"})

            # Iterates over all listings and extracts features
            for listing in listings_on_page:
                try:
                    name = listing.find("span", {"class": "listing-address"}).a.text.replace('\n', '').replace('\r', '')
                    image_link = listing.find("div", {"class": "listing-photo"}).img["data-src"]
                    data_source = "rew"
                    location = "vancouver"
                    num_bed = listing.find("ul", {"class": "listing-information"}).findAll("li")[0].text.replace(" Bed", "")
                    num_bath = listing.find("ul", {"class": "listing-information"}).findAll("li")[1].text.replace(" Bath", "")
                    square_footage = listing.find("ul", {"class": "listing-information"}).findAll("li")[2].text.replace(" sf", "")
                    price_usd = listing.find("div", {"class": "listing-price"}).text.replace('$', '').replace(',', '')

                    # Makes sure current listing is't already in database
                    if name not in name_list:
                        all_features.append((name, image_link, data_source, location, square_footage, num_bed, num_bath, price_usd))
                        name_list.append(name)
                    else:
                        print(f"Skipping {name} because it's already in database")
                except Exception:
                    print("Error with this listing: info missing (moving to next listing)")

            # Waits 5 seconds before scraping next page
            sleep(5)
            print(f"{page_url} done")

        print(f"allFeatures: {all_features}\nlen: {len(all_features)}")
        client.close()

        self.insert_data_into_heroku_postgres(all_features)

    # Scrapes https://www.zolo.ca/toronto-real-estate/ to get Toronto house data
    def get_tor_data_zolo(self, url):
        # List of all names (i.e. primary keys) currently in database
        name_list = self.get_all_names_from_database()

        # Builds base URL
        url += "page-"
        pages = [n for n in range(1, 165)]

        # List that will contain all features extracted from website
        all_features = []

        for page_num in pages:
            # Builds this page's URL
            page_url = url + str(page_num)
            print(page_url)

            # Creates soup of current page
            req = Request(page_url, data=None, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})
            client = urlopen(req)
            page_html = client.read()
            page_soup = soup(page_html, "html.parser")

            listings_on_page = page_soup.findAll("li", {"class": "listing-column text-4"})

            for listing in listings_on_page:
                try:
                    name = listing.find("span", {"class": "street"}).text
                    image_link = listing.find("a", {"class": "xs-block xs-aspect-3-2 fill-grey-bg card-listing--image-link"}).img["data-img-defer-src"]
                    data_source = "zolo"
                    location = "toronto"
                    num_bed = listing.find("ul", {"class": "card-listing--values truncate list-unstyled xs-flex-order-1"}).findAll("li")[1].text.replace(" bd", "")
                    num_bath = listing.find("ul", {"class": "card-listing--values truncate list-unstyled xs-flex-order-1"}).findAll("li")[2].text.replace("•", "").replace(" ba", "")
                    square_footage_list = list(map(float, listing.find("ul", {"class": "card-listing--values truncate list-unstyled xs-flex-order-1"}).findAll("li")[3].text.replace("•", "").replace(" sqft", "").replace("+", "").split("-")))
                    square_footage = sum(square_footage_list)/len(square_footage_list)
                    price_usd = listing.find("span", {"itemprop": "price"})["value"]

                    # Makes sure current listing is't already in database
                    if (name not in name_list) and ('-' not in num_bed) and ('-' not in num_bath):
                        all_features.append((name, image_link, data_source, location, square_footage, num_bed, num_bath, price_usd))
                        name_list.append(name)
                    else:
                        print(f"Skipping {name} because it's already in database")
                except Exception:
                    print("Error with this listing: info missing (moving to next listing)")

            # Waits 5 seconds before scraping next page
            sleep(5)
            print(f"{page_url} done")

        print(f"allFeatures: {all_features}\nlen: {len(all_features)}")
        client.close()

        self.insert_data_into_heroku_postgres(all_features)

    def get_nyc_data_realtor(self, url):
        # List of all names (i.e. primary keys) currently in database
        name_list = self.get_all_names_from_database()

        # List that will contain all features extracted from website
        all_features = []

        pages = [n for n in range(1, 86)]

        for page_num in pages:
            page_url = url + "pg-" + str(page_num)
            print(page_url)

            # Creates soup of current page
            req = Request(page_url, data=None, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})
            client = urlopen(req)
            page_html = client.read()
            page_soup = soup(page_html, "html.parser")

            listings_on_page = page_soup.findAll("li", {"class": "component_property-card js-component_property-card js-quick-view"})

            for listing in listings_on_page:
                try:
                    name = listing.find("span", {"class": "listing-street-address"}).text
                    image_link = listing.find("img", {"class": "main-photo"})["src"]
                    data_source = "realtor"
                    location = "new york city"
                    num_bed = listing.find("span", {"class": "data-value meta-beds"}).text.replace("+", "")
                    num_bath = listing.find("li", {"data-label": "property-meta-baths"}).span.text.replace("+", "")
                    try:
                        square_footage = listing.find("li", {"data-label": "property-meta-sqft"}).span.text.replace("+", "").replace(",", "")
                    except Exception:
                        square_footage = listing.find("li", {"data-label": "property-meta-lotsize"}).span.text.replace("+", "").replace(",", "")
                    price_usd = listing.find("span", {"class": "data-price"}).text.replace("$", "").replace(",", "")

                    # Makes sure current listing is't already in database
                    if name not in name_list:
                        all_features.append((name, image_link, data_source, location, square_footage, num_bed, num_bath, price_usd))
                        name_list.append(name)
                except Exception:
                    print("Error with this listing: info missing (moving to next listing)")

            # Waits 5 seconds before scraping next page
            sleep(5)
            print(f"{page_url} done")

        print(f"allFeatures: {all_features}\nlen: {len(all_features)}")
        client.close()

        self.insert_data_into_heroku_postgres(all_features)

    def get_sf_data_zephyrre(self, url):
        # List of all names (i.e. primary keys) currently in database
        name_list = self.get_all_names_from_database()

        # List that will contain all features extracted from website
        all_features = []

        pages = [n for n in range(1, 201)]

        for page_num in pages:
            page_url = url + "page/" + str(page_num)
            print(page_url)

            # Creates soup of current page
            req = Request(page_url, data=None, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})
            client = urlopen(req)
            page_html = client.read()
            page_soup = soup(page_html, "html.parser")

            listings_on_page = page_soup.findAll("div", {"class": "idx-listing__wrapper idx-listing listing-table "})

            for listing in listings_on_page:
                try:
                    name = listing.find("span", {"class": "idx-address idx-address-value"}).text
                    image_link = ""         # No image link
                    data_source = "zephyrre"
                    location = "san francisco"
                    num_bed = listing.find("span", {"class": " idx-beds-value"}).text.replace(" ", "")
                    num_bath = listing.find("span", {"class": "idx-baths-value"}).text.replace(" ", "")
                    square_footage = listing.find("span", {"class": "listing-square-feet idx-square-feet-value"}).text.replace(" ", "").replace("\n", "").replace(",", "")
                    price_usd = listing.find("span", {"class": "listing-price idx-price-value"}).text.replace(" ", "").replace(",", "")

                    if (num_bed == "") or (num_bath == "") or (square_footage == "") or (price_usd == ""):
                        raise Exception

                    # Makes sure current listing is't already in database
                    if name not in name_list:
                        all_features.append((name, image_link, data_source, location, square_footage, num_bed, num_bath, price_usd))
                        name_list.append(name)

                except Exception:
                    print("Error with this listing: info missing (moving to next listing)")

            # Waits 5 seconds before scraping next page
            sleep(5)
            print(f"{page_url} done")

        print(f"allFeatures: {all_features}\nlen: {len(all_features)}")
        client.close()

        self.insert_data_into_heroku_postgres(all_features)

    # Inserts array of features into Heroku Postgres db
    def insert_data_into_heroku_postgres(self, all_features):
        # print(all_features)
        DATABASE_URL = "postgres://dklxsxsaextmyw:dc202544829bbd460b5f5822b35c61b582f39ed4def680c1e79c7eed490c2ec0" \
                       "@ec2-174-129-18-247.compute-1.amazonaws.com:5432/d8l8j9bq8emjn4"
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        query = '''INSERT INTO residence (name, image_link, data_source, location, square_footage, num_bed, num_bath, price_usd) VALUES %s;'''
        psycopg2.extras.execute_values(cursor, query, all_features)
        conn.commit()

    # Returns list of all current names (i.e. primary keys) in database
    def get_all_names_from_database(self):
        DATABASE_URL = "postgres://dklxsxsaextmyw:dc202544829bbd460b5f5822b35c61b582f39ed4def680c1e79c7eed490c2ec0" \
                       "@ec2-174-129-18-247.compute-1.amazonaws.com:5432/d8l8j9bq8emjn4"
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM residence;")

        all_names = cursor.fetchall()
        name_list = [n[0] for n in all_names]

        return name_list

    # Loads data from Heroku Postgres
    def load_all_data_as_dataframe(self):
        DATABASE_URL = "postgres://dklxsxsaextmyw:dc202544829bbd460b5f5822b35c61b582f39ed4def680c1e79c7eed490c2ec0" \
                       "@ec2-174-129-18-247.compute-1.amazonaws.com:5432/d8l8j9bq8emjn4"
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        cursor.execute("SELECT location, square_footage, num_bed, num_bath, price_usd FROM residence;")

        housing_data_raw = np.array(cursor.fetchall())
        df = pd.DataFrame({'location': housing_data_raw[:, 0],
                           'square_footage': housing_data_raw[:, 1],
                           'num_bed': housing_data_raw[:, 2],
                           'num_bath': housing_data_raw[:, 3],
                           'price_usd': housing_data_raw[:, 4]})

        return df


# For debugging
if __name__ == "__main__":
    lrm = LinRegModel()
    # lrm.get_new_data()
    lrm.train_model()
    lrm.load_model()
    print("Result:")
    print(lrm.predict_price("toronto", [9000, 4, 4]))
    # print(self.models["toronto"].predict([[9000, 4, 4]]))
