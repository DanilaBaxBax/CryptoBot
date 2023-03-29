import telegram
#from telegram.ext import Updater
#from telegram.ext import CommandHandler
from tracker import get_prices
from string import Template
import json
import requests
import tracker2
import blockcypher
from moneywagon import AddressBalance
from web3 import Web3
from TrackerRUB import data2
import time
from credit_card_checker import CreditCardChecker
import random
import math
from bs4 import BeautifulSoup

import telebot
import aiogram
from telebot import types




API_TOKEN = 'YOUR_TOKEN' 



#updater = Updater(token=API_TOKEN,use_context=True) #use_context=True
#dispatcher = updater.dispatcher

def course(): # функция активации трэкера
    
    # chat_id = update.effective_chat.id
    message = ""

    crypto_data = get_prices()
    for i in crypto_data:
       coin = crypto_data[i]["coin"]
       price = crypto_data[i]["price"]
       change_day = crypto_data[i]["change_day"]
       change_hour = crypto_data[i]["change_hour"]
       message += f"Coin: {coin}\nPrice: ${price:,.2f}\nHour Change: {change_hour:.3f}%\nDay Change: {change_day:.3f}%\n\n"
    return message

    
bot = telebot.TeleBot(API_TOKEN)


def get_exchange_rate():
    url = 'https://cbr.ru/currency_base/daily/'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error getting exchange rate: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'class': 'data'})
    rows = table.find_all('tr')
    for row in rows:
        columns = row.find_all('td')
        if len(columns) > 0 and columns[1].text == 'USD':
            return float(columns[4].text.replace(',', '.'))

def get_bitcoin_rate():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error getting bitcoin rate: {e}")
        return None

    data = response.json()
    return data['bitcoin']['usd']

def welcome(message, edit=False):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("BTC1", switch_inline_query_current_chat="BTC1 "))
    markup.row(types.InlineKeyboardButton("BTC2", switch_inline_query_current_chat="BTC2 "))
    markup.row(types.InlineKeyboardButton("Tether1", switch_inline_query_current_chat="Tether1 "))
    markup.row(types.InlineKeyboardButton("Tether2", switch_inline_query_current_chat="Tether2 "))
    if edit:
        bot.edit_message_text("Выберите валюту и формулу для расчета:", message.chat.id, message.message_id, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Выберите валюту и формулу для расчета:", reply_markup=markup)

#@bot.message_handler(commands=['start'])
#def send_welcome(message):
 #  welcome(message)

def calculate_formula(input_value: str, formula: str) -> str:
    value = float(input_value)
    price= tracker2.scrape()
    rub_course = data2
    ruble_to_dollar = rub_course
    bitcoin_rate = price

    if ruble_to_dollar is None or bitcoin_rate is None:
        return "Ошибка: не удалось получить курс валют"

    if formula.lower() == "btc1":
        result = ((value / ruble_to_dollar) / bitcoin_rate) * 0.75
        result = round(result, 5)
    elif formula.lower() == "btc2":
        result = ((value * bitcoin_rate) * ruble_to_dollar) * 0.75
        result = round(result)
    elif formula.lower() == "tether1":
        result = (value / ruble_to_dollar) * 0.75
        result = round(result, 5)
    elif formula.lower() == "tether2":
        result = (value * ruble_to_dollar) * 0.75
        result = round(result)
    else:
        return "Ошибка: некорректная формула"
    return str(result)

def get_valid_range_message(formula):
    if formula.lower() == "btc1":
        return "Корректный диапазон для BTC1: 1000 ₽ - 200000 ₽"
    elif formula.lower() == "btc2":
        return "Корректный диапазон для BTC2: 0.0005 BTC - 0.1 BTC"
    elif formula.lower() == "tether1":
        return "Корректный диапазон для Tether1: 1000 ₽ - 200000 ₽"
    elif formula.lower() == "tether2":
        return "Корректный диапазон для Tether2: 14 USDT - 3000 USDT"
    else:
        return "Ошибка: некорректная формула"

def check_input_value(value, formula):
    value = float(value)
    if formula.lower() == "btc1" and 1000 <= value <= 200000:
        return True
    elif formula.lower() == "btc2" and 0.0005 <= value <= 0.1:
        return True
    elif formula.lower() == "tether1" and 1000 <= value <= 200000:
        return True
    elif formula.lower() == "tether2" and 14 <= value <= 3000:
        return True
    else:
        return False

def validate_input_value(value, formula):
    if not value.replace('.', '', 1).isdigit():
        return False, "❗️ Введите число"
    value = float(value)
    if formula.lower() == "btc1" and 1000 <= value <= 200000:
        return True, ""
    elif formula.lower() == "btc2" and 0.0005 <= value <= 0.1:
        return True, ""
    elif formula.lower() == "tether1" and 1000 <= value <= 200000:
        return True, ""
    elif formula.lower() == "tether2" and 14 <= value <= 3000:
        return True, ""
    else:
        if formula.lower() == "btc1":
            error_message = "❗️ Введите от 1000₽ до 200000₽"
        elif formula.lower() == "btc2":
            error_message = "❗️ Введите от 0.0005 BTC до 0.1 BTC"
        elif formula.lower() == "tether1":
            error_message = "❗️ Введите от 1000₽ до 200000₽"
        elif formula.lower() == "tether2":
            error_message = "❗️ Введите от 14 USDT до 3000 USDT"
        else:
            error_message = "Некорректная формула"

        return False, error_message

def get_description(value, formula, result):
    if formula.lower() == "btc1":
        return f"🍭 Покупка: {value} ₽ = {result} BTC"
    elif formula.lower() == "btc2":
        return f"🍭 Продажа: {value} BTC = {result} ₽"
    elif formula.lower() == "tether1":
        return f"🍭 Покупка : {value} ₽ = {result} USDT"
    elif formula.lower() == "tether2":
        return f"🍭 Продажа: {value} USDT = {result} ₽"
    else:
        return "Ошибка: некорректная формула"

@bot.inline_handler(func=lambda query: True)
def inline_calculator(query):
    query_data = query.query.split(" ", 1)
    if len(query_data) > 1:
        formula, input_value = query_data
        if input_value and formula:
            is_valid, error_message = validate_input_value(input_value, formula)
            if is_valid:
                result = calculate_formula(input_value, formula)
                title = get_description(input_value, formula, result)
                description = "✅ Нажмите сюда чтобы выбрать ✅"
                content = types.InputTextMessageContent(title)
                article = types.InlineQueryResultArticle(
                    id=0,
                    title=title,
                    input_message_content=content,
                    description=description,
                )
                bot.answer_inline_query(query.id, [article])
            else:
                title = "❗️ Некорректное значение"
                description = error_message
                content = types.InputTextMessageContent(title)
                article = types.InlineQueryResultArticle(
                    id=0,
                    title=title,
                    input_message_content=content,
                    description=description,
                )
                bot.answer_inline_query(query.id, [article])

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def ignore_message(message):
    pass




value = ''
old_value = ''

user_dict = {}
user_dict2 = {}
user_dict3 = {}
user_dict4 = {}


class user:
    def __init__(self,sum):
        
        
        self.sum = sum
        keys = {'Summ', 'Wallet', 'Summ', 'pay'}
        

        for key in keys:
            self.key = None

class user2:
    def __init__(self,sum):
        
        
        self.sum = sum
        keys = {'Summ', 'Wallet', 'Summ', 'pay'}
        

        for key in keys:
            self.key = None


class user3:
    def __init__(self,sum):
        
        
        self.sum = sum
        keys = {'Summ', 'Wallet', 'Summ', 'pay'}
        

        for key in keys:
            self.key = None


class user4:
    def __init__(self,sum):
        
        
        self.sum = sum
        keys = {'Summ', 'Wallet', 'Summ', 'pay'}
        

        for key in keys:
            self.key = None           

    
#@bot.message_handler(commands = ['Bitcoin_buy'])

def buy_btc(message): #ввод суммы для покупки биткоина
    
    global y
    global k
    global msg_to_delete3
    price= tracker2.scrape()
    rub_course = data2
    bot.delete_message(message.chat.id, msg_to_delete7.id)
    
  
    try:
        k = int (message.text)
        
        
    
        if (k >= 1000 and k <= 200000):
            chat_id = message.chat.id
            user_dict [chat_id]= user(message.text)
            user.pay = ((k /rub_course) / price) * 0.75
            y = ((k /rub_course) / price) * 0.75
            user.pay = round(user.pay, 5)
            y = round(y, 5)
            #bot.delete_message(message.chat.id, message.id)
            msg_to_delete3 = bot.send_message(message.chat.id, '⬇️Покупка BTC: {} ₽ \n💰Сумма  к получению:  {} BTC \n Введите Bitcon адрес кошелька, на который Вы хотите отправить:  {} BTC'.format(k,y,y))
            #msg = bot.edit_message_text(chat_id = message.call.chat.id,message_id= message.call.id, text='Введите адрес кошелька ')
            
            bot.delete_message(message.chat.id, message.id)
            
            #msg = bot.edit_message_text(message.chat.id, message.id, 'Введите кошелек')
            #msg = bot.edit_message_text(chat_id=message.chat.id, message_id=message.id, text = 'Введите кошелек')
            #bot.delete_message(message.chat.id, message.id)
            bot.register_next_step_handler(msg_to_delete3,buy_btc_2)
                     
        else :
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back_buy3')
            Inline.add (Back)
            #msg = bot.reply_to(message, 'Введите нормальное значение', reply_markup = Inline)
            msg = bot.send_message(message.chat.id,'Введите нормальное значение')

            
            bot.delete_message(message.chat.id, msg2)
            bot.register_next_step_handler(msg,buy_btc)
           
       
    except ValueError:
        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back_buy3')
        Inline.add(Back)
        #msg2 = bot.reply_to(message,'Введите нормальное значение', reply_markup = Inline)
        msg2 = bot.send_message(message.chat.id,'Введите нормальное значение')

        
        bot.delete_message(message.chat.id, msg2)
        bot.register_next_step_handler(msg2, buy_btc)    
        
      

def buy_btc_2(message): # Ввод адреса кошелька
    global q
    q = str (message.text)
    
    
  
    try:
        Inline = types.InlineKeyboardMarkup(row_width= 2)
        Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back')
        No = types.InlineKeyboardButton(text= '🔙Назад', callback_data= 'btc_buy_no')
        Yes = types.InlineKeyboardButton(text = ' ✅ Подтвердить', callback_data= 'btc_buy_yes')
        Inline.add(No, Yes)

        total = blockcypher.get_total_balance(message.text)
        
        group_id = 'your_group_ID' 
        chat_id = message.chat.id
        user = user_dict[chat_id]
        user.wallet = message.text
        #bot.send_message(message.chat.id,'Кошелек существует')
        #bot.send_message(message.chat.id,GetReGData(user, 'Ваша заявка', message.from_user.first_name), parse_mode= 'Markdown')
        
        bot.delete_message(message.chat.id, message.id)
        bot.delete_message(message.chat.id, msg_to_delete3.id)
       # bot.send_message(message.chat.id, 'Для продолжения работы с ботом нажмите кнопку назад', reply_markup= Inline)
        #bot.send_message(message.chat.id, 'Вы согласны продолжить?', reply_markup= Inline)
        bot.send_message(message.chat.id, 'ℹ️Информация о вашем обмене:\n 💰Сумма покупки: {} BTC\n 👛Адрес: {} \n 💰 Вы получите после покупки : {} \n \n 🚀Время отправки: от 30 до 120 минут \n ‼️Время ориентировочное и может измениться из-за нагрузки на Blockchain.\n \n ✅Если всё верно, то нажмите «подтвердить»:'.format(y,q, y),reply_markup=Inline)
        
       #msg = (group_id, GetReGData(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
        #bot.send_message(group_id, GetReGData(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
          
        

    except Exception as e:
        #total = AddressBalance().action('btc', message.text)
        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = '🔙Назад' , callback_data= 'Back_buy3')
        Inline.add(Back)
        #msg2 = bot.reply_to(message,'Адрес кошелька неверен, введите еще раз', reply_markup = Inline)
        msg2 = bot.send_message(message.chat.id,'Адрес кошелька неверен, введите еще раз',reply_markup= Inline)
        bot.register_next_step_handler(msg2, buy_btc_2)
        
    
    #group_id = 
    #chat_id = message.chat.id
    #user = user_dict[chat_id]
    #user.wallet = message.text
    #Inline = types.InlineKeyboardMarkup()
    #Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back')   
    #Inline.add(Back)

    

    #bot.send_message(message.chat.id,GetReGData(user, 'Ваша заявка', message.from_user.first_name), parse_mode= 'Markdown')
    #bot.send_message(message.chat.id, 'Для продолжения работы с ботом нажмите кнопку назад', reply_markup= Inline)
    #bot.send_message(group_id, GetReGData(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
   #bot.send_message(group_id, (user, 'id', bot.get_me().id),parse_mode = 'Markodown')
    

   


