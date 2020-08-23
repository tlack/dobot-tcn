CAMERAS = {'rpi':'http://localhost:8585/', 'rpzw':'http://192.168.1.249:8585/'}

import base64
import time

import requests

def docam(name, url):
    t1 = time.time()
    r = requests.get(url=url+'pic')
    t2 = time.time()
    resp = r.json()
    data = base64.b64decode(resp['data']) 
    fn = name + '.jpg'
    open(fn, 'wb').write(data)
    t3 = time.time()
    print(f"{name} -> {fn} {resp['size']} reqtime: {t2-t1} savetime: {t3-t2}")

def main():
    for name, url in CAMERAS.items():
        docam(name, url)

main()
