from selenium import webdriver
from time import sleep

driver = webdriver.Chrome()
driver.get('https://web.whatsapp.com/')

name = '+963 950 404 087'
filepath = 'F:\1.png'

input('Enter anything after scanning QR code')

user = driver.find_element_by_xpath('//span[@title = "{}"]'.format(name))
user.click()

attachment_box = driver.find_element_by_xpath('//div[@title = "Attach"]')
attachment_box.click()

image_box = driver.find_element_by_xpath(
    '//input[@accept="image/*,video/mp4,video/3gpp,video/quicktime"]')
image_box.send_keys(filepath)

sleep(3)

# send_button = driver.find_element_by_xpath('//span[@data-icon="send-light"]')
send_button = driver.find_element_by_xpath('//span[@data-icon="send"]')
send_button.click()
