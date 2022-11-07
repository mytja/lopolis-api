import asyncio
import os

from lopolis import LoPolisAPI

async def main():
    lopolis = LoPolisAPI()
    print("Logging in")
    await lopolis.get_token(os.environ.get("LOPOLIS_USERNAME"), os.environ.get("LOPOLIS_PASSWORD"))
    print("Successfully logged in")
    menus = await lopolis.get_menus("2022", "11")
    print(menus)
    menu_date = "2022-11-18T00:00:00.0000000"
    for i in range(len(menus[menu_date][0]["menu_options"])):
        menus[menu_date][0]["menu_options"][i]["selected"] = False
    menus[menu_date][0]["menu_options"][-1]["selected"] = True
    print(await lopolis.set_menus("2022", "11", menus))
    #checkouts = await lopolis.get_checkouts("2022", "10")
    #print(checkouts)
    #checkouts[list(checkouts.keys())[0]][0]["cancelled"] = True
    #print(await lopolis.set_checkouts("2022", "10", checkouts))

asyncio.run(main())
