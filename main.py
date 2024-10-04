import discord
import json
import psutil
import asyncio
import math
import platform
from discord.ext import commands
from datetime import datetime

intents = discord.Intents.default()
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

bot = commands.Bot(command_prefix='!', intents=intents)
status_message = None

def get_system_metrics():
    cpu_percent = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net_io = psutil.net_io_counters()
    system_info = platform.uname()
    
    return {
        "cpu_percent": cpu_percent,
        "ram_percent": ram.percent,
        "total_ram": math.ceil(ram.total / (1024**3)),
        "used_ram": math.ceil(ram.used / (1024**3)),
        "total_disk": math.ceil(disk.total / (1024**3)),
        "used_disk": math.ceil(disk.used / (1024**3)),
        "free_disk": math.ceil(disk.free / (1024**3)),
        "network_inbound": math.ceil(net_io.bytes_recv / (1024**2)),
        "network_outbound": math.ceil(net_io.bytes_sent / (1024**2)),
        "server_ping": math.ceil(bot.latency * 1000),
        "system_cores": psutil.cpu_count(logical=False),
        "system_info": f"{system_info.system} {system_info.release}"
    }

def create_embed(metrics, uptime_string, server_name, node_count, server_count, member_count):
    embed = discord.Embed(title="Serverstatus", color=discord.Color.blue())
    embed.add_field(name=":desktop: CPU-Auslastung", value=f"{metrics['cpu_percent']:.1f}%", inline=True)
    embed.add_field(name=":computer: RAM-Auslastung", value=f"{metrics['ram_percent']:.1f}%", inline=True)
    embed.add_field(name=":bar_chart: Gesamter RAM", value=f"{metrics['total_ram']} GB", inline=True)
    embed.add_field(name=":floppy_disk: Verwendeter RAM", value=f"{metrics['used_ram']} GB", inline=True)
    embed.add_field(name=":cd: Gesamter Speicherplatz", value=f"{metrics['total_disk']} GB", inline=True)
    embed.add_field(name=":cd: Verwendeter Speicherplatz", value=f"{metrics['used_disk']} GB", inline=True)
    embed.add_field(name=":cd: Verbleibender Speicherplatz", value=f"{metrics['free_disk']} GB", inline=True)
    embed.add_field(name=":arrow_down: Network (Inbound)", value=f"{metrics['network_inbound']} MB", inline=True)
    embed.add_field(name=":arrow_up: Network (Outbound)", value=f"{metrics['network_outbound']} MB", inline=True)
    embed.add_field(name=":ping_pong: Server-Ping", value=f"{metrics['server_ping']} ms", inline=True)
    embed.add_field(name=":gear: Kerne", value=f"{metrics['system_cores']}", inline=True)
    embed.add_field(name=":desktop: Betriebssystem", value=metrics['system_info'], inline=False)
    embed.add_field(name=":satellite: Nodes", value=f"{node_count}", inline=True)
    embed.add_field(name=":shield: Server", value=f"{server_count}", inline=True)
    embed.add_field(name=":busts_in_silhouette: Mitglieder", value=f"{member_count}", inline=True)
    embed.add_field(name=":blue_book: Server Name", value=f"{server_name}", inline=True)
    embed.add_field(name=":clock3: Uptime", value=uptime_string, inline=False)
    return embed

async def update_status():
    global status_message
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            metrics = get_system_metrics()
            node_count = server_count = len(bot.guilds)
            member_count = sum(guild.member_count for guild in bot.guilds)
            server_id = config["server_id"]
            server_name = bot.get_guild(server_id).name

            uptime = datetime.utcnow() - bot.start_time
            uptime_string = str(timedelta(seconds=int(uptime.total_seconds())))

            embed = create_embed(metrics, uptime_string, server_name, node_count, server_count, member_count)
            channel_id = config["channel"]
            channel = bot.get_channel(channel_id)

            if channel is not None:
                if status_message:
                    await status_message.delete()
                status_message = await channel.send(embed=embed)
            else:
                print(f"Fehler: Kanal mit ID {channel_id} wurde nicht gefunden oder der Bot hat keine Berechtigung, Nachrichten zu senden.")
        except Exception as e:
            print(f"Fehler beim Aktualisieren des Status: {e}")
        await asyncio.sleep(50)

@bot.event
async def on_ready():
    print(f'Bot ist eingeloggt als {bot.user.name}')
    bot.start_time = datetime.utcnow()
    bot.loop.create_task(update_status())

bot.run(config['token'])
