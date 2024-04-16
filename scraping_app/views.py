import boto3
import magic
import os
import ssl
import shutil
import time

from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.generic import View
from pathlib import Path
from pytube import YouTube
from pytube.exceptions import VideoUnavailable
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from my_settings import *

driver = None
profile_index = 0
lock = False


def open_driver():
    global driver
    global profile_index

    profiles = [
        r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\455dzlxw.default-release-1707249233643',
        r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\lybi8xkf.User 1',
        r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\kfpn79je.User 2',
        r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\edfdede0.User 3'
    ]
    # profiles = [
    #     r'C:\Users\Administrator\AppData\Roaming\Mozilla\Firefox\Profiles\1pgwv6ld.default-release'
    # ]

    temp_dir = r'C:\Users\Administrator\AppData\Local\Temp\2'

    try:
        driver.close()
        driver.quit()
    except:
        pass

    try:
        shutil.rmtree(temp_dir)
        os.mkdir(temp_dir)
    except:
        pass

    try:
        if profile_index >= len(profiles):
            profile_index = 0
        options = Options()
        options.profile = profiles[profile_index]
        options.set_preference('devtools.jsonview.enabled', False)

        service = Service('geckodriver.exe')
        driver = webdriver.Firefox(service=service, options=options)
    except Exception as e:
        print(e)


open_driver()


class InstagramView(View):
    def get(self, request, *args, **kwargs):
        username = request.GET['username']
        url = f'https://www.instagram.com/{username}/'

        name = ''
        profile_image_url = ''
        status = 400
        sleeps = 0

        global profile_index
        global lock
        while lock:
            time.sleep(1)
            sleeps += 1
            if sleeps >= 10:
                if len(driver.window_handles) == 1:
                    time.sleep(5)
                    if lock and len(driver.window_handles) == 1:
                        break
                return JsonResponse({'status': 500})

        lock = True
        while len(driver.window_handles) > 1:
            try:
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(1)
                driver.close()
            except:
                pass
        try:
            driver.execute_script(f"window.open('{url}', '_blank');")
            time.sleep(1)
            driver.switch_to.window(driver.window_handles[-1])
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//main')))
                if len(driver.find_elements(By.XPATH, '//header')) > 0:
                    if len(driver.find_elements(By.XPATH, '//header//img')) > 0:
                        profile_image_url = driver.find_element(By.XPATH, '//header//img').get_attribute('src')
                    if len(driver.find_elements(By.XPATH, '//header/section/div[3]//span')) > 0:
                        name = driver.find_element(By.XPATH, '//header/section/div[3]//span').text
                    if profile_image_url or name:
                        status = 200
                elif len(driver.find_elements(By.XPATH, '//*[text()="Sorry, this page isn\'t available."]')) > 0:
                    status = 401
                else:
                    raise Exception
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except:
                profile_index += 1
                open_driver()

                try:
                    driver.execute_script(f"window.open('{url}', '_blank');")
                    time.sleep(1)
                    driver.switch_to.window(driver.window_handles[-1])
                    try:
                        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//main')))
                        if len(driver.find_elements(By.XPATH, '//header')) > 0:
                            if len(driver.find_elements(By.XPATH, '//header//img')) > 0:
                                profile_image_url = driver.find_element(By.XPATH, '//header//img').get_attribute('src')
                            if len(driver.find_elements(By.XPATH, '//header/section/div[3]//span')) > 0:
                                name = driver.find_element(By.XPATH, '//header/section/div[3]//span').text
                            if profile_image_url or name:
                                status = 200
                        elif len(driver.find_elements(By.XPATH, '//*[text()="Sorry, this page isn\'t available."]')) > 0:
                            status = 401
                        else:
                            driver.save_screenshot(f'{username}.png')
                            raise Exception
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                    except:
                        profile_index += 1
                        open_driver()
                except Exception as e:
                    print('----------', repr(e))

        except Exception as e:
            print(repr(e))
        lock = False

        return JsonResponse({'status': status, 'name': name, 'profile_image_url': profile_image_url})


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
                    try:
                        yt_video = yt.streams.get_highest_resolution()
                    except:
                        try:
                            if yt.watch_html.find("This video has been removed for violating YouTube's Community Guidelines") > 0:
                                return JsonResponse({'status': 404, 'message': "This video has been removed for violating YouTube's Community Guidelines"})
                        except:
                            raise Exception

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


