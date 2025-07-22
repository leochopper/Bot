import discord
import os
import asyncio
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
from discord.errors import NotFound

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Diccionario para almacenar múltiples pruebas
pruebas = {}

class Prueba:
    def __init__(self):
        self.entrenador_online = None
        self.participantes = []
        self.prueba_en_curso = False
        self.mensaje_prueba = None
        self.canal_prueba_id = None

class PruebaView(View):
    def __init__(self, prueba_id):
        super().__init__(timeout=None)
        self.prueba_id = prueba_id

    @discord.ui.button(label="Unirse a la cola",
                       style=discord.ButtonStyle.green,
                       custom_id="unirse_cola")
    async def unirse_cola(self, interaction: discord.Interaction, button: Button):
        prueba = pruebas.get(self.prueba_id)
        if not prueba:
            return

        if interaction.user not in prueba.participantes:
            prueba.participantes.append(interaction.user)
            await actualizar_mensaje_prueba(self.prueba_id)
            await interaction.response.send_message("¡Te has unido a la cola!", ephemeral=True)
        else:
            await interaction.response.send_message("Ya estás en la cola.", ephemeral=True)

async def actualizar_mensaje_prueba(prueba_id):
    prueba = pruebas.get(prueba_id)
    if not prueba or not prueba.canal_prueba_id:
        return

    canal = bot.get_channel(prueba.canal_prueba_id)
    if not canal:
        return

    # Timestamp dinámico para Discord
    timestamp = int(datetime.now().timestamp())

    embed = discord.Embed(title=f"Sistema de Pruebas de Ascenso (Grupo {prueba_id})")
    view = PruebaView(prueba_id) if (prueba.entrenador_online and not prueba.prueba_en_curso) else None

    if prueba.entrenador_online:
        embed.color = discord.Color.green()
        embed.description = f"Prueba abierta ✳️\n{prueba.entrenador_online.mention} está online"
        if prueba.participantes:
            embed.add_field(name="Participantes",
                          value="\n".join([user.mention for user in prueba.participantes]),
                          inline=False)
    else:
        embed.color = discord.Color.red()
        embed.description = "Prueba cerrada 🔴\nNo hay entrenadores online"
        embed.set_footer(text=f"Última sesión: <t:{timestamp}:f>")  # Formato dinámico

    try:
        if prueba.mensaje_prueba:
            await prueba.mensaje_prueba.edit(embed=embed, view=view)
        else:
            prueba.mensaje_prueba = await canal.send(embed=embed, view=view)
    except (NotFound, AttributeError):
        prueba.mensaje_prueba = await canal.send(embed=embed, view=view)

@bot.command(name="set_here")
@commands.has_role("Entrenador")
async def set_here(ctx, prueba_id: int = 1):
    if prueba_id not in pruebas:
        pruebas[prueba_id] = Prueba()
    pruebas[prueba_id].canal_prueba_id = ctx.channel.id
    await actualizar_mensaje_prueba(prueba_id)
    await ctx.send(f"✅ Canal de pruebas {prueba_id} configurado aquí.", delete_after=5)

@bot.command(name="online")
@commands.has_role("Entrenador")
async def online(ctx, prueba_id: int = 1):
    prueba = pruebas.get(prueba_id)
    if not prueba:
        await ctx.send(f"❌ El grupo {prueba_id} no existe. Usa `!set_here{prueba_id}` primero.", delete_after=5)
        return
    if prueba.entrenador_online:
        await ctx.send("⚠️ Ya hay un entrenador online.", delete_after=5)
        return
    prueba.entrenador_online = ctx.author
    prueba.prueba_en_curso = False
    await actualizar_mensaje_prueba(prueba_id)
    await ctx.send("🟢 Modo entrenador activado.", delete_after=5)
    await asyncio.sleep(7200)  # 2 horas de timeout
    if pruebas.get(prueba_id) and pruebas[prueba_id].entrenador_online == ctx.author:
        await offline(ctx, prueba_id)

@bot.command(name="offline")
@commands.has_role("Entrenador")
async def offline(ctx, prueba_id: int = 1):
    prueba = pruebas.get(prueba_id)
    if not prueba:
        return
    prueba.entrenador_online = None
    prueba.participantes = []
    prueba.prueba_en_curso = False
    await actualizar_mensaje_prueba(prueba_id)
    await ctx.send("🔴 Modo entrenador desactivado.", delete_after=5)

@bot.command(name="iniciar")
@commands.has_role("Entrenador")
async def iniciar(ctx, prueba_id: int = 1):
    prueba = pruebas.get(prueba_id)
    if not prueba:
        return
    prueba.prueba_en_curso = True
    await actualizar_mensaje_prueba(prueba_id)
    await ctx.send("🟢 Prueba iniciada. Los participantes no pueden unirse ahora.", delete_after=5)

@bot.command(name="finalizar")
@commands.has_role("Entrenador")
async def finalizar(ctx, prueba_id: int = 1):
    prueba = pruebas.get(prueba_id)
    if not prueba:
        await ctx.send(f"❌ El grupo {prueba_id} no existe.", delete_after=5)
        return
    
    # Reinicia todo el estado (como !offline)
    prueba.entrenador_online = None
    prueba.participantes = []
    prueba.prueba_en_curso = False
    
    await actualizar_mensaje_prueba(prueba_id)
    await ctx.send(f"🔴 Prueba {prueba_id} finalizada. Estado reiniciado.", delete_after=5)

@bot.command(name="fix_msg")
@commands.has_role("Entrenador")
async def fix_msg(ctx, prueba_id: int = 1):
    prueba = pruebas.get(prueba_id)
    if not prueba:
        return
    prueba.mensaje_prueba = None
    await actualizar_mensaje_prueba(prueba_id)
    await ctx.send("✅ Mensaje recreado manualmente.", delete_after=5)

# Sistema keep_alive para 24/7
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot en línea"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(os.getenv('TOKEN'))