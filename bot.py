from client import client as client
import os
from os import listdir
from os.path import isfile, join
import youtube_dl
import discord
from discord import opus
from helper import *
#from musicplayer  import *
import asyncio
import utility

#Documentation used: https://discordpy.readthedocs.io/en/async/api.html

#Token is stored in Heroku environment to avoid 
#the vulnerability of private Discord bot key exposed to public
TOKEN = os.environ["TOKEN"]

control_panel = None
voice_channels = {}
message_to_channel = {}
mm_reaction_emoji_1 = '🔼'
mm_reaction_emoji_2 = '🔵'
mm_reaction_channel_name = 'mass-move-reactions'
server_name = 'execute'
main_server = None

@client.event
async def on_ready():
    #client.loop.create_task(bg())
    
    await start_mass_move_reactions()
    print(client.user.name)
    print("**********THE BOT IS READY**********")

######################################## MASS_MOVE FUNCTIONS ############################################
######################################## MASS_MOVE FUNCTIONS ############################################

async def start_mass_move_reactions():
    '''Init mass move'''
    global control_panel
    global voice_channels
    global main_server
    
    exe = None
    async for server in client.fetch_guilds():
        if server_name in server.name.lower():
            exe = server
            main_server = server
            break
    if not exe:
        error(f"{server_name} not found in function 'start_mass_move_reactions'")
        return
   
    channels = await exe.fetch_channels()
    for channel in channels:
        if type(channel) is discord.channel.VoiceChannel:
            voice_channels[channel.name] = channel
        elif type(channel) is discord.channel.TextChannel and mm_reaction_channel_name in channel.name:
            control_panel = channel
            
    if not control_panel:
        error("Control Channel not found in function 'start_mass_move_reactions'")
        return
		
    await control_panel.purge(limit=100)
    #await client.send_message(control_panel, channel_sep)
    for channel in sorted(voice_channels.keys(), key = lambda channel_name: voice_channels[channel_name].position):
        name = "**"+channel+"**"
        message = await control_panel.send(embed = discord.Embed(title = name))
        await message.add_reaction( mm_reaction_emoji_1)
        await message.add_reaction( mm_reaction_emoji_2)
        message_to_channel[message.id] = voice_channels[channel].id
        #await client.send_message(control_panel, channel_sep)
    await control_panel.send( f"**Click the {mm_reaction_emoji_1} emoji underneath the channel you wish to move everyone from. Then click the {mm_reaction_emoji_2} emoji underneath the channel you wish to move everyone to.**")
   
@client.command(pass_context=True)
async def rr(ctx):
    if(permission_to_move(ctx.message.author)):
        await start_mass_move_reactions()
    
@client.command(pass_context = True)
async def mg(ctx, game, chname):
    ''' "Move game": Moves everyone playing "game" to channel with chname in channel name '''
    author = ctx.message.author
    server = author.guild
    all_members = server.members
    if permission_to_move(author):
        move_channel = get_channel(server, chname)
        #Moves all people to specified channel if they have game in their currently playing game
        for member in all_members:
            if(member.voice != None and member.voice.channel and not member.voice.afk and game.lower() in str(member.game).lower()):
                await member.move_to(move_channel)
        await ctx.send(f"Mass moved everyone playing { game } to {str(move_channel)}")
    else:
        await ctx.send(f"Sorry you don't have permissions for that, {ctx.author.mention}")
        
@client.command(pass_context=True)
async def mah(ctx) -> None:
    ''' "Move-All-Here" : Moves everyone to your current voice channel '''
    author = ctx.message.author
    server = author.guild
    all_members = server.members
    channels = server.channels
    if permission_to_move(author):
        if author.voice:
            move_channel = author.voice.channel
        else:
            await ctx.send(f"You have to be in a Voice Channel to use this command, {ctx.author.mention}")
            return
        #Moves all people to author's channel
        for member in all_members:
            if(member.voice and not member.voice.afk and member != author):
                await member.move_to(move_channel)
        await ctx.send(f"Mass moved everyone to {str(move_channel)}")
        await ctx.message.delete()
    else:
        await ctx.send(f"Sorry you don't have permissions for that, {ctx.author.mention}")
        
