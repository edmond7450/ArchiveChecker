import json
import os.path
import time

from django.http import JsonResponse
from django.views.generic import View

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

driver = None
lock = False


def setDriver():
    global driver

    profile_path = r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\n0jnkby3.default-release'
    if not os.path.exists(profile_path):
        profile_path = r'C:\Users\Edmond\AppData\Roaming\Mozilla\Firefox\Profiles\6244c9sg.default-release'
    if not os.path.exists(profile_path):
        profile_path = r'C:\Users\Denis\AppData\Roaming\Mozilla\Firefox\Profiles\qpx5ocgo.default-release'

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

        fbid = ''
        name = ''
        profile_image_url = ''
        sleeps = 0

        global lock
        while lock:
            time.sleep(1)
            sleeps += 1
            if sleeps >= 5:
                return JsonResponse({'status': 500})

        lock = True
        try:
            driver.execute_script(f"window.open('{url}', '_blank');")
            driver.switch_to.window(driver.window_handles[-1])
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'pre')))
            content = driver.find_element(By.TAG_NAME, 'pre').text
            parsed_json = json.loads(content)
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except:
            pass
        lock = False

        try:
            if username == parsed_json['graphql']['user']['username']:
                fbid = parsed_json['graphql']['user']['fbid']
                name = parsed_json['graphql']['user']['full_name']
                profile_image_url = parsed_json['graphql']['user']['profile_pic_url']
        except:
            pass

        return JsonResponse({'status': 200, 'fbid': fbid, 'name': name, 'profile_image_url': profile_image_url})
