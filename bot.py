import discord
import os
import asyncio
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime
from discord.errors import NotFound

intents = discord.Intents.all()
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
        embed.set_footer(text=f"Última sesión: <t:{timestamp}:f>")

    try:
        if prueba.mensaje_prueba:
            await prueba.mensaje_prueba.edit(embed=embed, view=view)
        else:
            prueba.mensaje_prueba = await canal.send(embed=embed, view=view)
    except (NotFound, AttributeError):
        prueba.mensaje_prueba = await canal.send(embed=embed, view=view)

@bot.command()
@commands.has_role("Entrenador")
async def set_here1(ctx):
    if 1 not in pruebas:
        pruebas[1] = Prueba()
    pruebas[1].canal_prueba_id = ctx.channel.id
    await actualizar_mensaje_prueba(1)
    await ctx.send("✅ Canal de pruebas 1 configurado aquí.", delete_after=5)

@bot.command()
@commands.has_role("Entrenador")
async def online1(ctx):
    prueba = pruebas.get(1)
    if not prueba:
        await ctx.send("❌ Usa primero !set_here1 en este canal.", delete_after=5)
        return
    if prueba.entrenador_online:
        await ctx.send("⚠️ Ya hay un entrenador online.", delete_after=5)
        return
    
    prueba.entrenador_online = ctx.author
    prueba.prueba_en_curso = False
    await actualizar_mensaje_prueba(1)
    await ctx.send("🟢 Modo entrenador activado.", delete_after=5)
    await asyncio.sleep(7200)  # 2 horas de timeout
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
    await actualizar_mensaje_prueba(1)
    await ctx.send("🔴 Modo entrenador desactivado.", delete_after=5)

@bot.command()
@commands.has_role("Entrenador")
async def iniciar1(ctx):
    prueba = pruebas.get(1)
    if not prueba:
        return
    prueba.prueba_en_curso = True
    await actualizar_mensaje_prueba(1)
    await ctx.send("🟢 Prueba iniciada. Los participantes no pueden unirse ahora.", delete_after=5)

@bot.command()
@commands.has_role("Entrenador")
async def finalizar1(ctx):
    prueba = pruebas.get(1)
    if not prueba:
        await ctx.send("❌ No hay prueba activa en este grupo.", delete_after=5)
        return
    
    prueba.entrenador_online = None
    prueba.participantes = []
    prueba.prueba_en_curso = False
    await actualizar_mensaje_prueba(1)
    await ctx.send("🔴 Prueba finalizada. Estado reiniciado.", delete_after=5)

@bot.command()
@commands.has_role("Entrenador")
async def fix_msg1(ctx):
    prueba = pruebas.get(1)
    if not prueba:
        return
    prueba.mensaje_prueba = None
    await actualizar_mensaje_prueba(1)
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