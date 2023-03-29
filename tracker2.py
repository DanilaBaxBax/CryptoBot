import requests

def scrape():
    response = requests.get(URL)
    response_json = response.json()
    return float(response_json["USD"]["last"])

URL = 'https://blockchain.info/ru/ticker'
last_price = None

#while True:
latest_price = scrape()
 
if latest_price != last_price:
    #print(latest_price)
    last_price = latest_price

  



