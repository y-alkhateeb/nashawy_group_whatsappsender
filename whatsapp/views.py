import time
import os
from datetime import datetime

from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options

from .models import DrPhoneNumber, SystemSetting
import openpyxl
from selenium import webdriver
from time import sleep


def index(request):
    if "GET" == request.method:
        if not request.user.is_authenticated:
            return redirect('admin/login/?next=/')
        else:
            return render(request, 'index.html', {
                "all_phones": DrPhoneNumber.objects.all().count(),
                "all_phones_have_whatsapp": DrPhoneNumber.objects.all().filter(have_whatsapp=True).count()
            })
    else:
        if "s_m_all_number_db" in request.POST:
            return redirect('/whatsapp_send')
        elif "s_m_doesnot_have_wapp_db" in request.POST:
            return redirect('/whatsapp_send_dont_have_what')
        elif "s_m_does_have_wapp_db" in request.POST:
            return redirect('/whatsapp_send_have_what')
        elif "clear_database" in request.POST:
            DrPhoneNumber.objects.all().delete()
            return render(request, 'index.html', {
                "all_phones": DrPhoneNumber.objects.all().count(),
                "all_phones_have_whatsapp": DrPhoneNumber.objects.all().filter(have_whatsapp=True).count()
            })
        else:
            excel_file = request.FILES["excel_file"]

            # you may put validations here to check extension or file size

            wb = openpyxl.load_workbook(excel_file)

            # getting a particular sheet by name out of many sheets
            worksheet = wb["Sheet1"]
            print(worksheet)

            excel_data = list()
            phones = DrPhoneNumber()
            # iterating over the rows and
            # getting value from each cell in row
            for row in worksheet.iter_rows():
                row_data = list()
                for cell in row:
                    row_data.append(str(cell.value))
                    if len(str(cell.value)) > 6:
                        phones.phone_number = str(cell.value)
                        phones.have_whatsapp = True
                        phones.note = ""
                        phones.save()
                excel_data.append(row_data)
            return render(request, 'index.html', {
                "excel_data": len(excel_data),
                "all_phones": DrPhoneNumber.objects.all().count(),
                "all_phones_have_whatsapp": DrPhoneNumber.objects.all().filter(have_whatsapp=True).count()
            })


