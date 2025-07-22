import discord
import os
import asyncio
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
from discord.errors import NotFound

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Diccionario para múltiples pruebas
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

    # Formatear timestamp para Discord
    timestamp = prueba.ultima_sesion if prueba.ultima_sesion else int(datetime.now().timestamp())
    embed = discord.Embed(title=f"⚔️ Sistema de Pruebas (Grupo {prueba_id})")
    view = PruebaView(prueba_id) if (prueba.entrenador_online and not prueba.prueba_en_curso) else None

    if prueba.entrenador_online:
        embed.color = discord.Color.green()
        embed.description = f"**Prueba abierta** ✳️\n{prueba.entrenador_online.mention} está disponible"
        if prueba.participantes:
            embed.add_field(name="👥 Participantes",
                          value="\n".join([user.mention for user in prueba.participantes]),
                          inline=False)
    else:
        embed.color = discord.Color.red()
        embed.description = "**Prueba cerrada** 🔴\nEsperando entrenadores..."
        embed.set_footer(text=f"Última actividad: <t:{timestamp}:f>")

    try:
        if prueba.mensaje_prueba:
            await prueba.mensaje_prueba.edit(embed=embed, view=view)
        else:
            prueba.mensaje_prueba = await canal.send(embed=embed, view=view)
    except (NotFound, AttributeError):
        # Si el mensaje fue eliminado, se recrea
        prueba.mensaje_prueba = await canal.send(embed=embed, view=view)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando no reconocido. Usa `!help`", delete_after=5)

@bot.command()
@commands.has_role("Entrenador")
async def set_here1(ctx):
    if 1 not in pruebas:
        pruebas[1] = Prueba()
    pruebas[1].canal_prueba_id = ctx.channel.id
    pruebas[1].ultima_sesion = int(datetime.now().timestamp())
    await actualizar_mensaje_prueba(1)
    await ctx.send("✅ **Canal configurado para pruebas Grupo 1**", delete_after=5)

@bot.command()
@commands.has_role("Entrenador")
async def online1(ctx):
    prueba = pruebas.get(1)
    if not prueba:
        await ctx.send("⚠️ Usa primero `!set_here1` en este canal.", delete_after=5)
        return
    if prueba.entrenador_online:
        await ctx.send("⚠️ Ya hay un entrenador activo.", delete_after=5)
        return
    
    prueba.entrenador_online = ctx.author
    prueba.ultima_sesion = int(datetime.now().timestamp())
    prueba.prueba_en_curso = False
    await actualizar_mensaje_prueba(1)
    await ctx.send("🟢 **Modo entrenador activado**", delete_after=5)
    await asyncio.sleep(7200)  # Auto-offline después de 2 horas
    if pruebas.get(1) and pruebas[1].entrenador_online == ctx.author:
        await offline1(ctx)

@bot.command()
@commands.has_role("Entrenador")
async def offline1(ctx):
    prueba = pruebas.get(1)
    if not prueba:
        return
    
    prueba.entrenador_online = None
    prueba.participantes = []
    prueba.prueba_en_curso = False
    prueba.ultima_sesion = int(datetime.now().timestamp())
    await actualizar_mensaje_prueba(1)
    await ctx.send("🔴 **Modo entrenador desactivado**", delete_after=5)

@bot.command()
@commands.has_role("Entrenador")
async def iniciar1(ctx):
    prueba = pruebas.get(1)
    if not prueba:
        return
    
    prueba.prueba_en_curso = True
    prueba.ultima_sesion = int(datetime.now().timestamp())
    await actualizar_mensaje_prueba(1)
    await ctx.send("⏳ **Prueba iniciada: No se admiten más participantes**", delete_after=5)

@bot.command()
@commands.has_role("Entrenador")
async def finalizar1(ctx):
    prueba = pruebas.get(1)
    if not prueba:
        return
    
    prueba.entrenador_online = None
    prueba.participantes = []
    prueba.prueba_en_curso = False
    prueba.ultima_sesion = int(datetime.now().timestamp())
    await actualizar_mensaje_prueba(1)
    await ctx.send("🏁 **Prueba finalizada y reiniciada**", delete_after=5)

@bot.command()
@commands.has_role("Entrenador")
async def reset1(ctx):
    pruebas[1] = Prueba()  # Reinicia completamente el Grupo 1
    await ctx.send("🔄 **Grupo 1 reiniciado. Usa `!set_here1` en un canal nuevo**", delete_after=5)

# Sistema 24/7
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot Online"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
bot.run(os.getenv('TOKEN'))