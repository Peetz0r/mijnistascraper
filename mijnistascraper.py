#!/bin/python3

import bs4, requests, configparser, datetime

config = configparser.ConfigParser()
config.read("config.ini")

session = requests.Session()

r = session.get("https://mijn.ista.nl/home/index")
s = bs4.BeautifulSoup(r.text, features="html.parser")
formAction = s.form['action']

r = session.post(formAction, data={"username": config["account"]["user"]})
s = bs4.BeautifulSoup(r.text, features="html.parser")
formAction = s.form['action']

r = session.post(formAction, data={"password": config["account"]["pass"]})
s = bs4.BeautifulSoup(r.text, features="html.parser")
formAction = s.form['action']

data = {}
for i in s.find_all('input'):
  data[i['name']] = i['value']

r = session.post(formAction, data=data)
s = bs4.BeautifulSoup(r.text, features="html.parser")
jwt = s.find("input", {"id": "__twj_"})["value"]

r = session.post("https://mijn.ista.nl/api/Values/UserValues", json={"JWT": jwt})
userValues = r.json()
jwt = userValues['JWT']
endDate = datetime.datetime.strptime(userValues['Cus'][0]['curConsumption']['CurEnd'], "%d-%m-%Y")

print("endDate:\t", endDate)

endDate = datetime.date.today()

print("endDate:\t", endDate)


def doThing(date):
  global jwt
  r = session.post("https://mijn.ista.nl/api/Values/ConsumptionValues", json={
    "JWT": jwt,
    "Cuid": userValues['Cus'][0]['Cuid'],
    "Billingperiod": {
      "s": date.strftime("%Y-%m-%d"),
      "e": date.strftime("%Y-%m-%dT23:59:59"),
    },
  })

  todaysValues = r.json()
  jwt = todaysValues['JWT']

  data = todaysValues['ServicesComp'][0]['CurMeters']

  print(f'[{date:%Y-%m-%d}]', end='      ')
  for meter in data:
    print(f'''[{f"{meter['MeterNr']:,}".replace(',',' ')} | {f"{meter['MeterId']}"}]  {meter['Position']:12s}  CV: {meter['CValue']:4.0f}  CCV: {meter['CCValue']:4.0f}  Begin: {meter['BeginValue']:4.0f}  End: {meter['EndValue']:4.0f}''', end='      ')
  print()

for i in range(28):
  date = endDate - datetime.timedelta(days=i)
  doThing(date)

