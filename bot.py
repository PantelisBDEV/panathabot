import discord
import os
import io
import requests
import asyncio
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands, tasks
from bs4 import BeautifulSoup
from dotenv import load_dotenv


load_dotenv()  # Φορτώνει μεταβλητές από το .env αρχείο

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)
last_article_url = None  # Αποθηκεύει το τελευταίο URL
last_article_urlbc = None  # Αποθηκεύει το τελευταίο URL


def get_latest_panathinaikosbc_article():
    url2 = "https://www.sport24.gr/basket/tag/panathinaikos/"
    response2 = requests.get(url2)
    soup2 = BeautifulSoup(response2.text, 'html.parser')

    h2 = soup2.find("h2", class_="article_card__title")
    if h2:
        a_tag2 = h2.find("a")
        title2 = a_tag2.find("span", class_="desktop_title").get_text(strip=True)
        link2 = a_tag2["href"]
        return title2, link2
    return None, None


def get_latest_panathinaikos_article():
    url = "https://www.sport24.gr/football/tag/panathinaikos/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    h2 = soup.find("h2", class_="article_card__title")
    if h2:
        a_tag = h2.find("a")
        title = a_tag.find("span", class_="desktop_title").get_text(strip=True)
        link = a_tag["href"]
        return title, link
    return None, None


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_for_new_article.start()
    check_for_new_bc_article.start()
    # ξεκίνα το background task
    # Δοκιμή
    # title, link = get_latest_panathinaikosbc_article()
    # if title and link:
    #    print(f"📰 Τίτλος: {title}")
    #    print(f"🔗 Link: {link}")
    # else:
    #    print("❌ Δεν βρέθηκε άρθρο.")


@tasks.loop(hours=1)
async def check_for_new_article():
    global last_article_url
    channel = bot.get_channel(CHANNEL_ID)
    try:
        title, link = get_latest_panathinaikos_article()
        if link and link != last_article_url:
            last_article_url = link
            await channel.send(f"📰 **{title}**\n🔗 {link}")
        else:
            print("⏳ No new article.")
    except Exception as e:
        print(f"❌ Error: {e}")


@tasks.loop(hours=1)
async def check_for_new_bc_article():
    global last_article_urlbc
    channel = bot.get_channel(CHANNEL_ID)
    try:
        title2, link2 = get_latest_panathinaikosbc_article()
        if link2 and link2 != last_article_urlbc:
            last_article_urlbc = link2
            await channel.send(f"📰 **{title2}**\n🔗 {link2}")
        else:
            print("⏳ No new article.")
    except Exception as e:
        print(f"❌ Error: {e}")


@bot.command()
async def nextmatch(ctx):
    await ctx.send("🔍 Έλεγχος για τον επόμενο αγώνα...")
    try:
        url = "https://www.pao.gr/the-matches/fixtures/"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        match = soup.select_one("div.match-row")
        if not match:
            await ctx.send("❌ Δεν βρέθηκε αγώνας.")
            return
        date_time = match.select_one("span.event-date").text.strip()
        league = match.select_one("span.event-category").text.strip()
        teams = match.select("span.teamname")
        match.select_one("span.results-mx").text.strip()
        if len(teams) >= 2:
            home_team = teams[0].text.strip()
            away_team = teams[1].text.strip()
        else:
            home_team = "Άγνωστη"
            away_team = "Άγνωστη"
        await ctx.send(
            f"🏟️ **Επόμενος Αγώνας Παναθηναϊκού**\n"
            f"**{home_team} vs {away_team}**\n"
            f"📅 Ημερομηνία & Ώρα: `{date_time}`\n"
            f"📘 Διοργάνωση: `{league}`\n"
            f"🔗 [Περισσότερα](https://www.pao.gr/the-matches/fixtures/)"
        )
    except Exception as e:
        await ctx.send(f"⚠️ Σφάλμα: {str(e)}")


@bot.command()
async def standings(ctx):
    url = "https://www.pao.gr/the-matches/standings/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("tr.standing-row")
    if not rows:
        await ctx.send("❌ Δεν βρέθηκε βαθμολογία.")
        return
    # Δημιουργία εικόνας
    width, row_height = 900, 40
    row_count = len(rows) + 3
    height = row_height * row_count
    image = Image.new("RGB", (width, height), color="black")
    draw = ImageDraw.Draw(image)
    # Font (πρέπει να υπάρχει στο server, π.χ. DejaVuSansMono)
    font = ImageFont.truetype("JonovaCondensed-Bold.ttf", 20)
    # Κεφαλίδες
    headers = ["ΘΣ", "ΟΜΑΔΑ", "ΑΓ", "Ν", "Ι", "Η", "ΓΥ", "ΓΚ", "ΔΙΑΦ", "ΒΑΘ"]
    x_positions = [10, 70, 370, 420, 460, 500, 540, 590, 640, 720]
    draw.text((10, 10), "STOIXIMAN SUPER LEAGUE 2024-25", fill="white", font=font)
    for i, head in enumerate(headers):
        draw.text((x_positions[i], row_height * 2), head, fill="white", font=font)
    # Περιεχόμενο
    for idx, row in enumerate(rows):
        y = row_height * (idx + 3)
        values = [
            row.select_one("td.rank").text.strip().replace(".", ""),
            row.select_one("td.teamname").text.strip(),
            row.select_one("td.matchplayed").text.strip(),
            row.select_one("td.matchwin").text.strip(),
            row.select_one("td.matchdraw").text.strip(),
            row.select_one("td.matchdefeat").text.strip(),
            row.select_one("td.goalds-y").text.strip(),
            row.select_one("td.goals-k").text.strip(),
            row.select_one("td.goalsdif").text.strip(),
            row.select_one("td.gatherpoints").text.strip()
        ]
        for i, val in enumerate(values):
            draw.text((x_positions[i], y), val, fill="green", font=font)
    # Save σε buffer
    with io.BytesIO() as image_binary:
        image.save(image_binary, "PNG")
        image_binary.seek(0)
        await ctx.send(file=discord.File(fp=image_binary, filename="standings.png"))


@bot.command()
async def panathahype(ctx):
    # Εξασφαλίζουμε ότι το bot είναι συνδεδεμένο σε voice channel
    if not ctx.message.author.voice:
        await ctx.send("Πρέπει να είσαι σε φωνητικό κανάλι για να ακούσεις τον ύμνο!")
        return
    channel = ctx.message.author.voice.channel
    voice_channel = await channel.connect()
    # Αναπαραγωγή του ύμνου (αντικατάστησε με το σωστό μονοπάτι προς το mp3)
    voice_channel.play(discord.FFmpegPCMAudio('umnos.mp3'), after=lambda e: print('Finished playing'))
    # Περιμένουμε να τελειώσει το mp3
    while voice_channel.is_playing():
        await asyncio.sleep(1)
    # Όταν τελειώσει, αποσυνδέουμε το bot από το κανάλι φωνής
    await voice_channel.disconnect()


bot.run(TOKEN)
