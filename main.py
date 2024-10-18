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
from dotenv import load_dotenv
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, quote


load_dotenv()

def file_to_list(filepath):
    if os.path.exists(filepath):
        file = open(filepath, "r") 
        data = file.read() 
        datalist = data.split("\n") 
        file.close()
        return datalist 
    else:
        return False


TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def send_to_telegram(message):
    apiToken = TELEGRAM_BOT_TOKEN
    chatID = TELEGRAM_CHAT_ID
    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'
    try:
        response = requests.post(apiURL, json={'chat_id': chatID, 'text': message, "parse_mode": "HTML"})
        # print(response.text)
    except Exception as e:
        print(e)

def parse_message_to_html(link):
    html = "<strong>Product Available</strong>\n"
    html += f'<a href="{link}">Go to Page</a>'
    return html

proxypools = file_to_list("proxies.txt")
if proxypools == False:
    print("Missing proxies.txt")
    sys.exit()
proxypools = list(filter(None, proxypools))

urls = file_to_list("urls.txt")
if urls == False:
    print("Missing urls.txt")
    sys.exit()
urls = list(filter(None, urls))

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

def get_captcha_url(response, targeturl):
    restext = response.body().decode("utf-8")
    resheaders = response.all_headers()
    dd_cookie = resheaders.get('set-cookie').split('datadome=')[1].split(';')[0]
    soup = BeautifulSoup(restext, 'html.parser')
    script_tag = soup.find('script')
    dd_script = str(script_tag)
    dd_script = dd_script.replace('<script data-cfasync="false">var dd=', "")
    dd_script = dd_script.replace('</script>', "")

    # Replace single quotes with double quotes
    json_string = dd_script.replace("'", '"')

    # Parse the string into a JSON object
    dd = json.loads(json_string)
    if  "t" in dd:
        # print("found t")
        # params = {
        #     'initialCid': dd['cid'],
        #     'hash': dd['hsh'],
        #     'cid': dd_cookie,
        #     't': dd['t'],
        #     'referer': targeturl,
        #     's': dd['s'],
        #     'e': dd['e'],
        #     'dm': 'cd'
        # }

        captcha_url = "https://geo.captcha-delivery.com/captcha/"

        url = f"{captcha_url}?initialCid={dd['cid']}&hash={dd['hsh']}&cid={dd_cookie}&t={dd['t']}&referer={quote_plus(targeturl)}&s={dd['s']}&e={dd['e']}&dm=cd"
        
        url = url.replace("==", "%3D%3D")
        if "t=bv" in url:
            return False    
        else:
            return url    
    else:
        return False

def get_cookies():
    response = False
    while True:
        urldecoy = urls[random.choice(range(0, len(urls)))]
        print("get new cookies", '...', flush=True, end="")
        proxycamoufox, proxies = get_new_proxy()
        with Camoufox(headless=True, proxy=proxycamoufox, geoip=True, os=('macos','windows', 'linux'), screen=Screen(max_width=1920, max_height=1080)) as browser:
            page = browser.new_page(locale="en-US", java_script_enabled=True)
            try:
                response = page.goto(urldecoy, timeout=60000, wait_until="networkidle")    
                # breakpoint()
                page.wait_for_selector("iframe", timeout=60000)
                # page.wait_for_selector('iframe')
                captcha_url = get_captcha_url(response=response, targeturl=urldecoy)
                if captcha_url:
                    print(captcha_url)
                    if 't=bv' in captcha_url:
                        print("Blocked")
                        continue
                    else:
                        #todo: solve captcha url with 2captcha or captchasolver
                        pass


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
                # breakpoint()
                print(traceback.format_exc())
                continue
    print("OK")
    return cookies, proxies

def parse(cookies, proxies, url):
    for _ in range(0,5):
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
            html = parse_message_to_html(link=url)
            send_to_telegram(html)
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