@client.command(pass_context=True)
async def mcc(ctx, chname1 : str, chname2 : str, *arg) -> None:
    ''' "Move-Channel-to-Channel" : .mcc (CHANNEL 1) (CHANNEL 2) [roles to move] -  Moves everyone from Channel 1 to Channel 2. If roles are included, only users with the specified roles will be moved '''
    if permission_to_move(ctx.message.author):
        server = ctx.message.guild
        ch1 = get_channel(server, chname1)
        ch2 = get_channel(server, chname2)
        if arg == ():
            if(ch1 == None and ch2 != None):
                await ctx.send(f"Sorry, '{chname1}' could not be found.")
            elif(ch2 == None and ch1 != None):
                await ctx.send(f"Sorry, '{chname2}' could not be found.")
            elif(ch2 == None and ch1 == None):
                await ctx.send(f"Sorry, both '{chname1}' and  '{chname2}' could not be found.")
            else:
                lst = [member.move_to(ch2) for member in ch1.members]
                await asyncio.gather(*lst)
        else:
            for role in arg:
                await mbr_helper(server, role, ch1, ch2)
    else:
        await ctx.send(f"Sorry you don't have permissions for that, {ctx.author.mention}")
    #await ctx.message.delete()
    
@client.command(pass_context=True)
async def mbr(ctx, role : str, chname : str) -> None:
    ''' "Move-By-Role" : .mbr (ROLE_NAME) (CHANNEL x) -  Moves everyone from with ROLE_NAME in one of their roles to CHANNEL x '''
    if permission_to_move(ctx.message.author):
        server = ctx.message.guild
        ch = get_channel(server, chname)
        got_role = get_role(server, role)
        all_members = server.members
                
        if(ch == None and got_role == None):
            await ctx.send(f"Sorry, both '{chname}' and '{role}' could not be found.")
        elif(ch == None):
            await ctx.send(f"Sorry, '{chname}' could not be found.")
        elif(got_role == None):
            await ctx.send(f"Sorry, '{role}' could not be found.")
        for member in all_members:
            if(member.voice != None and member.voice.channel != ch and not member.voice.afk):
                for rolee in member.roles:
                    if rolee == got_role:
                        await member.move_to(ch)
                        #await ctx.send("Moved Member: " + member.name + " with role " + got_role.name + " to channel " + ch.name)
    else:
        await ctx.send(f"Sorry you don't have permissions for that, {ctx.author.mention}")
    await ctx.message.delete()

######################################## END OF MASS_MOVE FUNCTIONS ############################################
######################################## END OF MASS_MOVE FUNCTIONS ############################################        

@client.event
async def on_reaction_add(reaction, user):
    if user != client.user:
        if(permission_to_move(user) and reaction.message.channel == control_panel and reaction.emoji == mm_reaction_emoji_1 and reaction.message.id in message_to_channel):
            global voice_channels
            #ch1 = voice_channels[reaction.message.embeds[0].title.strip('*')]
            ch1 = client.get_channel(message_to_channel[reaction.message.id])
            
            def check(r,u):
                return r.emoji == mm_reaction_emoji_2 and u == user and r.message.id in message_to_channel
                
            next_reaction, _ = await client.wait_for('reaction_add', check = check)
            #ch2 = voice_channels[next_reaction.message.embeds[0].title.strip('*')]
            ch2 = client.get_channel(message_to_channel[next_reaction.message.id])
            
            lst = [member.move_to(ch2) for member in ch1.members]
            # for member in ch1.members:
                # await member.move_to(ch2)
            print("{}/{} moved everyone from {} to {}".format(user.display_name, user.name, ch1.name, ch2.name))
            await reaction.message.remove_reaction(mm_reaction_emoji_1, user)
            await next_reaction.message.remove_reaction(mm_reaction_emoji_2, user)
            await asyncio.gather(*lst)
            



@client.command(pass_context=True)
async def leave(ctx):
    if permission_to_move(ctx.message.author) and ctx.message.guild.voice_client:
        await ctx.message.guild.voice_client.disconnect(force = True)

#https://discordpy.readthedocs.io/en/latest/faq.html#how-do-i-pass-a-coroutine-to-the-player-s-after-function
def dc_bot(error):
    try:
        fut = asyncio.run_coroutine_threadsafe(main_server.voice_client.disconnect(), client.loop)
        fut.result()
    except Exception as e:
        print(e)

@client.command(pass_context=True)
async def lib(ctx, url):
    url = url.lower()
    mypath = "./"
    sounds = [f[1:-4] for f in listdir(mypath) if isfile(join(mypath, f)) and f[-3:] == "mp3"]
    
    if url in sounds:
        channel = ctx.message.author.voice.channel
        server = ctx.message.guild
        mp3_file = f'Ω{url}.mp3'
        if server.voice_client == None:
            await channel.connect()
        audio_source = discord.FFmpegPCMAudio(mp3_file)
        server.voice_client.play(audio_source)
        
    elif url == "list":
        await ctx.send(f"MP3 Name List: {', '.join(sounds)}")
    else:
        await ctx.send(f"Sorry {ctx.author.mention}, I couldn't find the MP3 file called '{url}'.")

#Run bot
#client.add_cog(Music(client))
client.run(TOKEN)