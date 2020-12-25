import getpass
import time
from datetime import datetime
from os.path import join
from django.http import HttpResponse
from django.shortcuts import render, redirect
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options

from .models import DrPhoneNumber, SystemSetting, SystemReporting, PhoneNumberGroup
import openpyxl
from selenium import webdriver
from time import sleep
from webdriver_manager.chrome import ChromeDriverManager

image_path = "C:\\nashawy_group_whatsapp_sender\\temp\\"


def checkUserIsAuthenticated(request, html_name, map_response):
    if not request.user.is_authenticated:
        return redirect('admin/login/?next=/')
    else:
        return render(request, html_name, map_response)


def index(request):
    dr_phone_number = DrPhoneNumber.objects.all()
    phone_number_group, created = PhoneNumberGroup.objects.get_or_create(group_name="global")
    total_sent_messages = 0
    for messages in dr_phone_number.filter(number_of_message_sent__gte=1):
        total_sent_messages += messages.number_of_message_sent
    if "GET" == request.method:
        return checkUserIsAuthenticated(request, 'index.html', {
            "all_phones": DrPhoneNumber.objects.all().count(),
            "all_phones_have_whatsapp": DrPhoneNumber.objects.all().filter(have_whatsapp=True).count(),
            "total_sent_messages": total_sent_messages
        })
    else:
        excel_file = request.FILES["excel_file"]

        # you may put validations here to check extension or file size

        wb = openpyxl.load_workbook(excel_file)

        # getting a particular sheet by name out of many sheets
        worksheet = wb["Sheet1"]
        excel_data = list()
        phones = DrPhoneNumber()
        # iterating over the rows and
        # getting value from each cell in row
        row_data = list()
        for row in worksheet.iter_rows():
            for cell in row:
                row_data.append(str(cell.value))
                if len(str(cell.value)) > 9:
                    phones.group = phone_number_group
                    phones.phone_number = str(cell.value)
                    phones.have_whatsapp = True
                    phones.note = ""
                    phones.save()
            excel_data.append(row_data)
        return render(request, 'index.html', {
            "excel_data": len(excel_data),
            "all_phones": DrPhoneNumber.objects.all().count(),
            "all_phones_have_whatsapp": DrPhoneNumber.objects.all().filter(have_whatsapp=True).count(),
            "total_sent_messages": "0"
        })


