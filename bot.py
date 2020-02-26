import discord
import boto3
import time
import subprocess as sp
from mcstatus import MinecraftServer

print('Loading...')
with open('config.txt') as f:
   line = f.readline()
   while line:
      exec(line) # we trust the file, so this is ok
      line = f.readline()
print('Loaded config! Connecting to Discord...')
client = discord.Client()
print('Connected to Discord! Setting up AWS...')
aws = boto3.client('ec2')
print('Done!')

wait_until = 0 # timestamp for waiting

async def getPlayers():
    r = []
    try:
        server = MinecraftServer("minecraft.<website>.com", 25565)
        status = server.status()
        r = [p.name for p in status.players.sample]
    except:
        r = ["Error! Couldn't connect to server."]
    return r

async def doMinecraft(param):
    status = ''
    r = -1
    try:
        r = sp.call(['./doMinecraft.sh', param])
    except:
        return 'Failed! (Code SHELL ERROR)'
    if r == 0:
       status = "Ran start command! (does nothing if server not booted)"
    else:
       status = 'Failed! (Code ' + str(r) + ')'
    return status

async def startServer():
    try:
        response = aws.start_instances(InstanceIds=[INSTANCE_ID])
        return response['StartingInstances'][0]['CurrentState']['Name']
    except:
        return 'BORKED!'

async def stopServer():
    try:
        response = aws.stop_instances(InstanceIds=[INSTANCE_ID])
        return response['StoppingInstances'][0]['CurrentState']['Name']
    except:
        return 'BORKED!'

async def rebootServer():
    try:
        response = aws.reboot_instances(InstanceIds=[INSTANCE_ID])
        return 'rebooting'
    except:
        return 'BORKED!'

async def getStatus():
    try:
        response = aws.describe_instances(InstanceIds=[INSTANCE_ID])
        return response['Reservations'][0]['Instances'][0]['State']['Name']
    except:
        return 'BORKED!'

async def do_thing(message):
    global wait_until
    command = message.content.lower().split('.')

    if command[0] != 'mc':
        return

    act = command[1].split(' ')
    param = ''
    if len(act) > 1:
        param = act[1]
    act = act[0]
    print('Processing ' + act + ' from ' + str(message.author))
    t = int(time.time())
    if t < wait_until:
        msg = '[WARN] ' + str(message.author.mention) + ' Please wait for a moment between commands.'
        await message.channel.send(msg)
        return

    wait_until = t + WAITTIME

    if (str(message.author) not in WHITELIST) and act not in FREE_COMMANDS:
        msg = 'Sorry, ' + str(message.author.mention) + ". You're not on the bot whitelist!\n"
        msg += 'Contact Ban for more information.'
        await message.channel.send(msg)
        return
    if len(command) < 2:
        return

    if act == 'help':
        msg = '[INFO] Commands are:\n'
        msg += 'mc.hello: test the bot\n'
        msg += 'mc.whitelist: display whitelisted users\n'
        msg += 'mc.boot: try to boot up the host computer\n'
        msg += 'mc.halt: try to shut down the host computer\n'
        msg += 'mc.reboot: try to reboot the host computer\n'
        msg += 'mc.status: try to get the host computer status\n'
        msg += 'mc.start [Vanilla|Modded]: start the specified Minecraft server program\n'
        msg += 'mc.stop: stop the Minecraft server program\n'
        msg += 'mc.list: list currently online players\n'

        msg += '\nTroubleshooting:\n'
        msg += 'If host enters BORKED state, wait a few moments and check the status. Certain operations can only be performed from specific states.\n'
        msg += "For example, you can't reboot if the server is stopped.\n"
        msg += "Only one Minecraft server can run at once (Modded or Vanilla), and it will take a few minutes to start.\n"

        msg += '\nTo connect to the server:\n'
        msg += 'Make sure mc.boot and mc.start Vanilla have both been run successfully. (Or Modded, if desired)\n'
        msg += 'Then, connect to minecraft.bengillett.com\n'
        msg += "The server doesn't use a whitelist.\n"

        msg += '\nWhen finished:\n'
        msg += 'Plese remember to shut down the host computer! It saves everyone money.\n'
        msg += "Run mc.stop to save and exit the Minecraft server, wait a few seconds, and then run mc.halt to shut down the machine.\n"

        msg += '\nThanks for using MinecraftBot!'

        await message.channel.send(msg)

    elif act == 'hello':
        msg = '[INFO] ' + 'Hello World, ' + str(message.author.mention) + '!'
        await message.channel.send(msg)

    elif act == 'whitelist':
        msg = '[INFO] ' + 'Here are the people authorized to use this bot:\n'
        for p in WHITELIST:
            msg += p + '\n'
        msg += "\nIf you'd like to be addded, please contact Ban."
        await message.channel.send(msg)

    elif act == 'boot':
        msg = '[INFO] Attempting to boot...'
        await message.channel.send(msg)
        status = await startServer()
        msg = '[INFO] Status: ' + status
        await message.channel.send(msg)

    elif act == 'halt':
        msg = '[INFO] Attempting to halt...'
        await message.channel.send(msg)
        status = await stopServer()
        msg = '[INFO] Status: ' + status
        await message.channel.send(msg)

    elif act == 'reboot':
        msg = '[INFO] Attempting to reboot...'
        await message.channel.send(msg)
        status = await rebootServer()
        msg = '[INFO] Status: ' + status
        await message.channel.send(msg)

    elif act == 'status':
        msg = '[INFO] Querying status...'
        await message.channel.send(msg)
        status = await getStatus()
        msg = '[INFO] Status: ' + status
        await message.channel.send(msg)

    elif act == 'start':
        attempt = False
        if param == 'vanilla' or param == 'modded':
            attempt = True
            msg = '[INFO] Starting ' + param + ' Minecraft!'
        else:
            msg = "[WARN] '" + param + "' not a valid option! Try 'mc.start Vanilla' or 'mc.start Modded'"
        await message.channel.send(msg)
        if attempt:
            status = await doMinecraft(param)
            msg = '[INFO] Minecraft Status: ' + status
            await message.channel.send(msg)

    elif act == 'stop':
        msg = '[INFO] Stopping Minecraft!'
        await message.channel.send(msg)
        status = await doMinecraft('stop')
        msg = '[INFO] Minecraft Status: ' + status
        await message.channel.send(msg)

    elif act == 'list':
        msg = '[INFO] Querying Server...'
        await message.channel.send(msg)
        players = await getPlayers()
        msg = '[INFO] Online Players: '
        for p in players[:-1]:
            msg += p + ', '
        msg += players[-1]
        await message.channel.send(msg)

    else:
        msg = '[ERROR] Unknown command: ' + act
        await message.channel.send(msg)
        msg = "[INFO] Use 'mc.help' for help"
        await message.channel.send(msg)

@client.event
async def on_message(message):
    # we do not want the bot to reply to itself
    if message.author == client.user:
        return
    # only interact with messages in minecraftbot channel
    if str(message.channel) == CHANNEL:
        await do_thing(message)

@client.event
async def on_ready():
    #print('Logged in as')
    #print(client.user.name)
    #print(client.user.id)
    print('Running!')

client.run(TOKEN)