def GetReGData(user,title,name):
    t = Template ('\n Сумма покупки BTC: *$summ* \n Адрес кошелька: #*$wallet* \n Сумма к получению: *$pay* \n') 
    #$Title *$name*
    return t.substitute({
    'title' : title,
    'name' : name,
    'summ' : user.sum,
    'wallet' : user.wallet,
    'pay' : user.pay
         
    })      


def sell_btc(message):
    global v
    global g
    global msg_to_delete2
    price= tracker2.scrape()
    rub_course = data2
    bot.delete_message(message.chat.id, msg_to_delete5.id)

    try:
        g = float (message.text)
    
        if (g <= 0.1 and g >= 0.0003):
            chat_id = message.chat.id
           
            user_dict2 [chat_id]= user2(message.text)
            user2.pay =math.floor(((g * price) *  rub_course) * 0.75)
            v =  math.floor(((g * price) *  rub_course) * 0.75)
            #msg = bot.send_message(message.chat.id,'Введите номер карты')
            msg_to_delete2 = bot.send_message(message.chat.id, '⬇️Продажа BTC: {} BTC \n💰Сумма к получению:  {} ₽ \n 💳 Введите номер банковской карты'.format(g,v))

            
            bot.delete_message(message.chat.id, message.id)
            bot.register_next_step_handler(msg_to_delete2,sell_btc_2)
        else:
            #msg = bot.reply_to(message, 'Введите нормальное значение')
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back')
            Inline.add(Back)
            
            msg = bot.send_message(message.chat.id,'Введите нормальное значение')
            bot.register_next_step_handler(msg,sell_btc)
            


    except ValueError:
        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back')
        Inline.add(Back)
        #msg = bot.reply_to(message, 'Введите нормальное значение', reply_markup = Inline)
        
        msg = bot.send_message(message.chat.id,'Введите нормальное значение')
        bot.register_next_step_handler(msg,sell_btc)
        


def sell_btc_2(message):
    global t
    t = str(message.text)

    try:
        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back')
        No = types.InlineKeyboardButton(text= '🔙Назад', callback_data= 'btc_sell_no') 
        Yes = types.InlineKeyboardButton(text= '✅Подтвердить', callback_data= 'btc_sell_yes')   
        Inline.add(No, Yes)

        group_id = 'your_group_ID' 
        chat_id = message.chat.id
        user = user_dict2[chat_id]
        user.wallet = message.text
        

        #total = blockcypher.get_total_balance(message.text)
        #card_number = list(t)


        #check_digit = card_number.pop()


        #card_number.reverse()

        #processed_digits = []

        #for index, digit in enumerate(card_number):
         #   if index % 2 == 0:
          #      doubled_digit = int(digit) * 2

             
           #     if doubled_digit > 9:
            #        doubled_digit = doubled_digit - 9

                 #   processed_digits.append(doubled_digit)
            #else:
             #   processed_digits.append(int(digit))

       # total = int(check_digit) + sum(processed_digits)


        #if total % 10 == 0:
        if CreditCardChecker(t).valid():
            
            bot.delete_message(message.chat.id, message.id)
            bot.delete_message(message.chat.id, msg_to_delete2.id)
            
            #bot.send_message(message.chat.id,GetReGData2(user, 'Ваша заявка', message.from_user.first_name), parse_mode= 'Markdown')
            #bot.send_message(message.chat.id, 'Вы согласны продолжить?', reply_markup = Inline)
            msg = bot.send_message(message.chat.id, 'ℹ️ Информация о вашем обмене:\n \n 💰Сумма продажи: {} BTC \n 💳Реквизиты: {}  \n 💰Вы получите после продажи: {} ₽\n \n 🚀 Время отправки: от 30 до 120 минут \n !!Время ориентировочное и может измениться \n \n ✅ Если все верно,  то нажмите подтвредить'.format(g,t,v),reply_markup= Inline)


            #bot.send_message(group_id, GetReGData2(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
        else:
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text = '🔙Назад' , callback_data= 'Back')
            Inline.add(Back)
            #msg2 = bot.reply_to(message,'Номер карты неверен, введите еще раз', reply_markup= Inline)
            
            msg2 = bot.send_message(message.chat.id,'Номер карты неверен, введите еще раз',reply_markup= Inline)
        
            bot.register_next_step_handler(msg2, sell_btc_2)  
             
        
    except Exception as e:
        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = '🔙Назад' , callback_data= 'Back')
        Inline.add(Back)
        #msg2 = bot.reply_to(message,'Номер карты неверен, введите еще раз', reply_markup= Inline)
        
        msg2 = bot.send_message(message.chat.id,'Номер карты неверен, введите еще раз',reply_markup=Inline)
        bot.register_next_step_handler(msg2, sell_btc_2)
        





def GetReGData2(user,title,name):
    t = Template (' \n Сумма продажи BTC: *$summ* \n Номер карты: *$wallet* \n Сумма к получению: *$pay* \n') 
    #$Title *$name*
    return t.substitute({
    'title' : title,
    'name' : name,
    'summ' : user.sum,
    'wallet' : user.wallet,
    'pay' : user.pay
         
    })     


def buy_usdt(message): #ввод суммы для покупки USDT
    rub_course = data2
    global z
    global o
    global msg_to_delete4
    bot.delete_message(message.chat.id, msg_to_delete8.id)
    try:
        o = int (message.text)
        
    #price= course2()
    
        if (o >= 1000 and o <= 200000):
            chat_id = message.chat.id
            user_dict3 [chat_id]= user3(message.text)
            user3.pay = math.floor((o / rub_course) * 0.75)
            z = math.floor((o / rub_course) * 0.75)
            #msg = bot.send_message(message.chat.id,'Введите адрес кошелька ')
            msg_to_delete4 = bot.send_message(message.chat.id, '⬇️Покупка USDT: {} ₽ \n💰Сумма перевода:  {} USDT\n Введите USDT адрес кошелька, на который Вы хотите отправить:  {} USDT'.format(o,z,z))
            
           
            bot.delete_message(message.chat.id, message.id)
            bot.register_next_step_handler(msg_to_delete4,buy_usdt_2)
        else :
            msg = bot.send_message(message.chat.id,'Введите нормальное значение')
            #msg = bot.reply_to(message, 'Введите нормальное значение')
            bot.register_next_step_handler(msg,buy_usdt)

    except ValueError:
        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back_buy3')
        Inline.add(Back)
        #msg2 = bot.reply_to(message, 'Введите нормальное значение')
        msg2 = bot.send_message(message.chat.id,'Введите нормальное значение')
        bot.register_next_step_handler(msg2, buy_usdt)    

    
