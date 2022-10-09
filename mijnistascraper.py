#!/bin/python3

import bs4, requests, configparser, pprint, datetime, time

config = configparser.ConfigParser()
config.read("config.ini")

session = requests.Session()

r = session.get("https://mijn.ista.nl/")
s = bs4.BeautifulSoup(r.text, features="html.parser")
loginRequestVerificationToken = s.find("form", {"id": "account"}).find("input", {"name": "__RequestVerificationToken"})["value"]

r = session.post("https://mijn.ista.nl/Identity/Account/Login", data={
    "txtUserName": config["account"]["user"],
    "txtPassword": config["account"]["pass"],
    "__RequestVerificationToken": loginRequestVerificationToken
  }, params={"ReturnUrl": "/"})
s = bs4.BeautifulSoup(r.text, features="html.parser")
jwt = s.find("input", {"id": "__twj_"})["value"]

r = session.post("https://mijn.ista.nl/api/Values/UserValues", json={"JWT": jwt})
userValues = r.json()
jwt = userValues['JWT']
endDate = datetime.datetime.strptime(userValues['Cus'][0]['curConsumption']['CurEnd'], "%d-%m-%Y")

print("endDate:\t", endDate)

for i in range(7):
  # +1 because data from endDate itself is still unavailable
  date = endDate - datetime.timedelta(days=i+1)

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

  print(date, end=' ')
  for i in todaysValues['ServicesComp'][0]['CurMeters']:
    print(i['CValue'], end=' ')
  print()

data = todaysValues['ServicesComp'][0]['CurMeters']

print(f"╭{'─'*18}┬{'─'*14}┬{'─'*14}╮")
for i in data[0]:
  print(f"│ {i:>16} │ {data[0][i]!s:12} │ {data[1][i]!s:12} │")
print(f"╰{'─'*18}┴{'─'*14}┴{'─'*14}╯")
