"""
  ThoughtBot-Discord

  A bot for the Discord chat system that allows users to query the THT
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
import discord
from discord_slash import SlashCommand # Importing the newly installed library.
import requests
from requests.exceptions import HTTPError
import subprocess

config = configparser.ConfigParser()
config.read_file(open(r'thoughtbot.cfg'))

DISCORD_TOKEN=config.get("Discord", "TOKEN") 
DISCORD_GUILD=int(config.get("Discord", "GUILD"))

client = discord.Client(intents=discord.Intents.all())
slash = SlashCommand(client, sync_commands=True) # Declares slash commands through the client.

@client.event
async def on_ready():
        print("Ready!")

guild_ids = [DISCORD_GUILD] 

@slash.slash(name="diff", description='Get current chain difficulty', guild_ids=guild_ids)
async def _diff(ctx): 
    difficulty = subprocess.Popen(["thought-cli", "getdifficulty"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = difficulty.communicate()
    print(output,errors)
    await ctx.send(f"Difficulty: {output}")

@slash.slash(name="height", description='Get current chain height', guild_ids=guild_ids)
async def _height(ctx): 
    height = subprocess.Popen(["thought-cli", "getblockcount"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = height.communicate()
    print(output,errors)
    await ctx.send(f"Height: {output}")

@slash.slash(name="mncount", description='Get the current number of masternodes', guild_ids=guild_ids)
async def _mncount(ctx): 
    p1 = subprocess.Popen(['thought-cli', 'masternodelist'], stdout=subprocess.PIPE, text=True)
    p2 = subprocess.Popen(['grep', '\"address\"'], stdin=p1.stdout, stdout=subprocess.PIPE, text=True)
    p3 = subprocess.Popen(['wc', '-l'], stdin=p2.stdout, stdout=subprocess.PIPE, text=True)
    output, errors = p3.communicate()
    print(output,errors)

    await ctx.send(f"Masternode Count: {output}")

@slash.slash(name="price", description='Get current exchange prices for THT', guild_ids=guild_ids)
async def _price(ctx): 
    price = 'Unknown'
    try:
        await ctx.defer()
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
            #output += f' CoinMetro: THT-EUR price unavailable\n'

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

            output += f'    P2PB2B: 1 THT = {price} USD\n'
            available = True
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
            #output += f'    P2PB2B: THT-USD price unavailable\n'

        if available == False:
            output += '    No price data available'

        print(output)
        await ctx.send(f'```{output}```')

    except Exception as err:
        print(f'Other error occurred: {err}')
        await ctx.send(f'Price temporarily unavailable')


client.run(DISCORD_TOKEN)
