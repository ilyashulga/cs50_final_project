import requests

# This is an example of downloading spectrum raw data via HTTP GET request

#for ping in range(1,255):
address = "http://10.77.10.65/TransferData/GetTrace/" #+ str(ping)

# Send HTTP GET request to server and attempt to receive a response
data = {'submit': 'All Traces'}
response = requests.post(url=address, data=data)

# If the HTTP GET request can be served
if response.status_code == 200:
    file = open("All_Traces.csv", 'w')
    file.write(response.text)
