import psycopg2.extras
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup as soup
from time import sleep

class LinRegModel:
    def __init__(self):
        pass
    
    # --------------------------------------------------------------
    # "Public" Methods (can be called directly by user)-------------
    # --------------------------------------------------------------

    # Saves model
    def saveModel(self):
        pass

    # Loads model
    def loadModel(self):
        pass
    
    # Trains model
    def trainModel(self):
        pass
    
    # Loads data from Heroku Postgres
    def loadData(self):
        pass

    # Converts Postgres data to Pandas Dataframe
    def convertPostgresToDataframe(self):
        pass
    
    # Gets new data to save in Heroku Postgres
    def getNewData(self):
        vanUrl = '''https://www.rew.ca/properties/areas/vancouver-bc'''
        nycUrl = '''_'''
        torUrl = '''_'''
        sfUrl = '''_'''

        self.getVanDataRew(vanUrl)
    
    # --------------------------------------------------------------
    # "Private" Methods (should never be called directly by user)---
    # --------------------------------------------------------------

    # Scrapes https://www.rew.ca/properties/areas/vancouver-bc to get vancouver house data
    def getVanDataRew(self, url):
        url = url + "/page/"
        pages = [n for n in range(1, 26)]

        all_features = []

        for pageNum in pages:
            pageUrl = url + str(pageNum)
            # print(pageUrl)
        
            req = Request(
                pageUrl,
                data=None,
                headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'}
                )

            # Gets soup of current page
            client = urlopen(req)
            pageHtml = client.read()
            pageSoup = soup(pageHtml, "html.parser")
            # print(pageSoup)
            listingsOnPage = pageSoup.findAll("article", {"class": "listing listing--branded"})

            # Iterates over all listings and extracts features
            # all_features = []
            for listing in listingsOnPage:
                # if len(listing.find("ul", {"class": "listing-information"}).findAll("li")) == 3:
                try:
                    name = listing.find("span", {"class": "listing-address"}).a.text.replace('\n', '').replace('\r', '')
                    image_link = listing.find("div", {"class": "listing-photo"}).img["data-src"]
                    data_source = "rew"
                    location = "vancouver"
                    num_bed = listing.find("ul", {"class": "listing-information"}).findAll("li")[0].text.replace(" Bed", "")
                    num_bath = listing.find("ul", {"class": "listing-information"}).findAll("li")[1].text.replace(" Bath", "")
                    square_footage = listing.find("ul", {"class": "listing-information"}).findAll("li")[2].text.replace(" sf", "")
                    price_usd = listing.find("div", {"class": "listing-price"}).text.replace('$', '').replace(',', '')

                    # print(f"{name}, image_link, {data_source}, {location}, {num_bed}, {num_bath}, {square_footage}, {price_usd}")
                    all_features.append((name, image_link, data_source, location, square_footage, num_bed, num_bath, price_usd))
                except Exception:
                    print("Error with this listing: info missing (moving to next listing)")
            
            # Waits 5 seconds before scraping next page
            sleep(5)
            print(f"{pageUrl} done")

        client.close()
        print(len(all_features))
        print(len(all_features[len(all_features)-1]))
        self.insertDataIntoHerokuPostgres(all_features)

    # Inserts array of features into Heroku Postgres db
    def insertDataIntoHerokuPostgres(self, all_features):
        # print(all_features)
        DATABASE_URL = "postgres://dklxsxsaextmyw:dc202544829bbd460b5f5822b35c61b582f39ed4def680c1e79c7eed490c2ec0@ec2-174-129-18-247.compute-1.amazonaws.com:5432/d8l8j9bq8emjn4"
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        insertQuery = '''INSERT INTO residence (name, image_link, data_source, location, square_footage, num_bed, num_bath, price_usd) VALUES %s;'''
        
        for f in all_features:
            try:
                cursor.execute(insertQuery % str(f))
            except psycopg2.IntegrityError:
                print(psycopg2.IntegrityError)
            except psycopg2.InternalError:
                print(psycopg2.InternalError)
                # print("Rolling back...")
                conn.rollback()
        
            conn.commit()

# For debugging
if __name__ == "__main__":
    lrm = LinRegModel()
    lrm.getNewData()






    # DATABASE_URL = "postgres://dklxsxsaextmyw:dc202544829bbd460b5f5822b35c61b582f39ed4def680c1e79c7eed490c2ec0@ec2-174-129-18-247.compute-1.amazonaws.com:5432/d8l8j9bq8emjn4"
    # conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    # cursor = conn.cursor()

    # insertQuery = '''INSERT INTO residence (name, image_link, data_source, location, square_footage, num_bed, num_bath, price_usd) VALUES ('name_here111', 'link_here', 'source_here', 'location_here', 1, 2, 3, 4);'''    

    # try:
    #     cursor.execute(insertQuery)
    # except psycopg2.IntegrityError:
    #     print("That key already exists")

    # data = [
    #     ("name_here1", "link_here", "source_here", "location_here", 1, 2, 3, 4),
    #     ("name_here2", "link_here", "source_here", "location_here", 1, 2, 3, 4),
    #     ("name_here3", "link_here", "source_here", "location_here", 1, 2, 3, 4),
    #     ("name_here4", "link_here", "source_here", "location_here", 1, 2, 3, 4),
    #     ("name_here5", "link_here", "source_here", "location_here", 1, 2, 3, 4)]
    # insert_query = "insert into residence (name, image_link, data_source, location, square_footage, num_bed, num_bath, price_usd) values %s"
    # psycopg2.extras.execute_values(cursor, insert_query, data, template=None, page_size=100)
    # conn.commit()

    
    # cursor.execute("SELECT * FROM residence;")

    # data = cursor.fetchall()[0]
    # for d in data:
    #     print(d)