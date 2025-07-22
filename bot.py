import discord
import os
import asyncio
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timezone
from discord.errors import NotFound

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

pruebas = {}

class Prueba:
    def __init__(self):
        self.entrenador_online = None
        self.participantes = []
        self.prueba_en_curso = False
        self.mensaje_prueba = None
        self.canal_prueba_id = None
        self.ultima_sesion = None

class PruebaView(View):
    def __init__(self, prueba_id):
        super().__init__(timeout=None)
        self.prueba_id = prueba_id

    @discord.ui.button(label="Unirse", style=discord.ButtonStyle.green, custom_id="unirse_cola")
    async def callback(self, interaction, button):
        prueba = pruebas.get(self.prueba_id)
        if not prueba: return
        
        if interaction.user not in prueba.participantes:
            prueba.participantes.append(interaction.user)
            await actualizar_mensaje(self.prueba_id)
            await interaction.response.send_message("¡Unido!", ephemeral=True)
        else:
            await interaction.response.send_message("Ya estás en la cola", ephemeral=True)

async def actualizar_mensaje(prueba_id):
    prueba = pruebas.get(prueba_id)
    if not prueba or not prueba.canal_prueba_id: return
    
    canal = bot.get_channel(prueba.canal_prueba_id)
    if not canal: return

    timestamp = prueba.ultima_sesion or int(datetime.now(timezone.utc).timestamp())
    embed = discord.Embed(title=f"Pruebas Grupo {prueba_id}")
    
    if prueba.entrenador_online:
        embed.color = discord.Color.green()
        embed.description = f"**Online** ✳️\n{prueba.entrenador_online.mention}"
        if prueba.participantes:
            embed.add_field(name="Participantes", value="\n".join([u.mention for u in prueba.participantes]))
    else:
        embed.color = discord.Color.red()
        embed.description = "**Offline** 🔴"
        embed.set_footer(text=f"Última actividad: <t:{timestamp}:F>")

    view = PruebaView(prueba_id) if prueba.entrenador_online and not prueba.prueba_en_curso else None

    try:
        if prueba.mensaje_prueba:
            await prueba.mensaje_prueba.edit(embed=embed, view=view)
        else:
            prueba.mensaje_prueba = await canal.send(embed=embed, view=view)
    except:
        prueba.mensaje_prueba = await canal.send(embed=embed, view=view)

def crear_comando(numero):
    @bot.command()
    @commands.has_role("Entrenador")
    async def comando(ctx):
        if numero not in pruebas:
            pruebas[numero] = Prueba()
        pruebas[numero].canal_prueba_id = ctx.channel.id
        pruebas[numero].ultima_sesion = int(datetime.now(timezone.utc).timestamp())  # ¡CORRECCIÓN AQUÍ!
        await actualizar_mensaje(numero)
        await ctx.send(f"✅ Grupo {numero} configurado", delete_after=5)
    comando.__name__ = f"set_here{numero}"

for i in range(1, 11):
    crear_comando(i)

from flask import Flask
from threading import Thread
app = Flask('')
@app.route('/')
def home(): return "Bot Online"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

try:
    bot.run(os.environ['TOKEN'])
except Exception as e:
    print(f'❌ Error al iniciar: {e}')
    raise