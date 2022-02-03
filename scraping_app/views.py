import json
import time

from django.http import JsonResponse
from django.views.generic import View

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

profile_path = r'c:\Users\Edmond\AppData\Roaming\Mozilla\Firefox\Profiles\6244c9sg.default-release'
driver = None
lock = False


def setDriver():
    global driver
    try:
        options = Options()
        # options.set_preference('profile', profile_path)
        options.set_preference('devtools.jsonview.enabled', False)

        # service = Service('geckodriver.exe')
        # driver = webdriver.Firefox(service=service, options=options)

        profile = webdriver.FirefoxProfile(profile_path)
        driver = webdriver.Firefox(executable_path='geckodriver.exe', firefox_profile=profile, options=options)
    except Exception as e:
        print(e)


setDriver()


class InstagramView(View):
    def get(self, request, *args, **kwargs):
        username = request.GET['username']
        url = f'https://www.instagram.com/{username}/?__a=1'

        name = ''
        profile_image_url = ''

        global lock
        while lock:
            time.sleep(1)

        lock = True
        try:
            driver.get(url)
            content = driver.find_element(By.TAG_NAME, 'pre').text
            parsed_json = json.loads(content)
        except:
            pass
        lock = False

        try:
            if username == parsed_json['graphql']['user']['username']:
                name = parsed_json['graphql']['user']['full_name']
                profile_image_url = parsed_json['graphql']['user']['profile_pic_url']
        except:
            pass

        return JsonResponse({'status': 200, 'name': name, 'profile_image_url': profile_image_url})
