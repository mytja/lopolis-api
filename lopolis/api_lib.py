import re

import httpx
from bs4 import BeautifulSoup

HOST = "https://web.lopolis.si"


class LoPolisAPI:
    def __init__(self):
        self.oseba_model = None
        self.ustanova_id = None
        self.oseba_id = None
        self.oseba_tip = None
        self.client = httpx.AsyncClient()

    async def get_token(self, username, password):
        json_data = {
            "Uporabnik": username,
            "Geslo": password,
            "OsveziURL": "",
        }

        response = await self.client.post("https://web.lopolis.si/Uporab/Prijava2", data=json_data)

        if response.status_code != 301:
            raise Exception({"error": True, "status_code": response.status_code})
        if self.client.cookies.get(".LopolisPortalAuth") is None:
            raise Exception("Unauthorized")

        await self.client.get(HOST)
        response = await self.client.get(f"{HOST}/?MeniZgorajID=6&MeniID=78")
        soup = BeautifulSoup(response.text, "html.parser")
        self.oseba_model = soup.find(id="OsebaModel_ddlOseba").find("option").attrs["value"]
        try:
            self.oseba_id, self.oseba_tip, self.ustanova_id = self.oseba_model.split(";")
        except:
            raise Exception("Unauthorized")

    async def get_menus(self, year, month):
        response = await self.client.get(f"{HOST}/Prehrana/Prednarocanje")
        soup = BeautifulSoup(response.text, "html.parser")
        verification_token = soup.find("input", {"name": "__RequestVerificationToken"}).attrs["value"]

        json_data = {
            "__RequestVerificationToken": verification_token,
            "Ukaz": "",
            "OsebaModel.ddlOseba": self.oseba_model,
            "OsebaModel.OsebaID": self.oseba_id,
            "OsebaModel.OsebaTipID": self.oseba_tip,
            "OsebaModel.UstanovaID": self.ustanova_id,
            "MesecModel.Mesec": month,
            "MesecModel.Leto": year,
            "X-Requested-With": "XMLHttpRequest",
        }

        response = await self.client.post(f"{HOST}/Prehrana/Prednarocanje", data=json_data)
        soup = BeautifulSoup(response.text, "html.parser")
        meals = soup.find("tbody").find_all("tr")

        menu = {}

        if meals is None:
            raise Exception("Unauthorized")
        for tr in meals:
            day_output = {}
            tds = tr.find_all("td")

            day_output["meal"] = tds[1].text.strip()
            day_output["menu_type"] = tds[2].text.strip()
            day_output["location"] = tds[3].text.strip()
            day_output["menu_options"] = []

            menu_content = tds[4]

            day_output["local_id"] = int(menu_content.find(id=re.compile(r"PrednarocanjeItems_(.*)__ABO_PrijavaID")).get("id").split("_")[1])
            day_output["id"] = menu_content.find(id=re.compile(r"PrednarocanjeItems_(.*)__ABO_PrijavaID")).attrs["value"]

            menu_options = [x for x in menu_content.contents[0].contents if x != "\n"]

            date = menu_content.contents[2]["value"]
            empty = False

            if menu.get(date) is None:
                menu[date] = []

            if menu_content.contents[0].get("readonly") != "readonly":
                day_output["readonly"] = False
                if len(menu_options) > 1:
                    for option in menu_options:
                        if option.get("value") != "":
                            menu_output = {"value": option.get("value"), "text": option.contents[0],
                                           "selected": (
                                               not option.get("selected") is None
                                           )}
                            day_output["menu_options"].append(menu_output)
                else:
                    empty = True
            else:
                menu_output = None
                for option in menu_options:
                    if (
                            not option.get("value") == ""
                            and not option.get("selected") is None
                            and not option.contents[0] == ""
                    ):
                        menu_output = {
                            "value": option.get("value"),
                            "text": option.contents[0],
                            "selected": True,
                        }
                        day_output["readonly"] = True

                if menu_output is not None:
                    day_output["menu_options"].append(menu_output)
                else:
                    empty = True

            #if not empty:
            menu[date].append(day_output)

        return menu

    async def get_checkouts(self, year, month):
        response = await self.client.get(f"{HOST}/Prehrana/Odjava")
        soup = BeautifulSoup(response.text, "html.parser")
        verification_token = soup.find("input", {"name": "__RequestVerificationToken"}).attrs["value"]

        json_data = {
            "__RequestVerificationToken": verification_token,
            "Ukaz": "",
            "OsebaModel.ddlOseba": self.oseba_model,
            "OsebaModel.OsebaID": self.oseba_id,
            "OsebaModel.OsebaTipID": self.oseba_tip,
            "OsebaModel.UstanovaID": self.ustanova_id,
            "MesecModel.Mesec": month,
            "MesecModel.Leto": year,
            "X-Requested-With": "XMLHttpRequest",
        }

        response = await self.client.post(f"{HOST}/Prehrana/Odjava", data=json_data)
        soup = BeautifulSoup(response.text, "html.parser")
        meals = soup.find("tbody").find_all("tr")
        checkouts = {}
        for tr in meals:
            tds = tr.find_all("td")
            checkbox_contents = tds[3].find_all("input")
            date = tds[0].text.strip()
            if checkouts.get(date) is None:
                checkouts[date] = []
            checkouts[date].append(
                {
                    "meal_type": tds[1].contents[0].split("\r")[0],
                    "disabled": checkbox_contents[0].get("disabled") is not None,
                    "cancelled": checkbox_contents[0].get("checked") is not None,
                    "location": tds[2].text.strip(),
                    "date": tds[0].text.strip(),
                    "full_date": checkbox_contents[2].attrs["value"].strip(),
                    "checkout_type": tds[4].text.strip(),
                    "checkout_id": checkbox_contents[3].attrs["value"],
                    "checkout_local_id": int(checkbox_contents[0].get("id").split("_")[1]),
                }
            )

        return checkouts

    # choices is the checkout object (dict) from before.
    async def set_checkouts(self, year, month, choices):
        response = await self.client.get(f"{HOST}/Prehrana/Odjava")
        soup = BeautifulSoup(response.text, "html.parser")
        verification_token = soup.find("input", {"name": "__RequestVerificationToken"}).attrs["value"]

        json_data = {
            "__RequestVerificationToken": verification_token,
            "Ukaz": "",
            "OsebaModel.ddlOseba": self.oseba_model,
            "OsebaModel.OsebaID": self.oseba_id,
            "OsebaModel.OsebaTipID": self.oseba_tip,
            "OsebaModel.UstanovaID": self.ustanova_id,
            "MesecModel.Mesec": month,
            "MesecModel.Leto": year,
            "X-Requested-With": "XMLHttpRequest",
        }

        response = await self.client.post(f"{HOST}/Prehrana/Odjava", data=json_data)
        soup = BeautifulSoup(response.text, "html.parser")
        verification_token = soup.find("input", {"name": "__RequestVerificationToken"}).attrs["value"]

        json_data = {
            "Shrani": "Shrani",
            "__RequestVerificationToken": verification_token,
            "Ukaz": "Shrani",
            "OsebaModel.ddlOseba": self.oseba_model,
            "OsebaModel.OsebaID": self.oseba_id,
            "OsebaModel.OsebaTipID": self.oseba_tip,
            "OsebaModel.UstanovaID": self.ustanova_id,
            "MesecModel.Mesec": month,
            "MesecModel.Leto": year,
            "X-Requested-With": "XMLHttpRequest",
        }

        for day in choices.values():
            for i in day:
                full_date = i["full_date"]
                cancelled = i["cancelled"]
                checkout_id = i["checkout_id"]
                checkout_local_id = i["checkout_local_id"]
                disabled = i["disabled"]

                odjava_item = f"OdjavaItems[{checkout_local_id}]."
                if bool(cancelled):
                    json_data[f"{odjava_item}CheckOut"] = ["true", "false"]
                else:
                    json_data[f"{odjava_item}CheckOut"] = "false"
                json_data[f"{odjava_item}Datum"] = full_date
                json_data[f"{odjava_item}ABO_PrijavaID"] = checkout_id
                json_data[f"{odjava_item}ReadOnly"] = "True" if disabled else "False"

        response = await self.client.post(f"{HOST}/Prehrana/Odjava", data=json_data)
        return response.status_code

    async def set_menus(self, year, month, choices):
        response = await self.client.get(f"{HOST}/Prehrana/Prednarocanje")
        soup = BeautifulSoup(response.text, "html.parser")
        verification_token = soup.find("input", {"name": "__RequestVerificationToken"}).attrs["value"]

        json_data = {
            "__RequestVerificationToken": verification_token,
            "Ukaz": "",
            "OsebaModel.ddlOseba": self.oseba_model,
            "OsebaModel.OsebaID": self.oseba_id,
            "OsebaModel.OsebaTipID": self.oseba_tip,
            "OsebaModel.UstanovaID": self.ustanova_id,
            "MesecModel.Mesec": month,
            "MesecModel.Leto": year,
            "X-Requested-With": "XMLHttpRequest",
        }

        response = await self.client.post(f"{HOST}/Prehrana/Prednarocanje", data=json_data)
        soup = BeautifulSoup(response.text, "html.parser")
        verification_token = soup.find("input", {"name": "__RequestVerificationToken"}).attrs["value"]

        json_data = {
            "Shrani": "Shrani",
            "__RequestVerificationToken": verification_token,
            "Ukaz": "Shrani",
            "OsebaModel.ddlOseba": self.oseba_model,
            "OsebaModel.OsebaID": self.oseba_id,
            "OsebaModel.OsebaTipID": self.oseba_tip,
            "OsebaModel.UstanovaID": self.ustanova_id,
            "MesecModel.Mesec": month,
            "MesecModel.Leto": year,
            "X-Requested-With": "XMLHttpRequest",
        }

        for i, (k, v) in enumerate(choices.items()):
            full_date = k

            for meal in v:
                id = meal["id"]
                local_id = meal["local_id"]
                try:
                    disabled = meal["readonly"]
                except:
                    disabled = True

                selected = ""
                for menu in meal["menu_options"]:
                    if menu["selected"]:
                        selected = menu["value"]
                        break

                item = f"PrednarocanjeItems[{local_id}]."
                if not disabled:
                    json_data[f"{item}MeniIDSkupinaID"] = selected
                json_data[f"{item}Datum"] = full_date
                json_data[f"{item}ABO_PrijavaID"] = id
                json_data[f"{item}ReadOnly"] = "True" if disabled else "False"

        #print(json_data)
        response = await self.client.post(f"{HOST}/Prehrana/Prednarocanje", data=json_data)
        #print(response.text)
        return response.status_code
