# import requests
import re
import json
from curl_cffi import requests
# import requests
import random
from camoufox.sync_api import Camoufox
from browserforge.fingerprints import Screen
import time
import traceback
import os
import sys

def file_to_list(filepath):
    if os.path.exists(filepath):
        file = open(filepath, "r") 
        data = file.read() 
        datalist = data.split("\n") 
        file.close()
        return datalist 
    else:
        return False

proxypools = file_to_list("proxies.txt")
if proxypools == False:
    print("Missing proxies.txt")
    sys.exit()

urls = file_to_list("urls.txt")
if urls == False:
    print("Missing urls.txt")
    sys.exit()

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:130.0) Gecko/20100101 Firefox/130.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Priority': 'u=0, i',
}
   
def get_new_proxy():
    padd=str(random.choice(proxypools)).split('@')
    proxy_address = padd[1]
    login = padd[0].split(":")[0]
    password = padd[0].split(":")[1]


    proxies = {
        'http': f'http://{login}:{password}@{proxy_address}',
        'https': f'http://{login}:{password}@{proxy_address}'
    }

    proxycamoufox = {"server": f"http://{proxy_address}",
                "username": login,
                "password": password
    }
    return proxycamoufox, proxies

def get_cookies():
    response = False
    while True:
        urldecoy = urls[random.choice(range(0, len(urls)))]
        print("get new cookies", '...', flush=True, end="")
        proxycamoufox, proxies = get_new_proxy()
        with Camoufox(headless=True, geoip=True, os=('windows'), screen=Screen(max_width=1920, max_height=1080)) as browser:
            try:
                page = browser.new_page(locale="en-US", proxy=proxycamoufox)
                response = page.goto(urldecoy, timeout=60000, wait_until="networkidle")    
                # breakpoint()
                page.wait_for_selector("h-main-content", timeout=60000)
                while True:
                    cookies = page.context.cookies()
                    try:
                        datadome_cookie = next((cookie for cookie in cookies if cookie['name'] == 'datadome'), None)
                        # cfbm_cookie = next((cookie for cookie in cookies if cookie['name'] == '__cf_bm'), None)
                        # cookies = {'datadome': datadome_cookie['value'], '__cf_bm': cfbm_cookie['value']}
                        cookies = {'datadome': datadome_cookie['value']}
                        break
                    except:
                        continue
                browser.close()
                break
            except Exception as e:
                print("Failed")
                print(traceback.format_exc())
                continue
    print("OK")
    return cookies, proxies

def parse(cookies, proxies, url):
    for _ in range(0,3):
        try:
            response = requests.get(url=url, cookies=cookies, headers=headers, proxies=proxies)
        except Exception as e:
            print(str(e), "Failed")
            # print(traceback.format_exc())
            print(url, '...', flush=True, end="")
            continue
        if response.status_code == 403:
            print("Failed")
            return False
        if response.status_code == 200:
            print("Ready")
        elif response.status_code == 404:
            print("Empty")
        else:
            print("Error:", response.status_code)
            return False
        return True
    return False
def main():
    cookies, proxies = get_cookies()
    while True:
        for url in urls:
            while True:
                print(url, '...', flush=True, end="")
                result = parse(cookies=cookies, proxies=proxies, url=url)
                if result:
                    break
                else:
                    cookies, proxies = get_cookies()
                    continue
            time.sleep(random.choice(range(3,10)))
        stime = 60*10
        print(stime, "seconds idle...")
        time.sleep(stime)

if __name__=='__main__':
    main()