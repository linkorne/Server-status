import os
import json
import socket
import urllib.request
import urllib.error

SERVER = os.environ["MINECRAFT_SERVER"]
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = os.environ["CHANNEL_ID"]

STATUS_FILE = "status.json"


def get_server_status():
    """
    Vérifie directement si le serveur Minecraft est joignable.
    """

    try:
        # Récupération de l'adresse IP et du port via DNS SRV
        srv_query = f"_minecraft._tcp.{SERVER}"

        # On utilise l'API pour obtenir les informations DNS du serveur
        url = f"https://api.mcsrvstat.us/3/{SERVER}"

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "MinecraftDiscordStatusBot/1.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        online = data.get("online", False)

        players = data.get("players", {})

        return {
            "online": online,
            "players": players.get("online", 0),
            "max_players": players.get("max", 0)
        }

    except Exception as error:
        print("Erreur :", error)

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

        json.dump(
            {
                "online": online
            },
            file
        )


def send_discord_message(embed):

    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"

    payload = {
        "embeds": [embed]
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "MinecraftDiscordStatusBot/1.0"
        }
    )

    try:

        with urllib.request.urlopen(request, timeout=20) as response:

            print(
                "Message Discord envoyé :",
                response.status
            )

    except urllib.error.HTTPError as error:

        print(
            "Erreur Discord :",
            error.code
        )

        print(
            error.read().decode("utf-8")
        )


def main():

    current = get_server_status()

    previous = get_previous_status()

    online = current["online"]

    print("--------------------------------")
    print("Serveur :", SERVER)
    print("Online :", online)
    print(
        "Joueurs :",
        f"{current['players']}/{current['max_players']}"
    )
    print("État précédent :", previous)
    print("--------------------------------")

    if previous is None:

        print(
            "Premier lancement : "
            "état enregistré."
        )

        save_status(online)

        return

    # OFFLINE -> ONLINE

    if online and previous is False:

        embed = {

            "title": "🟢 Serveur Minecraft ouvert !",

            "description": (
                "Le serveur Minecraft est maintenant disponible !\n\n"
                f"🎮 **Adresse :** `{SERVER}`\n"
                f"👥 **Joueurs :** "
                f"`{current['players']}/{current['max_players']}`"
            ),

            "color": 5763719
        }

        send_discord_message(embed)

    # ONLINE -> OFFLINE

    elif not online and previous is True:

        embed = {

            "title": "🔴 Serveur Minecraft fermé",

            "description":
                "Le serveur Minecraft vient de passer hors ligne.",

            "color": 15548997
        }

        send_discord_message(embed)

    save_status(online)


if __name__ == "__main__":

    main()
