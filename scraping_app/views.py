import boto3
import os
import requests
import ssl
import time
import urllib.request

from bs4 import BeautifulSoup
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.generic import View
from pytube import YouTube
from pytube.exceptions import VideoUnavailable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from my_settings import *

driver = None
lock = False


def setDriver():
    global driver

    profile_path = r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\oex5aocl.default'
    if not os.path.exists(profile_path):
        profile_path = r'C:\Users\Edmond\AppData\Roaming\Mozilla\Firefox\Profiles\a1oww1me.default-release'

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
            time.sleep(0.5)
            driver.switch_to.window(driver.window_handles[-1])
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//header')))
                profile_image_url = driver.find_element(By.XPATH, '//header//img').get_attribute('src')
                name = driver.find_element(By.XPATH, '//header/section/div[3]//span').text
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
            environment = request.GET.get('e')
            user_id = request.GET.get('u')
            account_id = request.GET.get('a')
            video_id = request.GET['v']
            if request.GET.get('s'):
                file_size = int(request.GET['s'])
            else:
                file_size = 0

            if not account_id:
                s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
                s3_path = f'YouTube/{video_id}.mp4'
                try:
                    response = s3.head_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=s3_path)

                    return JsonResponse({'status': 200, 'v': video_id, 's': response['ContentLength'], 't': response['LastModified'].strftime('%Y-%m-%d %H:%M:%S')})
                except:
                    pass

            url = f'https://www.youtube.com/watch?v={video_id}'
            output_path = settings.BASE_DIR.joinpath('archive_data')

            for i in range(4):
                try:
                    ssl._create_default_https_context = ssl._create_unverified_context

                    now = datetime.utcnow()

                    yt = YouTube(url, use_oauth=True, allow_oauth_cache=True)
                    yt_video = yt.streams.get_highest_resolution()

                    if file_size == yt_video.filesize:
                        return JsonResponse({'status': 200})

                    extension = os.path.splitext(yt_video.default_filename)[1]
                    if account_id:
                        file_name = f"{video_id}--{now.strftime('%Y-%m-%d--%H-%M-%S')}{extension}"
                    else:
                        file_name = f"{video_id}{extension}"

                    path = yt_video.download(output_path=output_path, filename=file_name)
                    file_size = os.path.getsize(path)
                    break

                except VideoUnavailable as e:
                    return JsonResponse({'status': 404, 'message': str(e)})
                except Exception as e:
                    if i == 3:
                        return JsonResponse({'status': 401, 'message': repr(e)})
                    time.sleep(10 + i * 10)

            try:
                if account_id:
                    s3_path = f'{environment}/archive_data/{user_id}/YouTube/{account_id}/{file_name}'
                else:
                    s3_path = f'YouTube/{file_name}'

                s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
                bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)

                bucket.upload_file(path, s3_path)

                os.remove(path)
            except Exception as e:
                return JsonResponse({'status': 402, 'message': repr(e)})

            return JsonResponse({'status': 200, 'u': user_id, 'a': account_id, 'v': video_id, 'e': extension, 's': file_size, 't': now.strftime('%Y-%m-%d %H:%M:%S')})

        except Exception as e:
            return JsonResponse({'status': 400, 'message': repr(e)})


def get_tiktok_download_url(id, video_url):
    cookies = {
        '_ga': 'GA1.2.214573273.1682039888',
        '_gid': 'GA1.2.1056694047.1682039888',
        '__gads': 'ID=6583bba55aa60e2d-226d98f4e9dc00e7:T=1682039892:RT=1682039892:S=ALNI_Ma5-APryWDWGu3PPqL2xhIMk5raRg',
        '__cflb': '02DiuEcwseaiqqyPC5qqJA27ysjsZzMZ7tdPt6nNMjAKV',
        '__gpi': 'UID=0000097d50921d86:T=1682039892:RT=1682062081:S=ALNI_MaAQ42D9mLmJih46WQOdv8zNVaRsg',
        '_gat_UA-3524196-6': '1',
    }

    headers = {
        'authority': 'ssstik.io',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,ko;q=0.8,ru;q=0.7',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'hx-current-url': 'https://ssstik.io/en',
        'hx-request': 'true',
        'hx-target': 'target',
        'hx-trigger': '_gcaptcha_pt',
        'origin': 'https://ssstik.io',
        'referer': 'https://ssstik.io/en',
        'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
    }

    params = {
        'url': 'dl',
    }

    data = {
        'id': video_url,
        'locale': 'en',
        'tt': 'blVBNEYy',
    }

    response = requests.post('https://ssstik.io/abc', params=params, cookies=cookies, headers=headers, data=data)
    if response.text == '':
        time.sleep(5)
        response = requests.post('https://ssstik.io/abc', params=params, cookies=cookies, headers=headers, data=data)

    soup = BeautifulSoup(response.text, 'html.parser')
    video_title = soup.p.getText().strip()
    download_url = soup.a['href']

    return download_url


class TikTokView(View):
    def get(self, request, *args, **kwargs):
        try:
            environment = request.GET.get('e')
            user_id = request.GET.get('u')
            account_id = request.GET.get('a')
            video_id = request.GET['i']
            video_url = request.GET['v']

            file_name = f'{video_id}.mp4'
            path = settings.BASE_DIR.joinpath('archive_data', file_name)

            s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
            if account_id:
                s3_path = f'{environment}/archive_data/{user_id}/TikTok/{account_id}/{file_name}'
            else:
                s3_path = f'TikTok/{file_name}'

            try:
                s3.head_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=s3_path)

                return JsonResponse({'status': 200})
            except:
                pass

            try:
                download_url = get_tiktok_download_url(video_id, video_url)

                resp = urllib.request.urlopen(download_url)
                content_type = resp.info()['Content-Type']
                if content_type != 'application/octet-stream':
                    return JsonResponse({'status': 401, 'message': content_type})

                urllib.request.urlretrieve(download_url, path)

                s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
                bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)

                bucket.upload_file(path, s3_path)

                os.remove(path)
            except Exception as e:
                return JsonResponse({'status': 402, 'message': repr(e)})

            return JsonResponse({'status': 200})

        except Exception as e:
            return JsonResponse({'status': 400, 'message': repr(e)})