def buy_usdt_2(message): # Ввод адреса кошелька
    global f
    f = str (message.text)
    try:
        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back')
        No = types.InlineKeyboardButton(text= '🔙Назад', callback_data= 'usdt_buy_no')
        Yes = types.InlineKeyboardButton(text= '✅Подтвердить', callback_data= 'usdt_buy_yes')    
        Inline.add(No, Yes)
    
        group_id = 'your_group_ID'   
        chat_id = message.chat.id
        user = user_dict3[chat_id]
        user.wallet = message.text
        
        
        #card_number = list(x)


        #check_digit = card_number.pop()


        #card_number.reverse()

        #processed_digits = []

        #for index, digit in enumerate(card_number):
           # if index % 2 == 0:
              #  doubled_digit = int(digit) * 2

             
                #if doubled_digit > 9:
                #    doubled_digit = doubled_digit - 9

                #    processed_digits.append(doubled_digit)
            #else:
                #processed_digits.append(int(digit))

        #total = int(check_digit) + sum(processed_digits)


       # if total % 10 == 0:
         
        

        binance_testnet_rpc_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
        web3 = Web3(Web3.HTTPProvider(binance_testnet_rpc_url))
        wallet_address = f
        balance = Web3.to_checksum_address(wallet_address)


        #bot.send_message(message.chat.id,GetReGData3(user, 'Ваша заявка', message.from_user.first_name), parse_mode= 'Markdown')
       
        bot.delete_message(message.chat.id, message.id)
        bot.delete_message(message.chat.id, msg_to_delete4.id)
        #bot.send_message(message.chat.id,config.chat.id, GetReGData(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
        #bot.send_message(message.chat.id,'Вы согласны продолжить?', reply_markup= Inline)
        bot.send_message(message.chat.id, 'ℹ️Информация о вашем обмене:\n 💰Сумма покупки: {} USDT\n 👛Адрес: {} \n Вы получите после продажи: {} \n \n 🚀Время отправки: от 30 до 120 минут \n ‼️Время ориентировочное и может измениться из-за нагрузки на Blockchain.\n \n ✅Если всё верно, то нажмите «подтвердить»:'.format(z,f,z),reply_markup=Inline) 
        #bot.send_message(group_id, GetReGData3(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')

        #else:
         #   Inline = types.InlineKeyboardMarkup()
          #  Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back_buy3')
           # Inline.add (Back)
           # msg = bot.reply_to(message, 'Номер карты неверен, введите еще раз', reply_markup = Inline)
           # bot.register_next_step_handler(msg,buy_usdt_2)    



    except Exception as e:
        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = '🔙ННазад' , callback_data= 'Back_buy3')
        Inline.add(Back)
        #msg2 = bot.reply_to(message, 'Адрес кошелька неверен, введите еще раз', reply_markup = Inline)
        msg2 = bot.send_message(message.chat.id,'Адрес кошелька неверен, введите еще раз',reply_markup=Inline)
        bot.register_next_step_handler(msg2, buy_usdt_2)


   


def GetReGData3(user,title,name):
    t = Template (' \n Сумма покупки USDT: *$summ* \n Адрес кошелька: #*$wallet* \n Сумма к оплате: *$pay* \n') 
    #$Title *$name*
    return t.substitute({
    'title' : title,
    'name' : name,
    'summ' : user.sum,
    'wallet' : user.wallet,
    'pay' : user.pay
         
    }) 


def sell_usdt(message):
    global msg_to_delete1
    global a
    global c 
    rub_course = data2
    bot.delete_message(message.chat.id, msg_to_delete6.id)
    try:
        a = int(message.text)

        if (a <= 3000 and a >= 10) :
            chat_id = message.chat.id
            user_dict4 [chat_id]= user4(message.text)
            user4.pay = math.floor((a * rub_course) * 0.75)
            c = math.floor((a * rub_course) * 0.75)
            #msg = bot.send_message(message.chat.id,'Введите вашу карту')
            msg_to_delete1 = bot.send_message(message.chat.id, '⬇️Продажа USDT: {} USDT \n💰Сумма перевода:  {} ₽ \n 💳 Введите номер банковской карты'.format(a,c))

            
            bot.delete_message(message.chat.id, message.id)
            bot.register_next_step_handler(msg_to_delete1,sell_usdt_2)
        else:
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text = '🔙Назад' , callback_data= 'Back')
            Inline.add(Back)
            #msg = bot.reply_to(message, 'Введите нормальное значение')
            msg = bot.send_message(message.chat.id,'ведите нормальное значение',reply_markup= Inline)
            bot.register_next_step_handler(msg,sell_usdt)

    except ValueError:
        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = '🔙Назад' , callback_data= 'Back')
        Inline.add(Back)
        #msg2= bot.reply_to(message, 'Введите нормальное значение', reply_markup = Inline)
        msg2 = bot.send_message(message.chat.id,'Введите нормальное значение',reply_markup= Inline)
        bot.register_next_step_handler(msg2, sell_usdt)
        

def sell_usdt_2(message):
    global p
    p = str(message.text)

    try:

        Inline = types.InlineKeyboardMarkup()
        Back = types.InlineKeyboardButton(text = 'Назад' , callback_data= 'Back')
        No = types.InlineKeyboardButton(text= '🔙Назад', callback_data= 'usdt_sell_no')
        Yes = types.InlineKeyboardButton(text= '✅ Да', callback_data= 'usdt_sell_yes')    
        Inline.add(No,Yes)

        Inline2 = types.InlineKeyboardMarkup()
        Back_button = types.InlineKeyboardButton(text = '🔙Назад' , callback_data= 'Back')
        Inline2.add(Back_button)

        group_id = 'your_group_ID'
        chat_id = message.chat.id
        user = user_dict4[chat_id]
        user.wallet = message.text

        #binance_testnet_rpc_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
        #web3 = Web3(Web3.HTTPProvider(binance_testnet_rpc_url))
        #wallet_address = x
        #balance = Web3.to_checksum_address(wallet_address)
        
        #card_number = list(p)


        #check_digit = card_number.pop()


        #card_number.reverse()

       # processed_digits = []

        #for index, digit in enumerate(card_number):
           # if index % 2 == 0:
            #    doubled_digit = int(digit) * 2

             
              #  if doubled_digit > 9:
               #     doubled_digit = doubled_digit - 9

               #     processed_digits.append(doubled_digit)
            #else:
            #    processed_digits.append(int(digit))

       # total = int(check_digit) + sum(processed_digits)


        #if total % 10 == 0:
        if CreditCardChecker(p).valid():
            
            bot.delete_message(message.chat.id, message.id)
            bot.delete_message (message.chat.id, msg_to_delete1.id)
   


            #bot.send_message(message.chat.id,GetReGData4(user, 'Ваша заявка', message.from_user.first_name), parse_mode= 'Markdown')
            #bot.send_message(message.chat.id, 'Вы согласны продолжить?', reply_markup= Inline)
            msg = bot.send_message(message.chat.id, 'ℹ️ Информация о вашем обмене:\n \n 💰Сумма продажи: {} USDT \n 💳Реквизиты: {}  \n 💰Вы получите после продажи: {} ₽\n \n 🚀 Время отправки: от 30 до 120 минут \n !!Время ориентировочное и может измениться \n \n ✅Если все верно, то нажмите подтвердить '.format(a,p,c),reply_markup= Inline)

            #bot.send_message(group_id, GetReGData4(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')

        else:
            Inline2 = types.InlineKeyboardMarkup()
            Back_button = types.InlineKeyboardButton(text = '🔙Назад' , callback_data= 'Back')
            Inline2.add(Back_button)
            #msg2 = bot.reply_to(message, 'Ваша карта неверна,  введите еще раз', reply_markup = Inline)
            msg2 = bot.send_message(message.chat.id,'Ваша карта неверна,  введите еще раз',reply_markup=Inline2)
            bot.register_next_step_handler(msg2, sell_usdt_2)
 



    except Exception as e:
        Inline2 = types.InlineKeyboardMarkup()
        Back_button = types.InlineKeyboardButton(text = '🔙Назад' , callback_data= 'Back_sell3')
        Inline2.add(Back_button)
        #msg2 = bot.reply_to(message, 'Ваша карта неверна,  введите еще раз', reply_markup = Inline)
        msg2 = bot.send_message(message.chat.id,'Ваша карта неверна,  введите еще раз', reply_markup= Inline2)
        bot.register_next_step_handler(msg2, sell_usdt_2)




def GetReGData4(user,title,name):
    t = Template (' \n Сумма продажи USDT: *$summ* \n Номер карты : *$wallet* \n Сумма к получению: *$pay* \n') 
    #$Title *$name*
    return t.substitute({
    'title' : title,
    'name' : name,
    'summ' : user.sum,
    'wallet' : user.wallet,
    'pay' : user.pay
         
    })

#@bot.message_handler(commands = ['calculator'])

# def check_btc_buy_course(message):
#      price= tracker2.scrape()
#      rub_course = data2
#      global input_check_btc_buy_course, calculate_check_btc_buy_course
     
#      try:
#          input_check_btc_buy_course = int(message.text)
#          calculate_check_btc_buy_course = ((input_check_btc_buy_course / rub_course)/ price) * 0.75
#          msg = bot.send_message(message.chat.id,'После покупки BTC на сумму {} RUB \n Вы получите {} BTC '.format(input_check_btc_buy_course,calculate_check_btc_buy_course))
#          bot.register_next_step_handler(msg, check_btc_buy_course)

#      except ValueError:
#          #Inline = types.InlineKeyboardMarkup()
#          #Back = types.InlineKeyboardMarkup(text = 'Назад',reply_markup = Inline)
#          #Inline.add(Back)
#          msg2 = bot.send_message(message.chat.id,'Введите нормальное значение')
#          bot.register_next_step_handler(msg2, check_btc_buy_course)

       
# def check_btc_sell_course(message):
#     price= tracker2.scrape()
#     rub_course = data2
#     global input_check_btc_sell_course, calculate_check_btc_sell_course
#     try:
#         input_check_btc_sell_course = float(message.text)
#         calculate_check_btc_sell_course = ((input_check_btc_sell_course * price) * rub_course) * 0.75 
#         msg3 = bot.send_message(message.chat.id,'После продажи BTC на сумму {} BTC\n Вы получите {} RUB '.format(input_check_btc_sell_course,calculate_check_btc_sell_course))
#         bot.register_next_step_handler(msg3, check_btc_sell_course) 

#     except ValueError:
#         msg4 = bot.send_message(message.chat.id, 'Введите нормальное значение')
#         bot.register_next_step_handler(msg4, check_btc_sell_course)    

# def check_usdt_buy_course(message):
#     rub_course = data2
#     global input_check_usdt_buy_course, calculate_check_usdt_buy_course
#     try:
#         input_check_usdt_buy_course = int(message.text)
#         calculate_check_usdt_buy_course = ((input_check_usdt_buy_course) / rub_course) * 0.75
#         msg5 = bot.send_message(message.chat.id,'После покупки USDT на сумму {} RUB\n Вы получите {} USDT '.format(input_check_usdt_buy_course, calculate_check_usdt_buy_course))
#         bot.register_next_step_handler(msg5, check_btc_sell_course) 
#     except ValueError:
#         msg6 = bot.send_message(message.chat.id, 'Введите нормальное значение')
#         bot.register_next_step_handler(msg6, check_usdt_buy_course)

# def check_usdt_sell_course(message):
#     rub_course = data2
#     global input_check_usdt_sell_course,calculate_check_usdt_sell_course
#     try:
#         input_check_usdt_sell_course = int (message.text)
#         calculate_check_usdt_sell_course = ((input_check_usdt_buy_course) * rub_course) * 0.75
#         msg7 = bot.send_message(message.chat.id,'После продажи USDT на сумму {} USDT \n Вы получите {} RUB '.format(input_check_usdt_sell_course, calculate_check_usdt_sell_course))
#         bot.register_next_step_handler(msg7, check_btc_sell_course) 
#     except ValueError:
#         msg8 = bot.send_message(message.chat.id, 'Введите нормальное значение')
#         bot.register_next_step_handler(msg8, check_usdt_sell_course)       



