import requests
import json
apiUrl = "https://api.worldoftanks.com/wot/encyclopedia/vehicles/?application_id=20e1e0e4254d98635796fc71f2dfe741&fields=name%2Cnation%2Cis_gift%2Cis_premium%2Cshort_name%2Ctank_id%2Ctier%2Ctype"

def getTankData():
	with open("tanks.txt",'r') as testFile:
		data = json.load(testFile)
		return data['data']

def getTankNames(data):
	nameDict = {}
	for x in data:
		nameDict[x] = data[x]['short_name']
	reverse = {v: k for k, v in nameDict.items()}
	return reverse
