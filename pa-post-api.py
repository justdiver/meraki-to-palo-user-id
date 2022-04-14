import requests

url = "https://<YOURFIREWALL>/api/?type=user-id&key=<YOURAPIKEY>"

payload={}
files=[
  ('file',('XMLBuilderoutput.xml',open('<PATH TO YOUR XML>/XMLBuilderoutput.xml','rb'),'text/xml'))
]

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
