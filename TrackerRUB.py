import requests
data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
data2 =  (data['Valute']['USD']['Value'])
print (data2)