def calculator(message):  
    global value 
      

    if value == '':
            Calculator_usdt = types.InlineKeyboardMarkup(row_width= 3)
            button_1 = types.InlineKeyboardButton(text = '1', callback_data= '1')
            button_2 = types.InlineKeyboardButton(text = '2', callback_data= '2')
            button_3 = types.InlineKeyboardButton(text = '3', callback_data= '3')
            button_4 = types.InlineKeyboardButton(text= '4', callback_data= '4')
            button_5 = types.InlineKeyboardButton(text = '5', callback_data= '5')
            button_6 = types.InlineKeyboardButton(text= '6', callback_data= '6')
            button_7 = types.InlineKeyboardButton(text= '7', callback_data= '7')
            button_8 = types.InlineKeyboardButton(text = '8', callback_data= '8')
            button_9 = types.InlineKeyboardButton(text = '9', callback_data= '9')
            button_10 = types.InlineKeyboardButton(text = '=', callback_data= '=')
            button_11 = types.InlineKeyboardButton(text= 'C', callback_data= 'C')
            button_12 = types.InlineKeyboardButton(text = '0', callback_data= '0')
            button_13 = types.InlineKeyboardButton(text = '.', callback_data= '.')
           
            Calculator_usdt.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9, button_13, button_12, button_11, button_10)
            bot.send_message(message.from_user.id, '0', reply_markup= Calculator_usdt)
            
    else:
            Calculator_usdt = types.InlineKeyboardMarkup(row_width= 3)
            button_1 = types.InlineKeyboardButton(text = '1', callback_data= '1')
            button_2 = types.InlineKeyboardButton(text = '2', callback_data= '2')
            button_3 = types.InlineKeyboardButton(text = '3', callback_data= '3')
            button_4 = types.InlineKeyboardButton(text= '4', callback_data= '4')
            button_5 = types.InlineKeyboardButton(text = '5', callback_data= '5')
            button_6 = types.InlineKeyboardButton(text= '6', callback_data= '6')
            button_7 = types.InlineKeyboardButton(text= '7', callback_data= '7')
            button_8 = types.InlineKeyboardButton(text = '8', callback_data= '8')
            button_9 = types.InlineKeyboardButton(text = '9', callback_data= '9')
            button_10 = types.InlineKeyboardButton(text = '=', callback_data= '=')
            button_11 = types.InlineKeyboardButton(text= 'C', callback_data= 'C')
            button_12 = types.InlineKeyboardButton(text = '0', callback_data= '0')
            button_13 = types.InlineKeyboardButton(text = '.', callback_data= '.')
           
            Calculator_usdt.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9, button_13, button_12, button_11, button_10)
            bot.send_message(message.chat.id, value, reply_markup= Calculator_usdt)


               
    # if value == '':
    #             Calculator_usdt = types.InlineKeyboardMarkup(row_width= 3)
    #             button_1 = types.InlineKeyboardButton(text = '1', callback_data= '1')
    #             button_2 = types.InlineKeyboardButton(text = '2', callback_data= '2')
    #             button_3 = types.InlineKeyboardButton(text = '3', callback_data= '3')
    #             button_4 = types.InlineKeyboardButton(text= '4', callback_data= '4')
    #             button_5 = types.InlineKeyboardButton(text = '5', callback_data= '5')
    #             button_6 = types.InlineKeyboardButton(text= '6', callback_data= '6')
    #             button_7 = types.InlineKeyboardButton(text= '7', callback_data= '7')
    #             button_8 = types.InlineKeyboardButton(text = '8', callback_data= '8')
    #             button_9 = types.InlineKeyboardButton(text = '9', callback_data= '9')
    #             button_10 = types.InlineKeyboardButton(text = '=', callback_data= '=')
    #             button_11 = types.InlineKeyboardButton(text= 'C', callback_data= 'C')
    #             button_12 = types.InlineKeyboardButton(text = '0', callback_data= '0')
    #             button_13 = types.InlineKeyboardButton(text = '.', callback_data= '.')
           
    #             Calculator_usdt.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9, button_13, button_12, button_11, button_10)
    #             bot.send_message(message.chat.id, '0', reply_markup= Calculator_usdt)
    # else:
    #             Calculator_usdt = types.InlineKeyboardMarkup(row_width= 3)
    #             button_1 = types.InlineKeyboardButton(text = '1', callback_data= '1')
    #             button_2 = types.InlineKeyboardButton(text = '2', callback_data= '2')
    #             button_3 = types.InlineKeyboardButton(text = '3', callback_data= '3')
    #             button_4 = types.InlineKeyboardButton(text= '4', callback_data= '4')
    #             button_5 = types.InlineKeyboardButton(text = '5', callback_data= '5')
    #             button_6 = types.InlineKeyboardButton(text= '6', callback_data= '6')
    #             button_7 = types.InlineKeyboardButton(text= '7', callback_data= '7')
    #             button_8 = types.InlineKeyboardButton(text = '8', callback_data= '8')
    #             button_9 = types.InlineKeyboardButton(text = '9', callback_data= '9')
    #             button_10 = types.InlineKeyboardButton(text = '=', callback_data= '=')
    #             button_11 = types.InlineKeyboardButton(text= 'C', callback_data= 'C')
    #             button_12 = types.InlineKeyboardButton(text = '0', callback_data= '0')
    #             button_13 = types.InlineKeyboardButton(text = '.', callback_data= '.')
           
    #             Calculator_usdt.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9, button_13, button_12, button_11, button_10)
    #             bot.send_message(message.chat.id, value, reply_markup= Calculator_usdt)


        #     Calculator_usdt = types.InlineKeyboardMarkup(row_width= 3)
        #     global value 
        #     global old_value
        # button_1 = types.InlineKeyboardButton(text = '1', callback_data= '1')
        # button_2 = types.InlineKeyboardButton(text = '2', callback_data= '2')
        # button_3 = types.InlineKeyboardButton(text = '3', callback_data= '3')
        # button_4 = types.InlineKeyboardButton(text= '4', callback_data= '4')
        # button_5 = types.InlineKeyboardButton(text = '5', callback_data= '5')
        # button_6 = types.InlineKeyboardButton(text= '6', callback_data= '6')
        # button_7 = types.InlineKeyboardButton(text= '7', callback_data= '7')
        # button_8 = types.InlineKeyboardButton(text = '8', callback_data= '8')
        # button_9 = types.InlineKeyboardButton(text = '9', callback_data= '9')
        # button_10 = types.InlineKeyboardButton(text = '=', callback_data= '=')
        # button_11 = types.InlineKeyboardButton(text= 'C', callback_data= 'C')
        # button_12 = types.InlineKeyboardButton(text = '0', callback_data= '0')
        # button_13 = types.InlineKeyboardButton(text = '.', callback_data= '.')
        # Calculator_usdt.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9, button_13, button_12, button_11, button_10)
    
        
    #if message.id == 'C':
     #       value = ''
    #elif message.id == '=':
    #        value = float(value) * 1.1
    #        value = str(value)
            
            
    #else:
    #    value += message.id
            

    #    if value != old_value:
     #     if value == '':
     #         bot.edit_message_text(chat_id= message.chat.id, message_id= message.id, text= '0', reply_markup= Calculator_usdt)
     #     else:
     #          bot.edit_message_text(chat_id= message.chat.id, message_id= message.id, text= value, reply_markup= Calculator_usdt)     
 
      #  old_value = value         
            
            

    
@bot.message_handler(commands = ['start'])


def start(message):
 
 

 bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
 Inline = types.InlineKeyboardMarkup(row_width= 2)
 item1 = types.InlineKeyboardButton(text = '⬇️Купить' , callback_data= 'buy')
 item2 = types.InlineKeyboardButton(text = '⬆️Продать', callback_data='sell') 
 item3 = types.InlineKeyboardButton(text = '💬Чат', url = 'https://t.me/+c2iY0XEkYzlhZGNk')
 item4 = types.InlineKeyboardButton(text = '📢Канал', url= 'https://t.me/candyshop_exchange')
 item5 = types.InlineKeyboardButton(text = '❓Отзывы', url= 'https://t.me/candyshop_exchange_reviews')
 item6 = types.InlineKeyboardButton(text = '👨🏼‍🚀Оператор', url= 'https://t.me/candyshop_exchange_support')
 item7 = types.InlineKeyboardButton(text = '📈Курс', callback_data= 'course')
 #Course = types.InlineKeyboardButton(text= '📈Курс', switch_inline_query_current_chat= '')

 item8 = types.InlineKeyboardButton(text = 'ℹ️Инфо', callback_data= 'info')

 

 Inline.add(item1, item2, item3, item4, item5, item6, item7, item8)

 
 
 
 bot.send_message(message.chat.id, ' 🍭 CANDYSHOP EXCHANGE \n \n 🔄Купить и продать криптовалюту\n 🔐 Конфиденциально \n 💫 Быстро и удобно \n 🔥 Поддержка клиентов 24/7 \n' , reply_markup = Inline)
 
 
 
 

 

 
     

           
 
@bot.callback_query_handler(func = lambda call: True )

