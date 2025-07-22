import discord
import os
import asyncio
from discord.ext import commands
from discord.ui import Button, View
from datetime import datetime, timezone
from discord.errors import NotFound

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Diccionario para almacenar hasta 10 grupos de pruebas
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

    # Obtener timestamp en UTC y formatear para Discord
    timestamp = prueba.ultima_sesion if prueba.ultima_sesion else int(datetime.now(timezone.utc).timestamp())
    hora_discord = f"<t:{timestamp}:F>"  # Formato completo con fecha y hora local
    
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
        embed.set_footer(text=f"Última actividad: {hora_discord}")

    try:
        if prueba.mensaje_prueba:
            await prueba.mensaje_prueba.edit(embed=embed, view=view)
        else:
            prueba.mensaje_prueba = await canal.send(embed=embed, view=view)
    except (NotFound, AttributeError):
        prueba.mensaje_prueba = await canal.send(embed=embed, view=view)

# Función para generar comandos dinámicos
def crear_comandos_grupo(numero):
    @bot.command()
    @commands.has_role("Entrenador")
    async def set_here(ctx):
        if numero not in pruebas:
            pruebas[numero] = Prueba()
        pruebas[numero].canal_prueba_id = ctx.channel.id
        pruebas[numero].ultima_sesion = int(datetime.now(timezone.utc).timestamp()
        await actualizar_mensaje_prueba(numero)
        await ctx.send(f"✅ **Canal configurado para pruebas Grupo {numero}**", delete_after=5)
    set_here.__name__ = f"set_here{numero}"

    @bot.command()
    @commands.has_role("Entrenador")
    async def online(ctx):
        prueba = pruebas.get(numero)
        if not prueba:
            await ctx.send(f"⚠️ Usa primero `!set_here{numero}` en este canal.", delete_after=5)
            return
        if prueba.entrenador_online:
            await ctx.send("⚠️ Ya hay un entrenador activo.", delete_after=5)
            return
        
        prueba.entrenador_online = ctx.author
        prueba.ultima_sesion = int(datetime.now(timezone.utc).timestamp())
        prueba.prueba_en_curso = False
        await actualizar_mensaje_prueba(numero)
        await ctx.send(f"🟢 **Modo entrenador activado (Grupo {numero})**", delete_after=5)
        await asyncio.sleep(7200)
        if pruebas.get(numero) and pruebas[numero].entrenador_online == ctx.author:
            await offline(ctx)
    online.__name__ = f"online{numero}"

    # ... (Repite el mismo patrón para offline, iniciar, finalizar y reset)

# Crear comandos para los grupos 1 al 10
for i in range(1, 11):
    crear_comandos_grupo(i)

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