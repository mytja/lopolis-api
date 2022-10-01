import asyncio
import os

from lopolis import LoPolisAPI

async def main():
    lopolis = LoPolisAPI()
    print("Logging in")
    await lopolis.get_token(os.environ.get("LOPOLIS_USERNAME"), os.environ.get("LOPOLIS_PASSWORD"))
    print("Successfully logged in")
    menus = await lopolis.get_menus("2022", "10")
    print(menus)
    menus["2022-10-12T00:00:00.0000000"][0]["menu_options"][0]["selected"] = True
    print(await lopolis.set_menus("2022", "10", menus))
    checkouts = await lopolis.get_checkouts("2022", "10")
    print(checkouts)
    checkouts[list(checkouts.keys())[0]][0]["cancelled"] = True
    print(await lopolis.set_checkouts("2022", "10", checkouts))

asyncio.run(main())
