import os
import json
import urllib.request
import urllib.error

SERVER = os.environ["MINECRAFT_SERVER"]
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

STATUS_FILE = "status.json"


def get_minecraft_status():
    url = f"https://api.mcsrvstat.us/3/{SERVER}"

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Minecraft-Discord-Status-Bot/1.0"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        online = data.get("online", False)

        if not online:
            return {
                "online": False,
                "players": 0,
                "max_players": 0
            }

        players = data.get("players", {})

        return {
            "online": True,
            "players": players.get("online", 0),
            "max_players": players.get("max", 0)
        }

    except Exception as error:
        print(f"Erreur de vérification : {error}")

        return {
            "online": False,
            "players": 0,
            "max_players": 0
        }


def get_previous_status():
    if not os.path.exists(STATUS_FILE):
        return None

    try:
        with open(STATUS_FILE, "r") as file:
            data = json.load(file)

        return data.get("online")

    except Exception:
        return None


def save_status(online):
    with open(STATUS_FILE, "w") as file:
        json.dump({"online": online}, file)


def send_discord_message(content=None, embed=None):

    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"

    payload = {}

    if content:
        payload["content"] = content

    if embed:
        payload["embeds"] = [embed]

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Minecraft-Discord-Status-Bot/1.0"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            print("Message Discord envoyé :", response.status)

    except urllib.error.HTTPError as error:
        print("Erreur Discord :", error.code)
        print(error.read().decode("utf-8"))


def main():

    current = get_minecraft_status()
    previous = get_previous_status()

    online = current["online"]

    print(
        f"Serveur : {SERVER} | "
        f"Online : {online} | "
        f"Joueurs : {current['players']}/{current['max_players']}"
    )

    # Premier lancement :
    # on mémorise simplement l'état sans envoyer de notification.
    if previous is None:
        save_status(online)
        print("Premier lancement : état enregistré.")
        return

    # Le serveur vient de démarrer
    if online and previous is False:

        embed = {
            "title": "🟢 Serveur Minecraft ouvert !",
            "description": (
                "Le serveur Minecraft est maintenant disponible !\n\n"
                f"🎮 **Adresse :** `{SERVER}`\n"
                f"👥 **Joueurs :** `{current['players']}/{current['max_players']}`"
            ),
            "color": 5763719
        }

        send_discord_message(embed=embed)

    # Le serveur vient de s'arrêter
    elif not online and previous is True:

        embed = {
            "title": "🔴 Serveur Minecraft fermé",
            "description": (
                "Le serveur Minecraft vient de passer hors ligne."
            ),
            "color": 15548997
        }

        send_discord_message(embed=embed)

    save_status(online)


if __name__ == "__main__":
    main()