class TikTokView(View):
    def get(self, request, *args, **kwargs):
        environment = request.GET.get('e')
        user_id = request.GET.get('u')
        account_id = request.GET.get('a')
        video_id = request.GET['i']
        video_url = request.GET['v']

        file_name = f'{video_id}.mp4'
        path = ''  # settings.BASE_DIR.joinpath('archive_data', file_name)

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

        sleeps = 0
        global lock
        while lock:
            time.sleep(1)
            sleeps += 1
            if sleeps >= 10:
                if len(driver.window_handles) == 1:
                    time.sleep(5)
                    if lock and len(driver.window_handles) == 1:
                        break
                return JsonResponse({'status': 500})

        for f in os.listdir('C:\\Users\\Administrator\\Downloads'):
            if f.endswith('.mp4') or f.endswith('.mp4.part'):
                os.remove(os.path.join('C:\\Users\\Administrator\\Downloads', f))

        if any((f.endswith('.mp4') or f.endswith('.mp4.part')) for f in os.listdir('C:\\Users\\Administrator\\Downloads')):
            return JsonResponse({'status': 501, 'message': 'MP4 file exists'})

        lock = True
        try:
            driver.execute_script("window.open('https://ssstik.io/en', '_blank');")
            time.sleep(0.5)
            driver.switch_to.window(driver.window_handles[-1])
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="main_page_text"]')))
                ele_input = driver.find_element(By.XPATH, '//input[@id="main_page_text"]')
                ele_input.click()
                time.sleep(0.1)
                ele_input.send_keys(video_url)
                time.sleep(1)

                driver.find_element(By.XPATH, '//button[@id="submit"]').click()
                try:
                    WebDriverWait(driver, 10).until(lambda driver: driver.find_elements(By.XPATH, '//a[text()="Without watermark"]') or driver.find_elements(By.XPATH, '//a[@id="slides_generate"]'))
                except TimeoutException:
                    time.sleep(10)
                    driver.find_element(By.XPATH, '//button[@id="submit"]').click()
                    WebDriverWait(driver, 10).until(lambda driver: driver.find_elements(By.XPATH, '//a[text()="Without watermark"]') or driver.find_elements(By.XPATH, '//a[@id="slides_generate"]'))

                if len(driver.find_elements(By.XPATH, '//*[@id="dismiss-button"]')) > 0 and driver.find_element(By.XPATH, '//*[@id="dismiss-button"]').is_displayed():
                    driver.find_element(By.XPATH, '//*[@id="dismiss-button"]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//button[@data-micromodal-close=""]')) > 0 and driver.find_element(By.XPATH, '//button[@data-micromodal-close=""]').is_displayed():
                    driver.find_element(By.XPATH, '//button[@data-micromodal-close=""]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//a[text()="Without watermark"]')) > 0:
                    driver.find_element(By.XPATH, '//a[text()="Without watermark"]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//a[@id="slides_generate"]')) > 0:
                    driver.find_element(By.XPATH, '//a[@id="slides_generate"]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//*[@id="dismiss-button"]')) > 0 and driver.find_element(By.XPATH, '//*[@id="dismiss-button"]').is_displayed():
                    driver.find_element(By.XPATH, '//*[@id="dismiss-button"]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//button[@data-micromodal-close=""]')) > 0 and driver.find_element(By.XPATH, '//button[@data-micromodal-close=""]').is_displayed():
                    driver.find_element(By.XPATH, '//button[@data-micromodal-close=""]').click()
                    time.sleep(0.1)
            except:
                driver.get('https://ssstik.io/en')

                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="main_page_text"]')))
                ele_input = driver.find_element(By.XPATH, '//input[@id="main_page_text"]')
                ele_input.click()
                ele_input.send_keys(video_url)
                time.sleep(0.1)

                driver.find_element(By.XPATH, '//button[@id="submit"]').click()
                try:
                    WebDriverWait(driver, 10).until(lambda driver: driver.find_elements(By.XPATH, '//a[text()="Without watermark"]') or driver.find_elements(By.XPATH, '//a[@id="slides_generate"]'))
                except TimeoutException:
                    time.sleep(10)
                    driver.find_element(By.XPATH, '//button[@id="submit"]').click()
                    WebDriverWait(driver, 10).until(lambda driver: driver.find_elements(By.XPATH, '//a[text()="Without watermark"]') or driver.find_elements(By.XPATH, '//a[@id="slides_generate"]'))

                if len(driver.find_elements(By.XPATH, '//*[@id="dismiss-button"]')) > 0 and driver.find_element(By.XPATH, '//*[@id="dismiss-button"]').is_displayed():
                    driver.find_element(By.XPATH, '//*[@id="dismiss-button"]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//button[@data-micromodal-close=""]')) > 0 and driver.find_element(By.XPATH, '//button[@data-micromodal-close=""]').is_displayed():
                    driver.find_element(By.XPATH, '//button[@data-micromodal-close=""]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//a[text()="Without watermark"]')) > 0:
                    driver.find_element(By.XPATH, '//a[text()="Without watermark"]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//a[@id="slides_generate"]')) > 0:
                    driver.find_element(By.XPATH, '//a[@id="slides_generate"]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//*[@id="dismiss-button"]')) > 0 and driver.find_element(By.XPATH, '//*[@id="dismiss-button"]').is_displayed():
                    driver.find_element(By.XPATH, '//*[@id="dismiss-button"]').click()
                    time.sleep(0.1)
                if len(driver.find_elements(By.XPATH, '//button[@data-micromodal-close=""]')) > 0 and driver.find_element(By.XPATH, '//button[@data-micromodal-close=""]').is_displayed():
                    driver.find_element(By.XPATH, '//button[@data-micromodal-close=""]').click()
                    time.sleep(0.1)

            for i in range(5):
                for f in sorted(Path('C:\\Users\\Administrator\\Downloads').iterdir(), key=os.path.getctime, reverse=True):
                    if f.name.endswith('.mp4.part'):
                        path = 'C:\\Users\\Administrator\\Downloads\\ssstik.io_' + f.name.split('_')[1][:-5]
                        break
                if path:
                    break
                time.sleep(0.5)

            if not path:
                for f in sorted(Path('C:\\Users\\Administrator\\Downloads').iterdir(), key=os.path.getctime, reverse=True):
                    if f.name.endswith('.mp4'):
                        path = 'C:\\Users\\Administrator\\Downloads\\' + f.name
                        break

            if path:
                for i in range(600):
                    if os.path.exists(path):
                        mime_type = magic.from_file(path, mime=True)
                        if mime_type != 'inode/x-empty':
                            break
                    time.sleep(1)

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception as e:
            print(repr(e))
        lock = False

        if path:
            if not os.path.exists(path):
                return JsonResponse({'status': 401, 'message': 'Download Timeout'})

            try:
                mime_type = magic.from_file(path, mime=True)
                if mime_type != 'video/mp4':
                    return JsonResponse({'status': 402, 'message': mime_type})

                s3 = boto3.resource('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
                bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)

                bucket.upload_file(path, s3_path)

                os.remove(path)
            except:
                return JsonResponse({'status': 502, 'message': 'Upload Failed'})
        else:
            return JsonResponse({'status': 401, 'message': 'Download failed'})

        return JsonResponse({'status': 200})
