import requests
import json
api_url = 'https://api.worldoftanks.com/wot/account/list/?language=en&application_id=20e1e0e4254d98635796fc71f2dfe741&search={}'

r = requests.get(api_url)

test = r.json()
print(test['data'][0]['account_id'])