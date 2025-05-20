import os
import requests

url = "https://proceedings.mlr.press/v26/nicol12a/nicol12a.pdf"
response = requests.get(url)
if response.status_code == 200:
    with open("this.pdf", 'wb') as f:
        f.write(response.content)   