def send(request):
    all_phone_numbers = DrPhoneNumber.objects.all().count()
    if SystemSetting.objects.all().filter(type_sent=1).count() == 0:
        SystemSetting.objects.create(type_sent=1, last_index_sent=0, last_phone_number=0,
                                     last_date_of_sent=datetime.now())
    last_sent = SystemSetting.objects.all().filter(type_sent=1).first()
    if "GET" == request.method:
        if not request.user.is_authenticated:
            return redirect('admin/login/?next=/whatsapp_send')
        else:
            return render(request, 'whatsapp_send.html', {
                "all_phone_numbers": all_phone_numbers,
                "start_from": last_sent.last_index_sent
            })
    else:
        image = request.FILES["image"]
        fs = FileSystemStorage()
        filepath = os.path.realpath(fs.url(image.name))
        message = request.POST.get('message', '')
        timer = request.POST.get('timer', 20)
        start = request.POST.get('start_from', last_sent.last_index_sent)
        end = request.POST.get('end_to', all_phone_numbers)
        # options = Options() options.add_argument(
        # "user-data-dir=C:\\Users\\Yousef\\AppData\\Local\\Google\\Chrome\\User Data\\profile2") driver =
        # webdriver.Chrome(executable_path='F:\python\/nashawy_group_whatsapp_sender\whatsapp/chromedriver.exe',
        # chrome_options=options)
        driver = webdriver.Chrome(executable_path='F:\python\/nashawy_group_whatsapp_sender\whatsapp/chromedriver.exe')
        try:
            driver.get('https://web.whatsapp.com/')
            time.sleep(15)
            while not is_element_present(driver, "div", "class", "landing-main"):
                print("is_element_present: landing-main")
                if is_element_present(driver, "span", "data-icon", "laptop"):
                    break
                driver.get('https://web.whatsapp.com/')
                time.sleep(15)
            while not is_element_present(driver, "span", "data-icon", "laptop"):
                print("is_element_present: laptop")
                driver.get('https://web.whatsapp.com/')
                time.sleep(15)
            phone = DrPhoneNumber.objects.all()
            for i in range(int(start), int(end)):
                if is_element_present(driver, "span", "data-icon", "alert-phone"):
                    return HttpResponse("Please check your internet connection on your phone and try again.")
                single_phone = phone.get(phone_number=phone[i].phone_number)
                driver.get('https://web.whatsapp.com/send?phone=' + single_phone.phone_number + '&text=' + message)
                time.sleep(int(timer))
                # this mean this phone number don't have whatsapp
                if not is_element_present(driver, "div", "id", "main"):
                    # this mean bot can't parse this page
                    if not is_element_present(driver, "div", "role", "button"):
                        pass
                    else:
                        single_phone.have_whatsapp = False
                        single_phone.save()
                        user = driver.find_element_by_xpath('//div[@role = "button"]')
                        user.click()
                else:
                    if is_element_present(driver, "div", "title", "Attach"):
                        attachment_box = driver.find_element_by_xpath('//div[@title = "Attach"]')
                        attachment_box.click()
                        try:
                            image_box = driver.find_element_by_xpath(
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                            image_box.send_keys(filepath)
                            sleep(5)
                        except WebDriverException as e:
                            return HttpResponse("Please select an image from another directory and try again.")
                        if is_element_present(driver, "span", "data-icon", "send"):
                            # send_button = driver.find_element_by_xpath('//span[@data-icon="send-light"]')
                            send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
                            send_button.click()
                            single_phone.have_whatsapp = True
                            single_phone.number_of_message_sent += 1
                            single_phone.save()
                            last_sent.last_date_of_sent = datetime.now()
                            last_sent.last_phone_number = single_phone.phone_number
                            last_sent.last_index_sent = i + 1
                            last_sent.save()
                            sleep(10)
        except WebDriverException as e:
            print(e)
            return HttpResponse("Please check your internet connection and refresh page to try again")
        driver.close()
        return render(request, 'whatsapp_send.html', {"phone_number": all_phone_numbers})


def sendHaveWhat(request):
    all_phone_numbers = DrPhoneNumber.objects.all().filter(have_whatsapp=True).count()
    if SystemSetting.objects.all().filter(type_sent=3).count() == 0:
        SystemSetting.objects.create(type_sent=3, last_index_sent=0, last_phone_number=0,
                                     last_date_of_sent=datetime.now())
    last_sent = SystemSetting.objects.all().filter(type_sent=3).first()
    if "GET" == request.method:
        if not request.user.is_authenticated:
            return redirect('admin/login/?next=/whatsapp_send')
        else:
            return render(request, 'whatsapp_send_3.html', {
                "all_phone_numbers": all_phone_numbers,
                "start_from": last_sent.last_index_sent
            })
    else:
        image = request.FILES["image"]
        fs = FileSystemStorage()
        filepath = os.path.realpath(fs.url(image.name))
        message = request.POST.get('message', '')
        timer = request.POST.get('timer', 20)
        start = request.POST.get('start_from', last_sent.last_index_sent)
        end = request.POST.get('end_to', all_phone_numbers)
        # options = Options() options.add_argument(
        # "user-data-dir=C:\\Users\\Yousef\\AppData\\Local\\Google\\Chrome\\User Data\\profile2") driver =
        # webdriver.Chrome(executable_path='F:\python\/nashawy_group_whatsapp_sender\whatsapp/chromedriver.exe',
        # chrome_options=options)
        driver = webdriver.Chrome(executable_path='F:\python\/nashawy_group_whatsapp_sender\whatsapp/chromedriver.exe')
        try:
            driver.get('https://web.whatsapp.com/')
            time.sleep(15)
            while not is_element_present(driver, "div", "class", "landing-main"):
                print("is_element_present: landing-main")
                if is_element_present(driver, "span", "data-icon", "laptop"):
                    break
                driver.get('https://web.whatsapp.com/')
                time.sleep(15)
            while not is_element_present(driver, "span", "data-icon", "laptop"):
                print("is_element_present: laptop")
                driver.get('https://web.whatsapp.com/')
                time.sleep(15)
            phone = DrPhoneNumber.objects.all()
            for i in range(int(start), int(end)):
                if is_element_present(driver, "span", "data-icon", "alert-phone"):
                    return HttpResponse("Please check your internet connection on your phone and try again.")
                single_phone = phone.get(phone_number=phone[i].phone_number)
                driver.get('https://web.whatsapp.com/send?phone=' + single_phone.phone_number + '&text=' + message)
                time.sleep(int(timer))
                # this mean this phone number don't have whatsapp
                if not is_element_present(driver, "div", "id", "main"):
                    # this mean bot can't parse this page
                    if not is_element_present(driver, "div", "role", "button"):
                        pass
                    else:
                        single_phone.have_whatsapp = False
                        single_phone.save()
                        user = driver.find_element_by_xpath('//div[@role = "button"]')
                        user.click()
                else:
                    if is_element_present(driver, "div", "title", "Attach"):
                        attachment_box = driver.find_element_by_xpath('//div[@title = "Attach"]')
                        attachment_box.click()
                        try:
                            image_box = driver.find_element_by_xpath(
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                            image_box.send_keys(filepath)
                            sleep(5)
                        except WebDriverException as e:
                            return HttpResponse("Please select an image from another directory and try again.")
                        if is_element_present(driver, "span", "data-icon", "send"):
                            # send_button = driver.find_element_by_xpath('//span[@data-icon="send-light"]')
                            send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
                            send_button.click()
                            single_phone.have_whatsapp = True
                            single_phone.number_of_message_sent += 1
                            single_phone.save()
                            last_sent.last_date_of_sent = datetime.now()
                            last_sent.last_phone_number = single_phone.phone_number
                            last_sent.last_index_sent = i + 1
                            last_sent.save()
                            sleep(10)
        except WebDriverException as e:
            return HttpResponse("Please check your internet connection and refresh page to try again")
        driver.close()
        return render(request, 'whatsapp_send_3.html', {"phone_number": all_phone_numbers})


def sendDontHaveWhat(request):
    all_phone_numbers = DrPhoneNumber.objects.all().filter(have_whatsapp=False).count()
    if "GET" == request.method:
        if not request.user.is_authenticated:
            return redirect('admin/login/?next=/whatsapp_send')
        else:
            return render(request, 'whatsapp_send_2.html', {
                "all_phone_numbers": all_phone_numbers,
            })
    else:
        image = request.FILES["image"]
        fs = FileSystemStorage()
        filepath = os.path.realpath(fs.url(image.name))
        message = request.POST.get('message', '')
        timer = request.POST.get('timer', 20)
        # options = Options() options.add_argument(
        # "user-data-dir=C:\\Users\\Yousef\\AppData\\Local\\Google\\Chrome\\User Data\\profile2") driver =
        # webdriver.Chrome(executable_path='F:\python\/nashawy_group_whatsapp_sender\whatsapp/chromedriver.exe',
        # chrome_options=options)
        driver = webdriver.Chrome(executable_path='F:\python\/nashawy_group_whatsapp_sender\whatsapp/chromedriver.exe')
        try:
            driver.get('https://web.whatsapp.com/')
            time.sleep(15)
            while not is_element_present(driver, "div", "class", "landing-main"):
                print("is_element_present: landing-main")
                if is_element_present(driver, "span", "data-icon", "laptop"):
                    break
                driver.get('https://web.whatsapp.com/')
                time.sleep(15)
            while not is_element_present(driver, "span", "data-icon", "laptop"):
                print("is_element_present: laptop")
                driver.get('https://web.whatsapp.com/')
                time.sleep(15)
            phone = DrPhoneNumber.objects.all().filter(have_whatsapp=False)
            for i in range(0, all_phone_numbers):
                if is_element_present(driver, "span", "data-icon", "alert-phone"):
                    return HttpResponse("Please check your internet connection on your phone and try again.")
                single_phone = phone.get(phone_number=phone[i].phone_number)
                driver.get('https://web.whatsapp.com/send?phone=' + single_phone.phone_number + '&text=' + message)
                time.sleep(int(timer))
                # this mean this phone number don't have whatsapp
                if not is_element_present(driver, "div", "id", "main"):
                    # this mean bot can't parse this page
                    if not is_element_present(driver, "div", "role", "button"):
                        pass
                    else:
                        single_phone.have_whatsapp = False
                        single_phone.save()
                        user = driver.find_element_by_xpath('//div[@role = "button"]')
                        user.click()
                else:
                    if is_element_present(driver, "div", "title", "Attach"):
                        attachment_box = driver.find_element_by_xpath('//div[@title = "Attach"]')
                        attachment_box.click()
                        try:
                            image_box = driver.find_element_by_xpath(
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                            image_box.send_keys(filepath)
                            sleep(5)
                        except WebDriverException as e:
                            return HttpResponse("Please select an image from another directory and try again.")
                        if is_element_present(driver, "span", "data-icon", "send"):
                            # send_button = driver.find_element_by_xpath('//span[@data-icon="send-light"]')
                            send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
                            send_button.click()
                            single_phone.have_whatsapp = True
                            single_phone.number_of_message_sent += 1
                            single_phone.save()
                            sleep(10)
        except WebDriverException as e:
            return HttpResponse("Please check your internet connection and refresh page to try again")
        driver.close()
        return render(request, 'whatsapp_send_2.html', {"phone_number": all_phone_numbers})


def is_element_present(driver, a, b, c):
    try:
        driver.find_element_by_xpath("//" + a + "[@" + b + "=" + "'" + c + "'" + "]")
    except NoSuchElementException as e:
        return False
    return True