def send(request):
    all_phone_numbers = DrPhoneNumber.objects.all().count()
    all_phone_failed_sent = []
    all_phone_success_sent = []

    if SystemSetting.objects.all().filter(type_sent=1).count() == 0:
        SystemSetting.objects.create(type_sent=1, last_index_sent=0, last_phone_number=0,
                                     last_date_of_sent=datetime.now())
    last_sent = SystemSetting.objects.all().filter(type_sent=1).first()
    if "GET" == request.method:
        return checkUserIsAuthenticated(request, 'whatsapp_send.html', {
            "all_phone_numbers": all_phone_numbers,
            "start_from": last_sent.last_index_sent
        })
    else:
        image = request.FILES["image"]
        file = open(join(image_path, image.name), 'wb')
        file.write(image.read())
        file.close()
        filepath = image_path + image.name
        message = request.POST.get('message', '')
        split_message = message.split("\n")
        message_with_newline = ''
        for line_message in split_message:
            message_with_newline = message_with_newline + line_message
        timer = request.POST.get('timer', 20)
        start = request.POST.get('start_from', last_sent.last_index_sent)
        end = request.POST.get('end_to', all_phone_numbers)
        username = getpass.getuser()
        options = Options()
        options.add_argument(
            "user-data-dir=C:\\Users\\" + username + "\\AppData\\Local\\Google\\Chrome\\User Data\\profile2")
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
        # driver = webdriver.Chrome(executable_path=r"F:\python\nashawy_group_whatsapp_sender\whatsapp\chromedriver.exe", chrome_options=options)
        try:
            driver.get('https://web.whatsapp.com/')
            time.sleep(15)
            while not is_element_present(driver, "div", "class", "landing-main"):
                if is_element_present(driver, "span", "data-icon", "laptop"):
                    break
                driver.get('https://web.whatsapp.com/')
                time.sleep(15)
            while not is_element_present(driver, "span", "data-icon", "laptop"):
                driver.get('https://web.whatsapp.com/')
                time.sleep(15)
            phone = DrPhoneNumber.objects.all()
            for i in range(int(start), int(end)):
                if is_element_present(driver, "span", "data-icon", "alert-phone"):
                    return HttpResponse("Please check your internet connection on your phone and try again.")
                start_or_stop = driver.find_element_by_xpath(
                    '//div[@class="_1awRl copyable-text selectable-text"]').text
                if "stop" in start_or_stop:
                    time.sleep(1)
                    while not "start" in driver.find_element_by_xpath(
                            '//div[@class="_1awRl copyable-text selectable-text"]').text:
                        time.sleep(5)
                single_phone = phone.get(phone_number=phone[i].phone_number)
                # find new chat icon and click it
                while not is_element_present(driver, "span", "data-testid", "chat"):
                    driver.get('https://web.whatsapp.com/')
                    time.sleep(15)
                new_chat = driver.find_element_by_xpath('//span[@data-testid="chat"]')
                new_chat.click()
                sleep(1)
                new_chat_search_input = driver.find_element_by_xpath('//div[@class="_1awRl copyable-text selectable-text"]')
                new_chat_search_input.send_keys(str(single_phone.phone_number))
                sleep(2)
                if not is_element_present(driver, "div", "class", "_1ivy5"):
                    print("find here")
                    chat_selected = driver.find_element_by_xpath('//div[@class = "_1C6Zl"]')
                    chat_selected.click()
                    sleep(2)
                    send_test_chat = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')
                    send_test_chat.send_keys(".")
                else:
                    driver.get('https://web.whatsapp.com/send?phone=' + str(single_phone.phone_number) + '&text=' + ".")
                    time.sleep(5)
                time.sleep(int(timer))
                while not is_element_present(driver, "div", "class", "_1awRl copyable-text selectable-text"):
                    print("_1awRl copyable-text selectable-text")
                    time.sleep(2)
                start_or_stop = driver.find_element_by_xpath(
                    '//div[@class="_1awRl copyable-text selectable-text"]').text
                if "stop" in start_or_stop:
                    time.sleep(1)
                    print("stop in start_or_stop")
                    while not "start" in driver.find_element_by_xpath(
                            '//div[@class="_1awRl copyable-text selectable-text"]').text:
                        time.sleep(5)
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
                        all_phone_failed_sent.append(single_phone.phone_number)
                else:
                    # here we add new line by java script
                    msg = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')
                    driver.execute_script("arguments[0].innerText=arguments[1];", msg, message_with_newline)
                    msg.send_keys(" ")
                    sleep(1)
                    start_or_stop = driver.find_element_by_xpath(
                        '//div[@class="_1awRl copyable-text selectable-text"]').text
                    if "stop" in start_or_stop:
                        time.sleep(1)
                        print("stop in start_or_stop")
                        while not "start" in driver.find_element_by_xpath(
                                '//div[@class="_1awRl copyable-text selectable-text"]').text:
                            time.sleep(5)
                    if is_element_present(driver, "div", "title", "Attach"):
                        attachment_box = driver.find_element_by_xpath('//div[@title = "Attach"]')
                        attachment_box.click()
                        try:
                            image_box = driver.find_element_by_xpath(
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                            image_box.send_keys(filepath)
                            sleep(3)
                        except WebDriverException as e:
                            return HttpResponse("Please select an image from another directory and try again.")
                        if is_element_present(driver, "span", "data-icon", "send"):
                            send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
                            send_button.click()
                            single_phone.have_whatsapp = True
                            single_phone.number_of_message_sent += 1
                            single_phone.save()
                            last_sent.last_date_of_sent = datetime.now()
                            last_sent.last_phone_number = single_phone.phone_number
                            last_sent.last_index_sent = i + 1
                            last_sent.save()
                            all_phone_success_sent.append(single_phone.phone_number)
                            sleep(1)
                            if is_element_present(driver, "span", "aria-label", " Pending "):
                                sleep(1)
                                while is_element_present(driver, "span", "aria-label", " Pending "):
                                    sleep(2)
                            start_or_stop = driver.find_element_by_xpath(
                                '//div[@class="_1awRl copyable-text selectable-text"]').text
                            if "stop" in start_or_stop:
                                time.sleep(1)
                                while not "start" in driver.find_element_by_xpath(
                                        '//div[@class="_1awRl copyable-text selectable-text"]').text:
                                    time.sleep(5)

                    elif is_element_present(driver, "div", "title", "إرفاق"):
                        attachment_box = driver.find_element_by_xpath('//div[@title = "إرفاق"]')
                        attachment_box.click()
                        try:
                            image_box = driver.find_element_by_xpath(
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                            image_box.send_keys(filepath)
                            sleep(3)
                        except WebDriverException as e:
                            return HttpResponse("Please select an image from another directory and try again.")
                        if is_element_present(driver, "span", "data-icon", "send"):
                            send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
                            send_button.click()
                            single_phone.have_whatsapp = True
                            single_phone.number_of_message_sent += 1
                            single_phone.save()
                            last_sent.last_date_of_sent = datetime.now()
                            last_sent.last_phone_number = single_phone.phone_number
                            last_sent.last_index_sent = i + 1
                            last_sent.save()
                            all_phone_success_sent.append(single_phone.phone_number)
                            sleep(1)
                            if is_element_present(driver, "span", "aria-label", " الرسائل المُعَلَّقة "):
                                sleep(1)
                                while is_element_present(driver, "span", "aria-label", " الرسائل المُعَلَّقة "):
                                    sleep(2)
                            start_or_stop = driver.find_element_by_xpath(
                                '//div[@class="_1awRl copyable-text selectable-text"]').text
                            if "stop" in start_or_stop:
                                time.sleep(1)
                                while not "start" in driver.find_element_by_xpath(
                                        '//div[@class="_1awRl copyable-text selectable-text"]').text:
                                    time.sleep(5)
        except WebDriverException as e:
            report = SystemReporting()
            report.total_success_sent = len(all_phone_success_sent)
            report.total_failure_sent = len(all_phone_failed_sent)
            report.date_of_reporting = datetime.now()
            report.save()
            return HttpResponse("Please check your internet connection and refresh page to try again")
        report = SystemReporting()
        report.total_success_sent = len(all_phone_success_sent)
        report.total_failure_sent = len(all_phone_failed_sent)
        report.date_of_reporting = datetime.now()
        report.save()
        return render(request, 'whatsapp_send_report.html', {
            "phone_number": all_phone_numbers,
            "all_phone_sent": len(all_phone_success_sent),
            "all_phone_failed_sent": len(all_phone_failed_sent)
        })


def sendHaveWhat(request):
    phone_number_group, created = PhoneNumberGroup.objects.get_or_create(group_name="global")
    all_phone_numbers = DrPhoneNumber.objects.all().filter(have_whatsapp=True, group_id=phone_number_group).count()
    all_phone_failed_sent = []
    all_phone_success_sent = []
    if "GET" == request.method:
        return checkUserIsAuthenticated(request, 'whatsapp_send_3.html', {
            "all_phone_numbers": all_phone_numbers,
            "phone_number_group": PhoneNumberGroup.objects.all(),
        })
    else:
        image = request.FILES["image"]
        file = open(join(image_path, image.name), 'wb')
        file.write(image.read())
        file.close()
        filepath = image_path + image.name
        phone_group = int(request.POST.get('phone_number_group', phone_number_group.id))
        message = request.POST.get('message', '')
        split_message = message.split("\n")
        message_with_newline = ''
        for line_message in split_message:
            message_with_newline = message_with_newline + line_message
        timer = request.POST.get('timer', 20)
        username = getpass.getuser()
        options = Options()
        options.add_argument(
            "user-data-dir=C:\\Users\\" + username + "\\AppData\\Local\\Google\\Chrome\\User Data\\profile2")
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
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
            phone = DrPhoneNumber.objects.all().filter(have_whatsapp=True, group_id=phone_group)
            for i in range(0, len(phone)):
                if is_element_present(driver, "span", "data-icon", "alert-phone"):
                    return HttpResponse("Please check your internet connection on your phone and try again.")
                start_or_stop = driver.find_element_by_xpath(
                    '//div[@class="_1awRl copyable-text selectable-text"]').text
                if "stop" in start_or_stop:
                    time.sleep(1)
                    while not "start" in driver.find_element_by_xpath(
                            '//div[@class="_1awRl copyable-text selectable-text"]').text:
                        time.sleep(5)
                single_phone = phone.get(phone_number=phone[i].phone_number)
                driver.get('https://web.whatsapp.com/send?phone=' + single_phone.phone_number + '&text=' + ".")
                time.sleep(int(timer))
                while not is_element_present(driver, "div", "class", "_1awRl copyable-text selectable-text"):
                    time.sleep(2)
                start_or_stop = driver.find_element_by_xpath(
                    '//div[@class="_1awRl copyable-text selectable-text"]').text
                if "stop" in start_or_stop:
                    time.sleep(1)
                    print("stop in start_or_stop")
                    while not "start" in driver.find_element_by_xpath(
                            '//div[@class="_1awRl copyable-text selectable-text"]').text:
                        time.sleep(5)
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
                        all_phone_failed_sent.append(single_phone.phone_number)
                else:
                    # here we add new line by java script
                    msg = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')
                    driver.execute_script("arguments[0].innerText=arguments[1];", msg, message_with_newline)
                    msg.send_keys(" ")
                    sleep(1)
                    start_or_stop = driver.find_element_by_xpath(
                        '//div[@class="_1awRl copyable-text selectable-text"]').text
                    if "stop" in start_or_stop:
                        time.sleep(1)
                        print("stop in start_or_stop")
                        while not "start" in driver.find_element_by_xpath(
                                '//div[@class="_1awRl copyable-text selectable-text"]').text:
                            time.sleep(5)
                    if is_element_present(driver, "div", "title", "Attach"):
                        attachment_box = driver.find_element_by_xpath('//div[@title = "Attach"]')
                        attachment_box.click()
                        try:
                            image_box = driver.find_element_by_xpath(
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                            image_box.send_keys(filepath)
                            sleep(3)
                        except WebDriverException as e:
                            return HttpResponse("Please select an image from another directory and try again.")
                        if is_element_present(driver, "span", "data-icon", "send"):
                            send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
                            send_button.click()
                            single_phone.have_whatsapp = True
                            single_phone.number_of_message_sent += 1
                            single_phone.save()
                            all_phone_success_sent.append(single_phone.phone_number)
                            sleep(1)
                            if is_element_present(driver, "span", "aria-label", " Pending "):
                                sleep(1)
                                while is_element_present(driver, "span", "aria-label", " Pending "):
                                    sleep(2)
                            start_or_stop = driver.find_element_by_xpath(
                                '//div[@class="_1awRl copyable-text selectable-text"]').text
                            if "stop" in start_or_stop:
                                time.sleep(1)
                                while not "start" in driver.find_element_by_xpath(
                                        '//div[@class="_1awRl copyable-text selectable-text"]').text:
                                    time.sleep(5)
                    elif is_element_present(driver, "div", "title", "إرفاق"):
                        attachment_box = driver.find_element_by_xpath('//div[@title = "إرفاق"]')
                        attachment_box.click()
                        try:
                            image_box = driver.find_element_by_xpath(
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                            image_box.send_keys(filepath)
                            sleep(3)
                        except WebDriverException as e:
                            return HttpResponse("Please select an image from another directory and try again.")
                        if is_element_present(driver, "span", "data-icon", "send"):
                            send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
                            send_button.click()
                            single_phone.have_whatsapp = True
                            single_phone.number_of_message_sent += 1
                            single_phone.save()
                            all_phone_success_sent.append(single_phone.phone_number)
                            sleep(1)
                            if is_element_present(driver, "span", "aria-label", " الرسائل المُعَلَّقة "):
                                sleep(1)
                                while is_element_present(driver, "span", "aria-label", " الرسائل المُعَلَّقة "):
                                    sleep(2)
                            start_or_stop = driver.find_element_by_xpath(
                                '//div[@class="_1awRl copyable-text selectable-text"]').text
                            if "stop" in start_or_stop:
                                time.sleep(1)
                                while not "start" in driver.find_element_by_xpath(
                                        '//div[@class="_1awRl copyable-text selectable-text"]').text:
                                    time.sleep(5)
        except WebDriverException as e:
            report = SystemReporting()
            report.total_success_sent = len(all_phone_success_sent)
            report.total_failure_sent = len(all_phone_failed_sent)
            report.date_of_reporting = datetime.now()
            report.save()
            return HttpResponse("Please check your internet connection and refresh page to try again")
        report = SystemReporting()
        report.total_success_sent = len(all_phone_success_sent)
        report.total_failure_sent = len(all_phone_failed_sent)
        report.date_of_reporting = datetime.now()
        report.save()
        return render(request, 'whatsapp_send_report.html', {
            "phone_number": len(phone),
            "all_phone_sent": len(all_phone_success_sent),
            "all_phone_failed_sent": len(all_phone_failed_sent)
        })


def sendToSpecificNumber(request):
    all_phone_failed_sent = []
    all_phone_success_sent = []
    phones = DrPhoneNumber()
    phone_number_group, created = PhoneNumberGroup.objects.get_or_create(group_name="global")
    if "GET" == request.method:
        return checkUserIsAuthenticated(request, 'whatsapp_send_4.html', {
            "phone_number_group": PhoneNumberGroup.objects.all()
        })
    else:
        image = request.FILES["image"]
        specific_numbers = request.POST.get("specific_numbers", "0")
        specific_numbers_split = specific_numbers.split("\n")
        specific_numbers_list = []
        numbers = ''
        for number in specific_numbers_split:
            numbers = numbers + number
        for number in numbers.split():
            if number.isdigit():
                specific_numbers_list.append(int(number))

        file = open(join(image_path, image.name), 'wb')
        file.write(image.read())
        file.close()
        phone_group = int(request.POST.get('phone_number_group', phone_number_group.id))
        message = request.POST.get('message', '')
        split_message = message.split("\n")
        message_with_newline = ''
        for line_message in split_message:
            message_with_newline = message_with_newline + line_message
        timer = request.POST.get('timer', 20)
        username = getpass.getuser()
        options = Options()
        options.add_argument(
            "user-data-dir=C:\\Users\\" + username + "\\AppData\\Local\\Google\\Chrome\\User Data\\profile2")
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
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
                driver.get('https://web.whatsapp.com/')
                time.sleep(15)
            for i in specific_numbers_list:
                if is_element_present(driver, "span", "data-icon", "alert-phone"):
                    return HttpResponse("Please check your internet connection on your phone and try again.")
                start_or_stop = driver.find_element_by_xpath(
                    '//div[@class="_1awRl copyable-text selectable-text"]').text
                if "stop" in start_or_stop:
                    time.sleep(1)
                    while not "start" in driver.find_element_by_xpath(
                            '//div[@class="_1awRl copyable-text selectable-text"]').text:
                        time.sleep(5)
                driver.get('https://web.whatsapp.com/send?phone=' + str(i) + '&text=' + ".")
                time.sleep(int(timer))
                while not is_element_present(driver, "div", "class", "_1awRl copyable-text selectable-text"):
                    time.sleep(2)
                start_or_stop = driver.find_element_by_xpath(
                    '//div[@class="_1awRl copyable-text selectable-text"]').text
                if "stop" in start_or_stop:
                    time.sleep(1)
                    while not "start" in driver.find_element_by_xpath(
                            '//div[@class="_1awRl copyable-text selectable-text"]').text:
                        time.sleep(5)
                # this mean this phone number don't have whatsapp
                if not is_element_present(driver, "div", "id", "main"):
                    # this mean bot can't parse this page
                    if not is_element_present(driver, "div", "role", "button"):
                        pass
                    else:
                        user = driver.find_element_by_xpath('//div[@role = "button"]')
                        phones.group_id = phone_group
                        phones.phone_number = str(i)
                        phones.have_whatsapp = False
                        phones.note = ""
                        phones.save()
                        user.click()
                        all_phone_failed_sent.append(str(i))
                else:
                    # here we add new line by java script
                    msg = driver.find_element_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')
                    driver.execute_script("arguments[0].innerText=arguments[1];", msg, message_with_newline)
                    msg.send_keys(" ")
                    sleep(1)
                    start_or_stop = driver.find_element_by_xpath(
                        '//div[@class="_1awRl copyable-text selectable-text"]').text
                    if "stop" in start_or_stop:
                        time.sleep(1)
                        while not "start" in driver.find_element_by_xpath(
                                '//div[@class="_1awRl copyable-text selectable-text"]').text:
                            time.sleep(5)
                    if is_element_present(driver, "div", "title", "Attach"):
                        attachment_box = driver.find_element_by_xpath('//div[@title = "Attach"]')
                        attachment_box.click()
                        try:
                            image_box = driver.find_element_by_xpath(
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                            image_box.send_keys(image_path + image.name)
                            sleep(3)
                        except WebDriverException as e:
                            return HttpResponse("Please select an image from another directory and try again.")
                        if is_element_present(driver, "span", "data-icon", "send"):
                            send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
                            send_button.click()
                            phones.group_id = phone_group
                            phones.phone_number = str(i)
                            phones.number_of_message_sent += 1
                            phones.have_whatsapp = True
                            phones.note = ""
                            phones.save()
                            all_phone_success_sent.append(str(i))
                            sleep(1)
                            if is_element_present(driver, "span", "aria-label", " Pending "):
                                sleep(1)
                                while is_element_present(driver, "span", "aria-label", " Pending "):
                                    sleep(2)
                            start_or_stop = driver.find_element_by_xpath(
                                '//div[@class="_1awRl copyable-text selectable-text"]').text
                            if "stop" in start_or_stop:
                                time.sleep(1)
                                while not "start" in driver.find_element_by_xpath(
                                        '//div[@class="_1awRl copyable-text selectable-text"]').text:
                                    time.sleep(5)
                    elif is_element_present(driver, "div", "title", "إرفاق"):
                        attachment_box = driver.find_element_by_xpath('//div[@title = "إرفاق"]')
                        attachment_box.click()
                        try:
                            print(image_path + image.name)
                            image_box = driver.find_element_by_xpath(
                                '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
                            image_box.send_keys(image_path + image.name)
                            sleep(3)
                        except WebDriverException as e:
                            return HttpResponse("Please select an image from another directory and try again.")
                        if is_element_present(driver, "span", "data-icon", "send"):
                            send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
                            send_button.click()
                            phones.group_id = phone_group
                            phones.phone_number = str(i)
                            phones.number_of_message_sent += 1
                            phones.have_whatsapp = True
                            phones.note = ""
                            phones.save()
                            all_phone_success_sent.append(str(i))
                            sleep(1)
                            if is_element_present(driver, "span", "aria-label", " الرسائل المُعَلَّقة "):
                                sleep(1)
                                while is_element_present(driver, "span", "aria-label", " الرسائل المُعَلَّقة "):
                                    sleep(2)
                            start_or_stop = driver.find_element_by_xpath(
                                '//div[@class="_1awRl copyable-text selectable-text"]').text
                            if "stop" in start_or_stop:
                                time.sleep(1)
                                while not "start" in driver.find_element_by_xpath(
                                        '//div[@class="_1awRl copyable-text selectable-text"]').text:
                                    time.sleep(5)
        except WebDriverException as e:
            report = SystemReporting()
            report.total_success_sent = len(all_phone_success_sent)
            report.total_failure_sent = len(all_phone_failed_sent)
            report.date_of_reporting = datetime.now()
            report.save()
            return HttpResponse("Please check your internet connection and refresh page to try again")
        all_phone_sent = len(specific_numbers_list) - len(all_phone_failed_sent)
        report = SystemReporting()
        report.total_success_sent = len(all_phone_success_sent)
        report.total_failure_sent = len(all_phone_failed_sent)
        report.date_of_reporting = datetime.now()
        report.save()
        return render(request, 'whatsapp_send_report.html', {
            "phone_number": len(specific_numbers_list),
            "all_phone_sent": all_phone_sent,
            "all_phone_failed_sent": len(all_phone_failed_sent)
        })


def whatsappSendReport(request):
    if "GET" == request.method:
        if "back_to_home" in request.GET:
            return render(request, 'index.html', {
                "all_phones": DrPhoneNumber.objects.all().count(),
                "all_phones_have_whatsapp": DrPhoneNumber.objects.all().filter(have_whatsapp=True).count()
            })
        else:
            total_success_sent = request.GET.get('all_phone_sent', '0')
            total_failure_sent = request.GET.get('all_phone_failed_sent', '0')
            return checkUserIsAuthenticated(request, 'whatsapp_send_report.html', {
                "phone_number": request.GET.get('phone_number', '0'),
                "all_phone_sent": total_success_sent,
                "all_phone_failed_sent": total_failure_sent,
                "date_of_sent": datetime.now()
            })


def is_element_present(driver, a, b, c):
    try:
        driver.find_element_by_xpath("//" + a + "[@" + b + "=" + "'" + c + "'" + "]")
    except NoSuchElementException as e:
        return False
    return True


def deleteAllDataBase(request):
    if "GET" == request.method:
        if not request.user.is_authenticated:
            return redirect('admin/login/?next=/')
        else:
            DrPhoneNumber.objects.all().delete()
            SystemSetting.objects.all().delete()
            return render(request, 'index.html', {
                "all_phones": DrPhoneNumber.objects.all().count(),
                "all_phones_have_whatsapp": DrPhoneNumber.objects.all().filter(have_whatsapp=True).count()
            })
