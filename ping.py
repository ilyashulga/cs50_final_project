import subprocess
import requests

for ping in range(1,255):
    address = "10.77.10." + str(ping)
    file=0
    try:
        response = requests.post('http://' + address + '/TransferData/GetTrace', data = 'All Traces')
        file = response.content
    except:
         print("not reachable")
    print(str(ping)
    if file:
        print(str(ping))
        print(file)
    #res = subprocess.call(['ping', '-c', '1', address])
    #if res == 0:
        #print ("ping to", address, "OK")
    #elif res == 2:
        #print ("no response from", address)
    #else:
        #print ("ping to", address, "failed!")