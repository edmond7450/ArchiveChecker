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


def setDriver():
    global driver
    try:
        options = Options()
        options.set_preference('profile', profile_path)
        options.add_argument('--start-maximized')

        service = Service('geckodriver.exe')

        driver = webdriver.Firefox(service=service, options=options)
    except Exception as e:
        print(e)


class InstagramView(View):
    def get(self, request, *args, **kwargs):
        username = request.GET['username']
        url = f'https://www.instagram.com/{username}/?__a=1'

        setDriver()
        driver.get('https://www.instagram.com/')

        return JsonResponse({'status': 200, 'name': '', 'profile_image_url': ''})
