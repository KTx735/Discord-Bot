import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
import urllib.parse, urllib.request, re

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('discord_token')
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix="?", intents=intents)
    #client_slash = discord.Client(intents=intents)
    #tree = app_commands.CommandTree(client_slash)

    queue = {}
    voice_clients = {}
    yt_dlp_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dlp_options)
    youtube_base_url = 'https://www.youtube.com/'
    youtube_results_url = youtube_base_url + 'results?'
    youtube_watch_url = youtube_base_url + 'watch?v='

    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn -filter:a "volume=0.25"'}

    @client.event
    async def on_ready():
        print(f'{client.user} is online!')
        print("---------------------------")

    #Queue function
    #If queue not is empty then pop the next song (at position 0)
    #Basically play next song on list
    async def play_next(ctx):
        if queue[ctx.guild.id] != []:
            link = queue[ctx.guild.id].pop(0)
            await play(ctx, link= link)
    
    @client.command(name="play")
    async def play(ctx, *, link):
        try:
            voice_client = await ctx.author.voice.channel.connect() #Connect to VC
            voice_clients[voice_client.guild.id] = voice_client
            await ctx.send("Now Playing" + " " + link)
            # print(ctx.voice_client.is_playing())
            # if ctx.voice_client.is_playing():
            #     await add(ctx, link)
            # else:
            #     voice_clients[voice_client.guild.id] = voice_client
            #     await ctx.send("Now Playing" + " " + link)
                
        except Exception as e:
            print(e)

        try:
            if youtube_base_url not in link:
                query_string = urllib.parse.urlencode({
                    'search_query': link
                })

                content = urllib.request.urlopen(
                    youtube_results_url + query_string
                )

                search_results = re.findall(r'/watch\?v=(.{11})', content.read().decode())

                #Generate Link
                link = youtube_watch_url + search_results[0]
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=False))

            song = data['url']
            player = discord.FFmpegOpusAudio(song, **ffmpeg_options)

            #Play request, if another request on the list then play after
            voice_clients[ctx.guild.id].play(player, after= lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), client.loop))
        except Exception as e:
            print(e)

    @client.command(name="pause")
    async def pause(ctx):
        try:
            voice_clients[ctx.guild.id].pause()
        except Exception as e:
            print(e)
    
    @client.command(name="resume")
    async def resume(ctx):
        try:
            voice_clients[ctx.guild.id].resume()
        except Exception as e:
            print(e)

    @client.command(name="stop")
    async def stop(ctx):
        try:
            voice_clients[ctx.guild.id].stop()
            await voice_clients[ctx.guild.id].disconnect()
            #Safety Net so everytime we play we create a new voice client
            #and we don't keep stacking
            del voice_clients[ctx.guild.id]
        except Exception as e:
            print(e)
    
    #Same function as stop but with new command
    @client.command(name="disconnect")
    async def disconnect(ctx):
        try:
            voice_clients[ctx.guild.id].stop()
            await voice_clients[ctx.guild.id].disconnect()
            #Safety Net so everytime we play we create a new voice client
            #and we don't keep stacking
            del voice_clients[ctx.guild.id]
        except Exception as e:
            print(e)

    @client.command(name="skip")
    async def skip(ctx):
        try:
            voice_clients[ctx.guild.id].stop()
            await play_next(ctx)
            await ctx.send("Skipped Current Track!")
        except Exception as e:
            print(e)

    #Queue
    @client.command(name="add")
    async def add(ctx, *, link):
        if ctx.guild.id not in queue:
            queue[ctx.guild.id] = []
        queue[ctx.guild.id].append(link)
        await ctx.send(link + " " + "is now on the queue!")
        

    @client.command(name="clear_queue")
    async def clear_queue(ctx):
        if ctx.guild.id in queue:
            queue[ctx.guild.id].clear()
            await ctx.send("Queue Cleared!")
        else:
            #Not working?
            await ctx.send("Queue is Empty!")
    
    client.run(TOKEN)
