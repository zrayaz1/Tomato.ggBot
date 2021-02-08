import requests

apiUrl = "https://tomatobackend.herokuapp.com/api/abcd/moetracker/get/com"
r = requests.get(apiUrl)
with open('moedata1.txt','wb') as text_file:
	text_file.truncate()
	text_file.write(r.content)


