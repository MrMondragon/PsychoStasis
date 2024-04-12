import requests
import discord
from discord.ext import commands
  
intents = discord.Intents.all()
  
TOKEN = 'MTEzMzc0NjQyMTgxNjg5MzQ5MA.GbkE9s.s54rE0PMUsFMEKQh5y6pAFRPsrBbyUdIL4WpSs'
CHANNEL_ID = 1133463456234881096
bot = commands.Bot(command_prefix="\\", intents=intents)
client = discord.Client(intents=intents)

@bot.event
async def on_ready():
  print(f'{bot.user} has awakened')
  channel = bot.get_channel(CHANNEL_ID)
  
  await channel.send(f'{bot.user} has awakened')
  
app_url=''  

@bot.command()
async def connect(ctx, url):
  global app_url  # Use the global keyword to modify the global app_url variable
  app_url = url
  await ctx.send(f'Connected to {app_url}')
  
@bot.command()
async def list_core(ctx):
  if(app_url is None):
    await ctx.send('Not Connected to server. Call \\connect')
  else:    
    result = GetModelList(app_url, True)
    await ctx.send(f'Models available on server: {result}')
  
@bot.command()
async def core_names(ctx):
  if(app_url is None):
    await ctx.send('Not Connected to server. Call \\connect')
  else:    
    result = get_modelNames(app_url, True)
    await ctx.send(f'Models available on server: {result}')
    

def GetModelList(address, core=True):
    url = f"{address}/model_list"
    params = {'core': 'true' if core else 'false'}

    try:
        response = requests.get(url, params=params)
        print(f"Request URL: {response.url}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        response.raise_for_status()  # Raise an exception if the request was not successful (status code >= 400)
        models = response.json()
        return models
    except requests.exceptions.RequestException as e:
        # Handle request exceptions here (e.g., connection error, timeout, etc.)
        print(f"Error calling remote GetModelList service: {e}")
        return None
  

def get_modelNames(address, core=True):
    url = f"{address}/modelNames"
    params = {'core': 'true' if core else 'false'}

    try:
        response = requests.get(url, params=params)
        print(f"Request URL: {response.url}")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        response.raise_for_status()  # Raise an exception if the request was not successful (status code >= 400)
        models = response.json()
        return models
    except requests.exceptions.RequestException as e:
        # Handle request exceptions here (e.g., connection error, timeout, etc.)
        print(f"Error calling remote get_modelNames service: {e}")
        return None  
  
# @bot.event
# async def on_message(message):
#   if(message.author == bot.user) or (message.content.startswith('\\')):
#     return
#   await message.channel.send(f"You were heard. You said: '{message.content}'")
#   elif(message.content.startswith('/')):
#     #parse commands
#     pass
#   elif(message.content.startswith('@@')):
#     #@ Proxy
#     pass
#   elif(message.content.startswith('@#')):
#     #@ Collective
#     pass
  
  
bot.run(TOKEN)