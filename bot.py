import os
import telebot
import yfinance as yf

from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import selenium
import json
import time
from selenium.webdriver.chrome.options import Options
import logging
import threading
from flask import Flask, request
from webserver import keep_alive


webUrl = "https://tap.az/elanlar/elektronika/telefonlar?utf8=%E2%9C%93&order=&q%5Buser_id%5D=&q%5Bcontact_id%5D=&q%5Bprice%5D%5B%5D=&q%5Bprice%5D%5B%5D=&p%5B749%5D=3855&p%5B916%5D=&p%5B917%5D=&p%5B918%5D=&p%5B920%5D=&p%5B743%5D=true&p%5B853%5D=&q%5Bregion_id%5D=&keywords=";

chat_id = -1001760489141;
API_KEY = os.getenv('API_KEY')
bot = telebot.TeleBot(API_KEY)
print(API_KEY);

server = Flask(__name__)

firstRun = True;
allData = [];

def sendMessage(msg, message = None):
    bot.send_message(chat_id, msg)

def sendLastItem(section):
    strMessage = section['name'] + '\n' + str(section['price'])+'\n' + section['time']+'\n'+ section['link']+'\n';
    sendMessage(strMessage);

def threadProcess(name):
    global firstRun;
    while(1):
        print("Thread %s: Starting", name)
        process();
        print("Thread %s: Updated!!!", name)
        if(firstRun):
            firstRun = False;
            sendMessage("!!!UPDATED!!!");
        time.sleep(3);

def process():
    global allData;
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(webUrl);
    
    productsList = []
    sectionContainer = driver.find_element(By.CSS_SELECTOR , 'div.js-endless-container');
    products = sectionContainer.find_elements(By.CSS_SELECTOR, 'div.products-i')

    for product in products:
        imgClass = product.find_element(By.CSS_SELECTOR, 'img');
        imgLink = imgClass.get_attribute("src")
        name = product.find_element(By.CSS_SELECTOR,'div.products-name').text
        price = product.find_element(By.CSS_SELECTOR,'span.price-val').text
        timeCreated = product.find_element(By.CSS_SELECTOR,'div.products-created').text
        linkTo = product.find_element(By.CSS_SELECTOR, 'a.products-link').get_attribute('href');
        intPrice = int(price.replace(' ',''));
        productsList.append({'name': name,
                        'img': imgLink,
                        'price': intPrice,
                        'time': timeCreated,
                        'link': linkTo})
    
    productsList.reverse();
    if(firstRun == False and allData[len(allData)-1]!= productsList[len(productsList)-1]):
        sendLastItem(productsList[len(productsList)-1]);
    allData = productsList;
    #for section in productsList:
        #print(section['name']);

@bot.message_handler(commands=['showall'])
def showall(message):
    sendMessage("Wait....")
    for section in allData:
        strMessage = section['name'] + '\n' + str(section['price'])+'\n' + section['time']+'\n'+ section['link']+'\n';
        #bot.send_photo(message.chat.id, section['link']);
        bot.send_message(message.chat.id, strMessage)

print("Main    : thread starting")
x = threading.Thread(target=threadProcess, args=(1,), daemon=True);
x.start()
print("Main    : thread started")

TOKEN = API_KEY;
#bot.polling()

@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://guarded-headland-29694.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))