import os.path
import time

from django.conf import settings
from django.http import JsonResponse
from django.views.generic import View
from pytube import YouTube

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

driver = None
lock = False


def setDriver():
    global driver

    profile_path = r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\oex5aocl.default'
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


# setDriver()


class InstagramView(View):
    def get(self, request, *args, **kwargs):
        username = request.GET['username']
        url = f'https://www.instagram.com/{username}/'

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
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//header')))
                profile_image_url = driver.find_element(By.XPATH, '//header//img').get_attribute('src')
                name = driver.find_element(By.XPATH, '//header/section/div[3]/span').text
            except:
                pass
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception as e:
            print(repr(e))
        lock = False

        return JsonResponse({'status': 200, 'name': name, 'profile_image_url': profile_image_url})


class YouTubeView(View):
    def get(self, request, *args, **kwargs):
        try:
            id = request.GET['id']
            url = f'https://www.youtube.com/watch?v={id}'
            output_path = settings.BASE_DIR.joinpath('archive_data', id)

            yt = YouTube(url)
            yt_video = yt.streams.get_highest_resolution()
            path = yt_video.download(output_path=output_path)
            file_name = os.path.basename(path)

            return JsonResponse({'status': 200, 'id': id, 'file_name': file_name})

        except Exception as e:
            return JsonResponse({'status': 400, 'message': repr(e)})