def answer(call):
        username= call.message.chat.username
        number = random.randint(10000, 99999)
       
        #user_input  = call.message.text
        #time.sleep(1)
        #bot.delete_message(call.chat.id, user_input.id)

        
    
        if call.data == 'chat':
          Inline = types.InlineKeyboardMarkup()
          url_chat = types.InlineKeyboardButton(text = 'Чат', url = 'https://t.me/+c2iY0XEkYzlhZGNk')
          back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
          Inline.add(back,url_chat)

          bot.send_message(call.message.chat.id,'Вы зашли в чат',reply_markup = Inline)

        #elif call.data == 'channel':
         #   Inline = types.InlineKeyboardMarkup()
          #  back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
           # Inline.add(back)

          #  bot.send_message(call.message.chat.id,'https://t.me/candyshop_exchange_channel', reply_markup = Inline)
            

        #elif call.data == 'Test':
        #    Inline = types.InlineKeyboardMarkup()
         #   test1 = types.InlineKeyboardButton(text= 'test1', callback_data= 'test1')
          #  test2 = types.InlineKeyboardButton(text='test2',callback_data='test2')
          #  Inline.add(test1,test2)
           # bot.edit_message_text(chat_id=call.message.chat.id, message_id= call.message.id, text= 'eue')
           # bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id,reply_markup=Inline)

       # elif call.data == 'otzivi':
        #    Inline = types.InlineKeyboardMarkup()
         #   back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
          #  Inline.add(back)
            
           # bot.send_message(call.message.chat.id, ' Вы зашли в Отзывы', reply_markup = Inline)
            #bot.send_message(call.message.chat.id, ' Ссылка на Отзывы\n https://vk.com/danilabaxbax ')

        #elif call.data == 'otzivi':
         #   Inline = types.InlineKeyboardMarkup()
          #  back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
           # Inline.add(back)

            #bot.send_message(call.message.chat.id, ' Вы зашли в Отзывы', reply_markup = Inline)
            #bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=' Вы зашли в Отзывы')
            #bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)    
  

        #elif call.data == 'operator':
         #   Inline = types.InlineKeyboardMarkup()
          #  back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
           # Inline.add(back)

            #bot.send_message(call.message.chat.id,'@candyshop_exhange', reply_markup = Inline)

        #elif call.data == 'course':
         #   Inline = types.InlineKeyboardMarkup()
          #  back = types.InlineKeyboardButton(text='Назад', callback_data= 'Back')
           # Inline.add(back)
            #course_message = course()
            #bot.send_message(call.message.chat.id, f'{course_message}',reply_markup= Inline)
            #bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=f'{course_message}')
            #bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)


        elif call.data == 'course':
             Inline = types.InlineKeyboardMarkup(row_width= 2)
             Buy = types.InlineKeyboardButton(text='⬇️Купить',callback_data= 'course_buy')
             Sell = types.InlineKeyboardButton(text= '⬆️Продать', callback_data= 'course_sell')
             Back = types.InlineKeyboardButton(text= '🔙Назад', callback_data= 'Back')
             Inline.add(Buy,Sell,Back) 

             bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.message.id, text= 'Купить или продать?')
             bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup= Inline)


        elif call.data == 'course_buy':
            Inline = types.InlineKeyboardMarkup(row_width= 2 ) 
            BTC = types.InlineKeyboardButton(text='🪙BTC', callback_data= 'course_buy_btc')
            USDT = types.InlineKeyboardButton(text= '💵USDT', callback_data= 'course_buy_usdt')
            Back = types.InlineKeyboardButton(text='🔙Назад',callback_data= 'Back')
            Inline.add(BTC,USDT,Back)

            bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.message.id, text= 'Какую валюту вы хотите купить?')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup= Inline)

        elif call.data == 'course_buy_btc':
            Inline = types.InlineKeyboardMarkup(row_width= 1  )
            Check_BTC_BUY = types.InlineKeyboardButton(text= '📈Посчитать курс',switch_inline_query_current_chat= ' BTC1 ')
            Back = types.InlineKeyboardButton(text='🔙Назад', callback_data= 'Back')
            Inline.add (Check_BTC_BUY,Back)

            msg = bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.message.id, text= 'Введите сумму покупки BTC')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup= Inline)
            #bot.register_next_step_handler(msg, check_btc_buy_course)

        elif call.data == 'course_buy_usdt':
            Inline = types.InlineKeyboardMarkup(row_width= 1)
            Check_USDT_BUY = types.InlineKeyboardButton(text= '📈Посчитать курс',switch_inline_query_current_chat= ' tether1 ')
            Back = types.InlineKeyboardButton(text='🔙Назад',callback_data='Back')
            Inline.add(Check_USDT_BUY,Back)

            msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id= call.message.id, text='На какую сумму вы купить USDT?')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id,message_id= call.message.id, reply_markup= Inline)
            #bot.register_next_step_handler(msg, check_usdt_buy_course)



        elif call.data == 'course_sell':
            Inline = types.InlineKeyboardMarkup(row_width= 2)
            BTC = types.InlineKeyboardButton(text= '🪙BTC',callback_data= 'course_sell_btc')
            USDT = types.InlineKeyboardButton(text= '💵USDT', callback_data='course_sell_usdt')
            Back = types.InlineKeyboardButton(text='🔙Назад',callback_data= 'Back')
            Inline.add(BTC,USDT, Back)

            bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.message.id, text = 'Какую валюту вы хотите продать?' )
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup= Inline)


        elif call.data =='course_sell_btc':
            Inline = types.InlineKeyboardMarkup(row_width= 1)
            Check_BTC_SELL = types.InlineKeyboardButton(text= '📈Посчитать курс',switch_inline_query_current_chat= ' BTC2 ')

            Back = types.InlineKeyboardButton(text='🔙Назад',callback_data= 'Back')
            Inline.add(Check_BTC_SELL,Back)

            msg = bot.edit_message_text(chat_id= call.message.chat.id,message_id= call.message.id, text='На какую сумму вы хотите продать BTC?')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id,reply_markup=Inline)
            #bot.send_message(call.message.chat.id, 'На какую сумму вы хотите продать BTC')
            #bot.register_next_step_handler(msg, check_btc_sell_course)
              

        elif call.data =='course_sell_usdt':
            Inline = types.InlineKeyboardMarkup(row_width= 1)
            Check_USDT_SELL = types.InlineKeyboardButton(text= '📈Посчитать курс',switch_inline_query_current_chat= ' tether2 ')

            Back = types.InlineKeyboardButton(text='🔙Назад',callback_data= 'Back')
            Inline.add(Check_USDT_SELL,Back)

            msg = bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.message.id, text='На какую сумму вы хотите продать USDT?')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)       
            #bot.register_next_step_handler(msg, check_usdt_sell_course)
        
        elif call.data == 'info':
            Inline = types.InlineKeyboardMarkup(row_width=1)
            Info2 = types.InlineKeyboardButton(text='Как работает обменник',callback_data= 'info 2')
            back = types.InlineKeyboardButton(text='Назад', callback_data= 'Back')
            Inline.add(Info2,back)

            #bot.send_message(call.message.chat.id, ' Вы зашли в Инфо', reply_markup = Inline)
            #bot.send_message(call.message.chat.id, ' Ссылка на Инфо\n https://vk.com/danilabaxbax ')
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=' ℹ️ ИНФО \n \n 🍭 CandyShop - это автоматический бот для обмена криптовалюты. \n \n  ✅ Мы работаем 24/7 \n \n  🔄 Все обмены проходят быстро и чётко, без какого либо вмешательства. \n \n  🔐 Мы не храним и не собираем ваши данные, все транзакции безопасны и полностью конфиденциальны! \n  \n 👨🏼‍🚀 Наши операторы работают круглосуточно и всегда будут рады помочь или ответить на Ваши вопросы!\n \n @candyshop_exchange_support ')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)

        elif call.data == 'info 2':
            Inline = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton(text='Назад',callback_data= 'info')
            Inline.add(back)

            bot.edit_message_text(chat_id= call.message.chat.id,message_id = call.message.id,text='Как работает обменник? \n \n  1️⃣ Нажмите кнопку «Купить» или «Продать».  \n \n  2️⃣ Бот предложит Вам выбрать необходимую валюту  \n  \n 3️⃣ После этого введите сумму. \n \n  4️⃣ Бот создаст заявку, которую Вам будет необходимо оплатить по указанным реквизитам.  \n \n  5️⃣ Всё! Бот обработает заявку и после подтверждения о зачислении высших средств, совершит обмен и вы получите необходимую валюту в максимально короткие сроки! \n \n  ❗️ОЧЕНЬ ВАЖНО ❗️Если вы оплатили неверную сумму, то Вам нужно связаться с оператором, предоставить ему номер заявки и отправить подтверждение перевода. \n \n  Наша круглосуточная поддержка: @candyshop_exchange_support\n' )
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id= call.message.id, reply_markup= Inline)

        elif call.data == 'buy':
           Inline = types.InlineKeyboardMarkup(row_width=2)
           itembuy1 = types.InlineKeyboardButton(text = '🪙Bitcoin', callback_data='Bitcoin_buy')
           itembuy2 = types.InlineKeyboardButton(text = '💵USDT (Tether ERC-20)', callback_data='USDT_buy')
           back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
           Inline.add(itembuy1,itembuy2,back)
    
            
            #bot.send_message(call.message.chat.id, ' Выберите валюту, которую хотите купить', reply_markup = Inline)
           bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=' 🔄 Выберите валюту, которую хотите приобрести')
           bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
           
            


        elif call.data == 'Bitcoin_buy':
          global msg_to_delete7
          Inline = types.InlineKeyboardMarkup()
          backbuy = types.InlineKeyboardButton(text='Назад', callback_data='Back_buy1')

          Inline.add(backbuy)

            #bot.send_message(call.message.chat.id,'На какую сумму вы хотите купить Bitcoin?', reply_markup= Inline)
          msg_to_delete7 = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='❔ На какую сумму вы хотите купить Bitcoin? \n (Напишите сумму от 1000 до 200000 RUB) \n 👨🏼‍🚀Если вам необходима большая сумма обмена, напишите нашему оператору: @candyshop_exchange_support ')
          bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
          bot.register_next_step_handler(msg_to_delete7, buy_btc)
          
          #time.sleep(60)
          #bot.delete_message(call.message.chat.id, call.message.id)
          
          
            
            


        elif call.data == 'USDT_buy':
           global msg_to_delete8
           Inline = types.InlineKeyboardMarkup()
           backbuy = types.InlineKeyboardButton(text='Назад', callback_data = 'Back_buy2')
           Inline.add(backbuy)

            #bot.send_message(call.message.chat.id,'На какую сумму вы хотите купить USDT (Tether ERC-20)?', reply_markup= Inline)
           msg_to_delete8 = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=' ❔ На какую сумму вы хотите купить USDT (Tether ERC-20)?  \n (Напишите сумму от 1000 до 200000 RUB) \n 👨🏼‍🚀Если вам необходима большая сумма обмена, напишите нашему оператору: @candyshop_exchange_support')
           bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
           bot.register_next_step_handler(msg_to_delete8, buy_usdt)

           #time.sleep(60)
           #bot.delete_message(call.message.chat.id, call.message.id)
        

        elif call.data == 'Back_buy1':
            Inline = types.InlineKeyboardMarkup()
            itembuy1 = types.InlineKeyboardButton(text = '🪙Bitcoin', callback_data='Bitcoin_buy')
            itembuy2 = types.InlineKeyboardButton(text = '💵USDT (Tether ERC-20)', callback_data='USDT_buy')
            back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
            Inline.add(back,itembuy1,itembuy2)

            #bot.send_message(call.message.chat.id, ' Выберите валюту, которую хотите купить', reply_markup = Inline)
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=' 🔄 Выберите валюту, которую хотите приобрести')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)


        elif call.data == 'Back_buy2':
            Inline = types.InlineKeyboardMarkup()
            itembuy1 = types.InlineKeyboardButton(text = '🪙Bitcoin', callback_data='Bitcoin_buy')
            itembuy2 = types.InlineKeyboardButton(text = '💵USDT (Tether ERC-20)', callback_data='USDT_buy')
            back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
            Inline.add(back,itembuy1,itembuy2)

            #bot.send_message(call.message.chat.id, ' Выберите валюту, которую хотите купить', reply_markup = Inline)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=' 🔄 Выберите валюту, которую хотите приобрести')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)         


        elif call.data == 'sell':
            Inline = types.InlineKeyboardMarkup(row_width=2)
            itemsell1 = types.InlineKeyboardButton(text='🪙Bitcoin', callback_data= 'Bitcoin_sell')
            itemsell2 = types.InlineKeyboardButton(text='💵USDT (Tether ERC-20)', callback_data= 'USDT_sell')
            back = types.InlineKeyboardButton(text='Назад', callback_data = 'Back')
            Inline.add(itemsell1,itemsell2,back)

            #bot.send_message(call.message.chat.id, ' Выберите валюту, которую хотите продать', reply_markup = Inline)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='❔ Выберите валюту, которую хотите продать')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
            


        elif call.data == 'Bitcoin_sell':
            global msg_to_delete5
            Inline = types.InlineKeyboardMarkup()
            backsell = types.InlineKeyboardButton(text='Назад',callback_data='Back_sell1')
            Inline.add(backsell)
            
            #bot.send_message(call.message.chat.id,'На какую сумму вы хотите продать Bitcoin?', reply_markup= Inline)
            msg_to_delete5 = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='❔ На какую сумму вы хотите продать Bitcoin \n (Напишите сумму от 0.0003 до 0.1 BTC) \n \n ⛔ Внимание! Выплаты производятся только на карты российских банков \n \n 👨🏼‍🚀Если вам необходима большая сумма обмена, напишите нашему оператору: @candyshop_exchange_support \n')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
            bot.register_next_step_handler(msg_to_delete5, sell_btc)

            #time.sleep(15)
            #bot.delete_message(call.message.chat.id, call.message.id, timeout= 15)


        elif call.data == 'USDT_sell':
            global msg_to_delete6
            Inline = types.InlineKeyboardMarkup()
            backsell = types.InlineKeyboardButton(text='Назад',callback_data = 'Back_sell2')
            Inline.add(backsell)

            #bot.send_message(call.message.chat.id,'На какую сумму вы хотите продать USDT (Tether ERC-20)?', reply_markup= Inline)
            msg_to_delete6 = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='❔ На какую сумму вы хотите продать USDT (Tether ERC-20) \n (Напишите сумму от 10 до 3000 USDT) \n \n⛔Внимание! Выплаты производятся только на карты российских банков\n \n  👨🏼‍🚀Если вам необходима большая сумма обмена, напишите нашему оператору: @candyshop_exchange_support\n')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
            bot.register_next_step_handler(msg_to_delete6, sell_usdt)

            #time.sleep(15)
            #bot.delete_message(call.message.chat.id, call.message.id,timeout= 15)


        elif call.data == 'Back_sell1':
            Inline = types.InlineKeyboardMarkup()
            itemsell1 = types.InlineKeyboardButton(text='🪙Bitcoin', callback_data= 'Bitcoin_sell')
            itemsell2 = types.InlineKeyboardButton(text='💵USDT (Tether ERC-20)', callback_data= 'USDT_sell')
            back = types.InlineKeyboardButton(text='Назад', callback_data = 'Back')
            Inline.add(back,itemsell1,itemsell2)

            #bot.send_message(call.message.chat.id, ' Выберите валюту, которую хотите продать', reply_markup = Inline)
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='❔ Выберите валюту, которую хотите продать')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)


        elif call.data == 'Back_sell2':
            Inline = types.InlineKeyboardMarkup()
            itemsell1 = types.InlineKeyboardButton(text='🪙Bitcoin', callback_data= 'Bitcoin_sell')
            itemsell2 = types.InlineKeyboardButton(text='USDT (Tether ERC-20)', callback_data= 'USDT_sell')
            back = types.InlineKeyboardButton(text='Назад', callback_data = 'Back')
            Inline.add(back,itemsell1,itemsell2)

            #bot.send_message(call.message.chat.id, ' Выберите валюту, которую хотите продать', reply_markup = Inline)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='❔ Выберите валюту, которую хотите продать')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)   

        elif call.data == 'Back_sell3':
            itemsell1 = types.InlineKeyboardButton(text='🪙Bitcoin', callback_data= 'Bitcoin_sell')
            itemsell2 = types.InlineKeyboardButton(text='USDT (Tether ERC-20)', callback_data= 'USDT_sell')
            back = types.InlineKeyboardButton(text='Назад', callback_data = 'Back')
            Inline.add(back,itemsell1,itemsell2)

            #bot.send_message(call.message.chat.id, ' Выберите валюту, которую хотите продать', reply_markup = Inline)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='❔ Выберите валюту, которую хотите продать')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            


        elif call.data == 'Back_buy3':
            Inline = types.InlineKeyboardMarkup()
            itembuy1 = types.InlineKeyboardButton(text = '🪙Bitcoin', callback_data='Bitcoin_buy')
            itembuy2 = types.InlineKeyboardButton(text = '💵USDT (Tether ERC-20)', callback_data='USDT_buy')
            back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
            Inline.add(back,itembuy1,itembuy2)

            #bot.send_message(call.message.chat.id, ' Выберите валюту, которую хотите купить', reply_markup = Inline)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='🔄 Выберите валюту, которую хотите приобрести')
            bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)


        elif call.data == 'btc_buy_yes':
            
            group_id = 'your_group_ID'
            chat_id = call.message.chat.id
            user = user_dict[chat_id] 
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text = '❌Отменить заявку', callback_data= 'Back')
            Approve = types.InlineKeyboardButton(text='✅Перевёл',callback_data='btc_buy_yes_approve')
            Inline.add(Back,Approve)
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id,'✅Заявка успешно создана\n \n 💰Сумма: {} BTC \n 👛Адрес кошелька: {} \n 💰Сумма к оплате: {} ₽ \n \n 💳 Реквизиты для оплаты: \n реквизиты \n \n Время отправки: от 30 до 120 минут\n \n 🕘Заявка действительна 15 минут\n После перевода средств по указанным реквизитам нажмите кнопку «Оплачено» или вы можете отменить заявку, нажав на кнопку «Отменить заявку»\n \n ‼️Важно! Если вы оплатили заявку позже 15 минут, то мы делаем перерасчет по актуальному курсу.'.format(y,q,k),reply_markup= Inline)
            #bot.send_message(group_id, GetReGData(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
            #bot.send_message(group_id,  'Заявка выше от человка с id:@' f'{username}',  parse_mode='Markdown')
            
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)


        elif call.data == 'btc_buy_yes_approve':
            group_id = 'your_group_ID'
            chat_id = call.message.chat.id
            user = user_dict[chat_id] 
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
            Inline.add(Back)

            Start = types.InlineKeyboardMarkup(row_width= 2)
            item1 = types.InlineKeyboardButton(text = '⬇️Купить' , callback_data= 'buy')
            item2 = types.InlineKeyboardButton(text = '⬆️Продать', callback_data='sell') 
            item3 = types.InlineKeyboardButton(text = '💬Чат', url = 'https://t.me/+c2iY0XEkYzlhZGNk')
            item4 = types.InlineKeyboardButton(text = '📢Канал', url= 'https://t.me/candyshop_exchange')
            item5 = types.InlineKeyboardButton(text = '❓Отзывы', url= 'https://t.me/candyshop_exchange_reviews')
            item6 = types.InlineKeyboardButton(text = '👨🏼‍🚀Оператор', url= 'https://t.me/candyshop_exchange_support')
            item7 = types.InlineKeyboardButton(text = '📈Курс', callback_data= 'course')
            #Course = types.InlineKeyboardButton(text= '📈Курс', switch_inline_query_current_chat= '')
            item8 = types.InlineKeyboardButton(text = 'ℹ️Инфо', callback_data= 'info')

 

            Start.add(item1, item2, item3, item4, item5, item6, item7, item8)

 
 
 
            #bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.mesage.id, text= 'Лучший')
            #bot.edit_message_reply_markup(chat_id= call.message.chat.id,message_id= call.message.id, reply_markup= Inline)
            bot.delete_message(call.message.chat.id,call.message.id)
            bot.send_message(call.message.chat.id, '✅Ваша заявка № {} успешно создана! \n \n 💰Сумма: {} BTC \n 💰Сумма к оплате: {} ₽ \n 💳 Реквизиты: \n  реквизиты \n \n ‼️Важно! Если вы отправили неверную сумму, то заявка будет пересчитана!'.format(number,y,k))
            bot.send_message(group_id, GetReGData(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
            bot.send_message(group_id,  'Заявка выше от человка с id:@' f'{username}',  parse_mode='Markdown')
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
            bot.send_message(call.message.chat.id, ' 🍭 CANDYSHOP EXCHANGE \n \n 🔄Купить и продать криптовалюту\n 🔐 Конфиденциально \n 💫 Быстро и удобно \n 🔥 Поддержка клиентов 24/7 \n' , reply_markup = Start)     

        elif call.data == 'btc_buy_no':
             Inline = types.InlineKeyboardMarkup()
             backbuy = types.InlineKeyboardButton(text='Назад', callback_data='Back_buy1')

             Inline.add(backbuy)

            #bot.send_message(call.message.chat.id,'На какую сумму вы хотите купить Bitcoin?', reply_markup= Inline)
             msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=' На какую сумму вы хотите купить Bitcoin? \n (Напишите сумму от 1000 до 200000 RUB) \n 👨🏼‍🚀Если вам необходима большая сумма обмена, напишите нашему оператору: @candyshop_exchange_support ')
             bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
             bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
             bot.register_next_step_handler(msg, buy_btc)

        elif call.data == 'btc_sell_yes':
            group_id = 'your_group_ID'
            chat_id = call.message.chat.id
            user = user_dict2[chat_id] 
            Inline = types.InlineKeyboardMarkup(row_width= 2)
            Back = types.InlineKeyboardButton(text = '❌Отменить заявку', callback_data= 'Back')
            Approve = types.InlineKeyboardButton(text= '✅Оплатил', callback_data= 'btc_sell_yes_approve')
            Address = types.InlineKeyboardButton(text= 'Скопировать адрес кошелька', switch_inline_query_current_chat="адрес кошелька")

            Inline.add(Back,Approve,Address)
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id,'✅Заявка успешно создана\n  💰Отправьте: {} BTC \n 👛На этот адрес:  адрес кошелька \n ‼️Важно! Вам нужно перевести ровно «сумма» «валюта» иначе ваша заявка будет отменена!\n 🕘Заявка действительна 15 минут. \n 💰Сумма к получению: {} ₽ \n 💳Ваши реквизиты: {} \n После перевода средств по указанным реквизитам нажмите кнопку «Оплатил» или вы можете отменить заявку, нажав на кнопку «Отменить заявку» \n ‼️Важно! Если вы оплатили заявку позже 15 минут, то мы делаем перерасчет по актуальному курсу.'.format(g,v,t),reply_markup= Inline)
           # bot.send_message(group_id, GetReGData2(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
            #bot.send_message(group_id,  'Заявка выше от человка с id:@' f'{username}',  parse_mode='Markdown')
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)


        elif call.data == 'btc_sell_yes_approve':
            group_id = 'your_group_ID'
            chat_id = call.message.chat.id
            user = user_dict2[chat_id] 
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
            Inline.add(Back)

            Start = types.InlineKeyboardMarkup(row_width= 2)
            item1 = types.InlineKeyboardButton(text = '⬇️Купить' , callback_data= 'buy')
            item2 = types.InlineKeyboardButton(text = '⬆️Продать', callback_data='sell') 
            item3 = types.InlineKeyboardButton(text = '💬Чат', url = 'https://t.me/+c2iY0XEkYzlhZGNk')
            item4 = types.InlineKeyboardButton(text = '📢Канал', url= 'https://t.me/candyshop_exchange')
            item5 = types.InlineKeyboardButton(text = '❓Отзывы', url= 'https://t.me/candyshop_exchange_reviews')
            item6 = types.InlineKeyboardButton(text = '👨🏼‍🚀Оператор', url= 'https://t.me/candyshop_exchange_support')
            item7 = types.InlineKeyboardButton(text = '📈Курс', callback_data= 'course')
            #Course = types.InlineKeyboardButton(text= '📈Курс', switch_inline_query_current_chat='')
            item8 = types.InlineKeyboardButton(text = 'ℹ️Инфо', callback_data= 'info')

 

            Start.add(item1, item2, item3, item4, item5, item6, item7, item8)

            #bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.mesage.id, text= 'Лучший')
            #bot.edit_message_reply_markup(chat_id= call.message.chat.id,message_id= call.message.id, reply_markup= Inline)
            bot.delete_message(call.message.chat.id,call.message.id)
            bot.send_message(call.message.chat.id, '✅ Ваша заявка № {} успешно создана!\n 💰Сумма продажи: {} BTC \n 💰Сумма к получению: {} ₽\n 💳Ваши реквизиты: {} \n 👛Адрес кошелька: адрес кошелька \n \n 🚀 Время отправки от 30 до 120 минут \n \n ‼️Важно! Если вы отправили неверную сумму, то заявка будет пересчитана!'.format(number,g,v,t))
            bot.send_message(group_id, GetReGData2(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
            bot.send_message(group_id,  'Заявка выше от человка с id:@' f'{username}',  parse_mode='Markdown')
            bot.send_message(call.message.chat.id, ' 🍭 CANDYSHOP EXCHANGE \n \n 🔄Купить и продать криптовалюту\n 🔐 Конфиденциально \n 💫 Быстро и удобно \n 🔥 Поддержка клиентов 24/7 \n' , reply_markup = Start)
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)    
            

        elif call.data == 'btc_sell_no':
             Inline = types.InlineKeyboardMarkup()
             backbuy = types.InlineKeyboardButton(text='Назад', callback_data='Back_sell1')

             Inline.add(backbuy)

            #bot.send_message(call.message.chat.id,'На какую сумму вы хотите купить Bitcoin?', reply_markup= Inline)
             msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=' \n (Напишите сумму от 0.0003 до 0.1 BTC) \n 👨🏼‍🚀Если вам необходима большая сумма обмена, напишите нашему оператору: @candyshop_exchange_support  ')
             bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
             bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
             bot.register_next_step_handler(msg, sell_btc)

        elif call.data == 'usdt_buy_yes':
            group_id = 'your_group_ID'
            chat_id = call.message.chat.id
            user = user_dict3[chat_id] 
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
            Approve = types.InlineKeyboardButton(text='✅Оплатил', callback_data='usdt_buy_yes_approve')
            Inline.add(Back,Approve)
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id,'✅Заявка успешно создана\n \n 💰Сумма: {} USDT \n 👛Адрес кошелька: {} \n \n 💰Сумма к оплате: {} ₽ \n \n  💳 Реквизиты для оплаты: \n реквизиты \n \n Время отправки от 30 до 120 минут \n \n 🕘Заявка действительна 15 минут\n После перевода средств по указанным реквизитам нажмите кнопку «Оплачено» или вы можете отменить заявку, нажав на кнопку «Отменить заявку»\n \n ‼️Важно! Если вы оплатили заявку позже 15 минут, то мы делаем перерасчет по актуальному курсу.'.format(z,f,o),reply_markup= Inline)
            #bot.send_message(group_id, GetReGData3(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
            #bot.send_message(group_id,  'Заявка выше от человка с id:@' f'{username}',  parse_mode='Markdown')
            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)


        elif call.data == 'usdt_buy_yes_approve':
            group_id = 'your_group_ID'
            chat_id = call.message.chat.id
            user = user_dict3[chat_id] 
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text = 'Назад', callback_data= 'Back')
            Inline.add(Back)

            Start = types.InlineKeyboardMarkup(row_width= 2)
            item1 = types.InlineKeyboardButton(text = '⬇️Купить' , callback_data= 'buy')
            item2 = types.InlineKeyboardButton(text = '⬆️Продать', callback_data='sell') 
            item3 = types.InlineKeyboardButton(text = '💬Чат', url = 'https://t.me/+c2iY0XEkYzlhZGNk')
            item4 = types.InlineKeyboardButton(text = '📢Канал', url= 'https://t.me/candyshop_exchange')
            item5 = types.InlineKeyboardButton(text = '❓Отзывы', url= 'https://t.me/candyshop_exchange_reviews')
            item6 = types.InlineKeyboardButton(text = '👨🏼‍🚀Оператор', url= 'https://t.me/candyshop_exchange_support')
            item7 = types.InlineKeyboardButton(text = '📈Курс', callback_data= 'course')
            #Course = types.InlineKeyboardButton(text= '📈Курс', switch_inline_query_current_chat='')
            item8 = types.InlineKeyboardButton(text = 'ℹ️Инфо', callback_data= 'info')

 

            Start.add(item1, item2, item3, item4, item5, item6, item7, item8)
            #bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.mesage.id, text= 'Лучший')
            #bot.edit_message_reply_markup(chat_id= call.message.chat.id,message_id= call.message.id, reply_markup= Inline)
            bot.delete_message(call.message.chat.id,call.message.id)
            bot.send_message(call.message.chat.id, '✅Ваша заявка № {} успешно создана! \n ⚙️Статус: ожидайте получения средств \n 💰Сумма: {} USDT \n 💰Сумма к оплате: {} ₽ \n 💳 Реквизиты: \n  реквизиты \n ‼️Важно! Если вы отправили неверную сумму, то заявка будет пересчитана!'.format(number,z,o))
            bot.send_message(group_id, GetReGData3(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
            bot.send_message(group_id,  'Заявка выше от человка с id:@' f'{username}',  parse_mode='Markdown')
            bot.send_message(call.message.chat.id, ' 🍭 CANDYSHOP EXCHANGE \n \n 🔄Купить и продать криптовалюту\n 🔐 Конфиденциально \n 💫 Быстро и удобно \n 🔥 Поддержка клиентов 24/7 \n' , reply_markup = Start)

            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)     
            

        elif call.data == 'usdt_buy_no':
             Inline = types.InlineKeyboardMarkup()
             backbuy = types.InlineKeyboardButton(text='Назад', callback_data='Back_buy1')

             Inline.add(backbuy)

            #bot.send_message(call.message.chat.id,'На какую сумму вы хотите купить Bitcoin?', reply_markup= Inline)
             msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='На какую сумму вы хотите купить USDT (Tether ERC-20) \n (Напишите сумму от 1000 до 200000 USDT) \n 👨🏼‍🚀Если вам необходима большая сумма обмена, напишите нашему оператору: @candyshop_exchange_support  ')
             bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
             bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
             bot.register_next_step_handler(msg, buy_usdt)


        elif call.data == 'usdt_sell_yes':
            group_id = 'your_group_ID'
            chat_id = call.message.chat.id
            user = user_dict4[chat_id] 
            Inline = types.InlineKeyboardMarkup(row_width= 2)
            Back = types.InlineKeyboardButton(text = '❌Отменить заявку', callback_data= 'Back')
            Approve = types.InlineKeyboardButton(text='✅Оплатил', callback_data= 'usdt_sell_yes_approve')
            Address = types.InlineKeyboardButton(text= 'Скопировать адрес кошелька', switch_inline_query_current_chat="адрес кошелька")

            Inline.add(Back, Approve,Address)
            bot.delete_message(call.message.chat.id, call.message.id)
            bot.send_message(call.message.chat.id,'✅Заявка успешно создана\n  💰Отправьте: {} USDT \n 👛На этот адрес:  адрес кошелька\n ‼️Важно! Вам нужно перевести ровно «сумма» «валюта» иначе ваша заявка будет отменена!\n 🕘Заявка действительна 15 минут. \n 💰Сумма к получению: {} ₽ \n 💳Ваши реквизиты: {} \n После перевода средств по указанным реквизитам нажмите кнопку «Оплатил» или вы можете отменить заявку, нажав на кнопку «Отменить заявку» \n ‼️Важно! Если вы оплатили заявку позже 15 минут, то мы делаем перерасчет по актуальному курсу.'.format(a,c,p),reply_markup=Inline)
            #bot.send_message(group_id, GetReGData4(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
            #bot.send_message(group_id,  'Заявка выше от человка с id:@' f'{username}',  parse_mode='Markdown')
            #bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)

        elif call.data == 'usdt_sell_yes_approve':
            group_id = 'your_group_ID'
            chat_id = call.message.chat.id
            user = user_dict4[chat_id] 
            Inline = types.InlineKeyboardMarkup()
            Back = types.InlineKeyboardButton(text= 'Назад', callback_data= 'Back')
            Address = types.InlineKeyboardButton(text= 'Скопировать адрес кошелька', switch_inline_query_current_chat="адрес кошелька")
            Inline.add(Address)

            Start = types.InlineKeyboardMarkup(row_width= 2)
            item1 = types.InlineKeyboardButton(text = '⬇️Купить' , callback_data= 'buy')
            item2 = types.InlineKeyboardButton(text = '⬆️Продать', callback_data='sell') 
            item3 = types.InlineKeyboardButton(text = '💬Чат', url = 'https://t.me/+c2iY0XEkYzlhZGNk')
            item4 = types.InlineKeyboardButton(text = '📢Канал', url= 'https://t.me/candyshop_exchange')
            item5 = types.InlineKeyboardButton(text = '❓Отзывы', url= 'https://t.me/candyshop_exchange_reviews')
            item6 = types.InlineKeyboardButton(text = '👨🏼‍🚀Оператор', url= 'https://t.me/candyshop_exchange_support')
            item7 = types.InlineKeyboardButton(text = '📈Курс', callback_data= 'course')
            #Course = types.InlineKeyboardButton(text= '📈Курс', switch_inline_query_current_chat='')
            item8 = types.InlineKeyboardButton(text = 'ℹ️Инфо', callback_data= 'info')

 

            Start.add(item1, item2, item3, item4, item5, item6, item7, item8)

            #bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.mesage.id, text= 'Лучший')
            #bot.edit_message_reply_markup(chat_id= call.message.chat.id,message_id= call.message.id, reply_markup= Inline)
            bot.delete_message(call.message.chat.id,call.message.id)
            bot.send_message(call.message.chat.id, '✅ Ваша заявка № {} успешно создана!\n 💰Сумма продажи: {} USDT \n 💰Сумма к получению: {} ₽\n 💳Ваши реквизиты: {} \n 👛Адрес кошелька: адрес кошелька \n \n 🚀Время отправки: от 30 до 120 минут \n \n ‼️Важно! Если вы отправили неверную сумму, то заявка будет пересчитана!'.format(number,a,c,p))
            bot.send_message(group_id, GetReGData4(user, 'Заявка от ', bot.get_me().username), parse_mode= 'Markdown')
            bot.send_message(group_id,  'Заявка выше от человка с id:@' f'{username}',  parse_mode='Markdown')
            bot.send_message(call.message.chat.id, ' 🍭 CANDYSHOP EXCHANGE \n \n 🔄Купить и продать криптовалюту\n 🔐 Конфиденциально \n 💫 Быстро и удобно \n 🔥 Поддержка клиентов 24/7 \n' , reply_markup = Start)

            bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)


            

        elif call.data == 'usdt_sell_no':
             Inline = types.InlineKeyboardMarkup()
             backbuy = types.InlineKeyboardButton(text='Назад', callback_data='Back_sell1')

             Inline.add(backbuy)

            #bot.send_message(call.message.chat.id,'На какую сумму вы хотите купить Bitcoin?', reply_markup= Inline)
             msg = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text='На какую сумму вы хотите продать USDT (Tether ERC-20) \n (Напишите сумму от 10 до 3000 USDT) \n 👨🏼‍🚀Если вам необходима большая сумма обмена, напишите нашему оператору: @candyshop_exchange_support  ')
             bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)
             bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
             bot.register_next_step_handler(msg, sell_usdt)                

                             
        elif call.data == 'Back':
         Inline = types.InlineKeyboardMarkup(row_width= 2)
         item1 = types.InlineKeyboardButton(text = '⬇️Купить' , callback_data= 'buy')
         item2 = types.InlineKeyboardButton(text = '⬆️Продать', callback_data='sell') 
         item3 = types.InlineKeyboardButton(text = '💬Чат', url='https://t.me/+c2iY0XEkYzlhZGNk')
         item4 = types.InlineKeyboardButton(text = '📢Канал', url= 'https://t.me/candyshop_exchange')
         item5 = types.InlineKeyboardButton(text = '❓Отзывы', url= 'https://t.me/candyshop_exchange_reviews')
         item6 = types.InlineKeyboardButton(text = '👨🏼‍🚀Оператор', url= 'https://t.me/candyshop_exchange_support')
         item7 = types.InlineKeyboardButton(text = '📈Курс', callback_data= 'course')
         #Course = types.InlineKeyboardButton(text= '📈Курс', switch_inline_query_current_chat= '')
         item8 = types.InlineKeyboardButton(text = 'ℹ️Инфо', callback_data= 'info')

         Inline.add(item1, item2, item3, item4, item5, item6, item7, item8)

         #bot.send_message(call.message.chat.id, ' Вы вернулись назад', reply_markup = Inline)
         bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
         bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=' 🍭 CANDYSHOP EXCHANGE \n \n 🔄Купить и продать криптовалюту\n 🔐 Конфиденциально \n 💫 Быстро и удобно \n 🔥 Поддержка клиентов 24/7 \n')
         bot.edit_message_reply_markup(chat_id= call.message.chat.id, message_id= call.message.id, reply_markup=Inline)


        

        #elif call.data == '123':
        #def calculator_answer():
                    #global value 
                    #global old_value
        #if value == '':
                    #Calculator_usdt = types.InlineKeyboardMarkup(row_width= 3)
                   # button_1 = types.InlineKeyboardButton(text = '1', callback_data= '1')
                   # button_2 = types.InlineKeyboardButton(text = '2', callback_data= '2')
                    #button_3 = types.InlineKeyboardButton(text = '3', callback_data= '3')
                    #button_4 = types.InlineKeyboardButton(text= '4', callback_data= '4')
                    #button_5 = types.InlineKeyboardButton(text = '5', callback_data= '5')
                    #button_6 = types.InlineKeyboardButton(text= '6', callback_data= '6')
                   # button_7 = types.InlineKeyboardButton(text= '7', callback_data= '7')
                    #button_8 = types.InlineKeyboardButton(text = '8', callback_data= '8')
                    #button_9 = types.InlineKeyboardButton(text = '9', callback_data= '9')
                    #button_10 = types.InlineKeyboardButton(text = '=', callback_data= '=')
                    #button_11 = types.InlineKeyboardButton(text= 'C', callback_data= 'C')
                    #button_12 = types.InlineKeyboardButton(text = '0', callback_data= '0')
                    #button_13 = types.InlineKeyboardButton(text = '.', callback_data= '.')
           
                    #Calculator_usdt.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9, button_13, button_12, button_11, button_10)
                    #bot.send_message(call.message.chat.id, '0', reply_markup= Calculator_usdt)
        #else:
                    #Calculator_usdt = types.InlineKeyboardMarkup(row_width= 3)
                    #button_1 = types.InlineKeyboardButton(text = '1', callback_data= '1')
                    #button_2 = types.InlineKeyboardButton(text = '2', callback_data= '2')
                   # button_3 = types.InlineKeyboardButton(text = '3', callback_data= '3')
                    #button_4 = types.InlineKeyboardButton(text= '4', callback_data= '4')
                   # button_5 = types.InlineKeyboardButton(text = '5', callback_data= '5')
                   # button_6 = types.InlineKeyboardButton(text= '6', callback_data= '6')
                    #button_7 = types.InlineKeyboardButton(text= '7', callback_data= '7')
                    #button_8 = types.InlineKeyboardButton(text = '8', callback_data= '8')
                    #button_9 = types.InlineKeyboardButton(text = '9', callback_data= '9')
                   # button_10 = types.InlineKeyboardButton(text = '=', callback_data= '=')
                   # button_11 = types.InlineKeyboardButton(text= 'C', callback_data= 'C')
                    #button_12 = types.InlineKeyboardButton(text = '0', callback_data= '0')
                    #button_13 = types.InlineKeyboardButton(text = '.', callback_data= '.')
           
                   # Calculator_usdt.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9, button_13, button_12, button_11, button_10)
                   # bot.send_message(call.message.chat.id, value, reply_markup= Calculator_usdt)


        #Calculator_usdt = types.InlineKeyboardMarkup(row_width= 3)
            #global value 
            #global old_value
        #button_1 = types.InlineKeyboardButton(text = '1', callback_data= '1')
        #button_2 = types.InlineKeyboardButton(text = '2', callback_data= '2')
        #button_3 = types.InlineKeyboardButton(text = '3', callback_data= '3')
        #button_4 = types.InlineKeyboardButton(text= '4', callback_data= '4')
        #button_5 = types.InlineKeyboardButton(text = '5', callback_data= '5')
        #button_6 = types.InlineKeyboardButton(text= '6', callback_data= '6')
        #button_7 = types.InlineKeyboardButton(text= '7', callback_data= '7')
        #button_8 = types.InlineKeyboardButton(text = '8', callback_data= '8')
        #button_9 = types.InlineKeyboardButton(text = '9', callback_data= '9')
        #button_10 = types.InlineKeyboardButton(text = '=', callback_data= '=')
        #button_11 = types.InlineKeyboardButton(text= 'C', callback_data= 'C')
        #button_12 = types.InlineKeyboardButton(text = '0', callback_data= '0')
        #button_13 = types.InlineKeyboardButton(text = '.', callback_data= '.')
        #Calculator_usdt.add(button_1, button_2, button_3, button_4, button_5, button_6, button_7, button_8, button_9, button_13, button_12, button_11, button_10)
    
        
        # if call.data== 'C':
        #        value = ''
        # elif call.data == '=':
        #        value = float(value) * 1.1
        #        value = str(value)
            
            
        #else:
               #value += call.data
            

        #if value != old_value:
          # if value == '':
             #  bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.message.id, text= '0', reply_markup= Calculator_usdt)
           #else:
               #bot.edit_message_text(chat_id= call.message.chat.id, message_id= call.message.id, text= value, reply_markup= Calculator_usdt)     
 
        #old_value = value 



     
          

try:
    bot.polling(none_stop=True)
except:
    pass

