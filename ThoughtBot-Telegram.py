"""
  ThoughtBot-Telegram

  A bot for the Telegram chat system that allows users to query the THT
  blockchain for information.

  MIT License

  Copyright (c) 2020-2022 Philip A Grim II

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
"""

import configparser
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import Updater
import logging
import requests
from requests.exceptions import HTTPError
import subprocess

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                             level=logging.INFO)

config = configparser.ConfigParser()
config.read_file(open(r'thoughtbot.cfg'))

TELEGRAM_TOKEN=config.get("Telegram", "TOKEN") 

updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher

def _start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="ThoughtBot is listening.")

def _help(update: Update, context: CallbackContext):
    help = """ThoughtBot help:
    /start   - Initialize ThoughtBot
    /diff    - Show current THT network difficulty
    /height  - Show the current height of the THT blockchain
    /mncount - Show the current number of masternodes on the THT blockchain
    /price   - Show current price listings for THT
    """
    context.bot.send_message(chat_id=update.effective_chat.id, text=help)

def _settings(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="ThoughtBot is using default settings.")

def _diff(update: Update, context: CallbackContext): 
    difficulty = subprocess.Popen(["thought-cli", "getdifficulty"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = difficulty.communicate()
    print(output,errors)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Difficulty: {output}")

def _height(update: Update, context: CallbackContext): 
    height = subprocess.Popen(["thought-cli", "getblockcount"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = height.communicate()
    print(output,errors)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Height: {output}")

def _mncount(update: Update, context: CallbackContext): 
    p1 = subprocess.Popen(['thought-cli', 'masternodelist'], stdout=subprocess.PIPE, text=True)
    p2 = subprocess.Popen(['grep', '\"address\"'], stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
    p3 = subprocess.Popen(['wc', '-l'], stdin=p2.stdout, stdout=subprocess.PIPE, text=True)
    output, errors = p3.communicate()
    print(output,errors)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Masternode Count: {output}")

def _price(update: Update, context: CallbackContext): 
    price = 'Unknown'
    try:
        output = "Current Price:\n"
        available = False

        try:
            response = requests.get('https://api.coinmetro.com/exchange/prices')
            response.raise_for_status()
            # access JSOn content
            jsonResponse = response.json()

            prices = jsonResponse['latestPrices']
            for item in prices:
                if item['pair'] == 'THTEUR':
                    eurprice = '{:.6f}'.format(item['price'])
                elif item['pair'] == 'THTUSD':
                    usdprice = '{:.6f}'.format(item['price'])

            output += f' CoinMetro: 1 THT = {eurprice} EUR\n'
            output += f' CoinMetro: 1 THT = {usdprice} USD\n'
            available = True
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            #output += f' CoinMetro: THT-EUR price unavailable\n' # For now, only output if there is a price.

        try:
            response = requests.get('http://api.p2pb2b.io/api/v2/public/ticker?market=THT_ETH')
            response.raise_for_status()
            # access JSOn content
            jsonResponse = response.json()

            result = jsonResponse['result']
            price = result['last']

            output += f'    P2PB2B: 1 THT = {price} ETH\n'
            available = True
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            #output += f'    P2PB2B: THT-ETH price unavailable\n'

        try:
            response = requests.get('http://api.p2pb2b.io/api/v2/public/ticker?market=THT_USD')
            response.raise_for_status()
            # access JSOn content
            jsonResponse = response.json()

            result = jsonResponse['result']
            price = result['last']

            output += f'    P2PB2B: 1 THT = {price} USD'
            available = True
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            #output += f'    P2PB2B: THT-USD price unavailable\n'

        if available == False:
            output += '    No price data available'

        print(output)

        context.bot.send_message(chat_id=update.effective_chat.id, text=f'{output}')

    except Exception as err:
        print(f'Other error occurred: {err}')
        context.bot.send_message(chat_id=update.effective_chat.id, text='Price temporarily unavailable.')



start_handler = CommandHandler('start', _start)
dispatcher.add_handler(start_handler)

help_handler = CommandHandler('help', _help)
dispatcher.add_handler(help_handler)

settings_handler = CommandHandler('settings', _settings)
dispatcher.add_handler(settings_handler)

diff_handler = CommandHandler('diff', _diff)
dispatcher.add_handler(diff_handler)

height_handler = CommandHandler('height', _height)
dispatcher.add_handler(height_handler)

mncount_handler = CommandHandler('mncount', _mncount)
dispatcher.add_handler(mncount_handler)

price_handler = CommandHandler('price', _price)
dispatcher.add_handler(price_handler)

updater.start_polling()
