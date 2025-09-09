import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv("CLICKUP_API_TOKEN")

def list_accessible_lists():
    headers = {"Authorization": API_TOKEN}

    # Step 1: Get teams
    team_res = requests.get("https://api.clickup.com/api/v2/team", headers=headers)
    team_id = team_res.json()["teams"][0]["id"]

    # Step 2: Get spaces
    space_res = requests.get(f"https://api.clickup.com/api/v2/team/{team_id}/space", headers=headers)
    spaces = space_res.json().get("spaces", [])

    for space in spaces:
        print(f"\n🗂️ Space: {space['name']} ({space['id']})")
        # Step 3: Get lists in each space
        list_res = requests.get(f"https://api.clickup.com/api/v2/space/{space['id']}/list", headers=headers)
        lists = list_res.json().get("lists", [])
        for l in lists:
            print(f"   ✅ List: {l['name']} (ID: {l['id']})")

if __name__ == "__main__":
    list_accessible_lists()
