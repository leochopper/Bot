import discord
import os
import asyncio
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
from discord.errors import NotFound
from flask import Flask
from threading import Thread

# Configuración inicial
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True  # Necesario para manejar menciones

bot = commands.Bot(command_prefix="!", intents=intents)

# Configuración para 10 sistemas independientes
sistemas_pruebas = {
    i: {
        'entrenador_online': None,
        'participantes': [],
        'prueba_en_curso': False,
        'mensaje_prueba': None,
        'canal_prueba_id': None,
        'timeout_task': None
    } for i in range(1, 11)  # Sistemas del 1 al 10
}

class PruebaView(View):
    def __init__(self, sistema_id):
        super().__init__(timeout=None)
        self.sistema_id = sistema_id

    @discord.ui.button(label="Unirse a la cola",
                      style=discord.ButtonStyle.green,
                      custom_id="unirse_cola")
    async def unirse_cola(self, interaction: discord.Interaction, button: Button):
        sistema = sistemas_pruebas[self.sistema_id]
        if interaction.user not in sistema['participantes']:
            sistema['participantes'].append(interaction.user)
            await actualizar_mensaje_prueba(self.sistema_id)
            await interaction.response.send_message("¡Te has unido a la cola!", ephemeral=True)
        else:
            await interaction.response.send_message("Ya estás en la cola.", ephemeral=True)

async def actualizar_mensaje_prueba(sistema_id):
    sistema = sistemas_pruebas[sistema_id]
    if not sistema['canal_prueba_id']:
        return

    canal = bot.get_channel(sistema['canal_prueba_id'])
    if not canal:
        return

    embed = discord.Embed(title=f"Sistema de Pruebas de Ascenso #{sistema_id}")
    view = PruebaView(sistema_id) if (sistema['entrenador_online'] is not None and not sistema['prueba_en_curso']) else None

    if sistema['entrenador_online']:
        embed.color = discord.Color.green()
        embed.description = f"Prueba abierta ✳️\n{sistema['entrenador_online'].mention} está online"
        if sistema['participantes']:
            embed.add_field(name="Participantes",
                          value="\n".join([user.mention for user in sistema['participantes']]),
                          inline=False)
    else:
        embed.color = discord.Color.red()
        embed.description = "Prueba cerrada 🔴\nNo hay entrenadores online"
        embed.set_footer(text=f"Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    try:
        if sistema['mensaje_prueba']:
            await sistema['mensaje_prueba'].edit(embed=embed, view=view)
        else:
            sistema['mensaje_prueba'] = await canal.send(embed=embed, view=view)
    except (NotFound, AttributeError):
        sistema['mensaje_prueba'] = await canal.send(embed=embed, view=view)

async def timeout_entrenador(sistema_id, author):
    await asyncio.sleep(7200)  # 2 horas = 7200 segundos
    sistema = sistemas_pruebas[sistema_id]
    if sistema['entrenador_online'] == author:
        sistema['entrenador_online'] = None
        sistema['participantes'] = []
        await actualizar_mensaje_prueba(sistema_id)

def get_sistema_id(ctx):
    command_name = ctx.invoked_with.lower()
    if command_name[-1].isdigit():
        return int(command_name[-1])
    return 1  # Default al sistema 1

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user.name}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="!help"))

# Comandos del sistema
@bot.command(name='set_here', aliases=[f'set_here{i}' for i in range(1, 11)])
@commands.has_role("Entrenador")
async def set_here(ctx):
    sistema_id = get_sistema_id(ctx)
    sistemas_pruebas[sistema_id]['canal_prueba_id'] = ctx.channel.id
    sistemas_pruebas[sistema_id]['mensaje_prueba'] = None
    await actualizar_mensaje_prueba(sistema_id)
    await ctx.send(f"✅ Canal de pruebas #{sistema_id} configurado aquí.", delete_after=5)

@bot.command(name='online', aliases=[f'online{i}' for i in range(1, 11)])
@commands.has_role("Entrenador")
async def online(ctx):
    sistema_id = get_sistema_id(ctx)
    sistema = sistemas_pruebas[sistema_id]
    
    if sistema['entrenador_online']:
        await ctx.send("⚠️ Ya hay un entrenador online en este sistema.", delete_after=5)
        return
        
    sistema['entrenador_online'] = ctx.author
    sistema['prueba_en_curso'] = False
    
    # Cancelar timeout anterior si existe
    if sistema['timeout_task']:
        sistema['timeout_task'].cancel()
    
    # Configurar nuevo timeout
    sistema['timeout_task'] = bot.loop.create_task(timeout_entrenador(sistema_id, ctx.author))
    
    await actualizar_mensaje_prueba(sistema_id)
    await ctx.send(f"🟢 Modo entrenador activado en sistema #{sistema_id}.", delete_after=5)

@bot.command(name='offline', aliases=[f'offline{i}' for i in range(1, 11)])
@commands.has_role("Entrenador")
async def offline(ctx):
    sistema_id = get_sistema_id(ctx)
    sistema = sistemas_pruebas[sistema_id]
    
    if sistema['timeout_task']:
        sistema['timeout_task'].cancel()
        sistema['timeout_task'] = None
    
    sistema['entrenador_online'] = None
    sistema['participantes'] = []
    sistema['prueba_en_curso'] = False
    await actualizar_mensaje_prueba(sistema_id)
    await ctx.send(f"🔴 Modo entrenador desactivado en sistema #{sistema_id}.", delete_after=5)

@bot.command(name='iniciar', aliases=[f'iniciar{i}' for i in range(1, 11)])
@commands.has_role("Entrenador")
async def iniciar(ctx):
    sistema_id = get_sistema_id(ctx)
    sistema = sistemas_pruebas[sistema_id]
    
    sistema['prueba_en_curso'] = True
    await actualizar_mensaje_prueba(sistema_id)
    await ctx.send(f"🟢 Prueba iniciada en sistema #{sistema_id}. Los participantes no pueden unirse ahora.", delete_after=5)

@bot.command(name='finalizar', aliases=[f'finalizar{i}' for i in range(1, 11)])
@commands.has_role("Entrenador")
async def finalizar(ctx):
    sistema_id = get_sistema_id(ctx)
    sistema = sistemas_pruebas[sistema_id]
    
    sistema['prueba_en_curso'] = False
    sistema['participantes'] = []
    await actualizar_mensaje_prueba(sistema_id)
    await ctx.send(f"🔴 Prueba finalizada en sistema #{sistema_id}. Se reinició la cola.", delete_after=5)

@bot.command(name='fix_msg', aliases=[f'fix_msg{i}' for i in range(1, 11)])
@commands.has_role("Entrenador")
async def fix_msg(ctx):
    sistema_id = get_sistema_id(ctx)
    sistemas_pruebas[sistema_id]['mensaje_prueba'] = None
    await actualizar_mensaje_prueba(sistema_id)
    await ctx.send(f"✅ Mensaje recreado manualmente en sistema #{sistema_id}.", delete_after=5)

# Configuración del servidor Flask para mantener vivo el bot
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot de pruebas de ascenso en línea"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# Iniciar el bot
if __name__ == '__main__':
    bot_token = os.getenv('TOKEN')
    if not bot_token:
        raise ValueError("No se encontró el token de Discord. Configura la variable de entorno TOKEN.")
    bot.run(bot_token)