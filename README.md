## About
The **Telegram Airdrop Bot** 💰 helps you to manage your airdrops on ERC-20, BEP-20 etc. tokens.

## Features
- Check if the wallet length is correct
- Set a max cap
- Each wallet address can only be submitted once
- Users can change their wallet address after submission  
- Receive detailed notifications for new submissions
- Enable / disable the airdrop
- Admins can export the airdrop list by command (`/airdroplist`)

> 💡 Got a feature idea? Open an [issue](https://github.com/fabston/Telegram-Airdrop-Bot/issues/new?assignees=&labels=enhancement&template=feature-request---.md) and I might implement it.


## Installation
> ⚠️ Best to run the bot on a VPS. I can recommend <a href="https://fabston.dev/hetzner" title="Get €20 in cloud credits">Hetzner</a>'s CX11 VPS for 2.89€/month. [Sign up](https://fabston.dev/hetzner) now and receive **€20 free** credits.
1. Log into MySQL (`sudo mysql`) and create a dedicated database and user with the following commands:
   1. `CREATE DATABASE TelegramAirdropBot;`
   1. `CREATE USER 'AirdropUser'@'localhost' IDENTIFIED BY '<YOUR PASSWORD>';`
   1. `GRANT ALL PRIVILEGES ON TelegramAirdropBot. * TO 'AirdropUser'@'localhost';`
   1. `exit;`
1. Clone this repository `git clone https://github.com/fabston/Telegram-Airdrop-Bot.git`
1. Create your virtual environment `python3 -m venv Telegram-Airdrop-Bot`
1. Activate it `source Telegram-Airdrop-Bot/bin/activate && cd Telegram-Airdrop-Bot`
1. Install all requirements `pip install -r requirements.txt`
1. The bot runs behind a webhook, so you have to create a SSL cert first:
   1. `openssl genrsa -out webhook_pkey.pem 2048`
   1. `openssl req -new -x509 -days 3650 -key webhook_pkey.pem -out webhook_cert.pem`
      1. _When asked for "Common Name (e.g. server FQDN or YOUR name)" you should reply with your server ip._
1. Edit and update [`config.py`](https://github.com/fabston/Telegram-Airdrop-Bot/blob/master/config.py)
1. Run the bot `python main.py`

