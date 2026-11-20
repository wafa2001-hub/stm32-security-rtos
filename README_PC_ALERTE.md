# Passerelle PC & Alerte Email (Membre 2)

Partie PC du projet « Sécurité des Systèmes Embarqués Temps Réel (STM32 & FreeRTOS) ».
Elle lit la télémétrie envoyée par la STM32 via UART/USB, détecte les alertes
et envoie un email sécurisé avec un cooldown anti-inondation.

## Architecture

```
STM32 (UART/USB) ──► serial_alert_bridge.py ──► Email SMTP (TLS/SSL)
                         │
mock_stm32_sender.py ────┘ (simulation sans carte, via ports COM virtuels)
```

## Format des trames UART

Baudrate : 115200, une trame par ligne (terminée par `\n`).

| Trame        | Signification                         |
|--------------|---------------------------------------|
| `cpu=45%`    | Charge CPU (télémétrie périodique)    |
| `ALERT,100`  | Alerte d'attaque détectée             |

Toute autre trame est ignorée sans faire planter la passerelle.

## Installation

```
python -m venv venv
venv\Scripts\activate        (Windows)
source venv/bin/activate     (Linux)
pip install -r requirements.txt
```

Copier `.env.example` vers `.env` puis l'adapter (ne jamais publier `.env`).

## Lancement sans carte (mock)

1. Créer une paire de ports virtuels :
   - Windows : `com0com` (ex. COM5 <-> COM4)
   - Linux : `socat -d -d pty,raw,echo=0 pty,raw,echo=0`
2. Terminal 1 (simulateur) :
   ```
   python mock_stm32_sender.py --port COM5
   ```
3. Terminal 2 (passerelle, `SERIAL_PORT=COM4` dans `.env`) :
   ```
   python serial_alert_bridge.py
   ```

## Lancement avec la STM32 réelle

Brancher la carte en USB, repérer son port COM (Gestionnaire de périphériques),
puis mettre ce port dans `SERIAL_PORT` du fichier `.env`.

## Configuration email

Renseigner dans `.env` : `SMTP_HOST`, `SMTP_PORT` (465 = SSL, 587 = STARTTLS),
`SMTP_USER`, `SMTP_PASS`, `EMAIL_TO`.
Pour Gmail, utiliser un « mot de passe d'application » (validation en deux étapes requise).
Si ces variables sont vides, l'email est simulé dans la console.

## Fonctionnalités

- Parsing robuste par expressions régulières
- Reconnexion automatique si le port série disparaît
- Cooldown anti-inondation (`COOLDOWN`, en secondes)
- Logs console et fichier `bridge.log`
- Secrets dans `.env` (jamais dans le code)

## Tests effectués

| Test                              | Résultat attendu                          |
|-----------------------------------|-------------------------------------------|
| Trame corrompue                   | Ignorée, pas de crash                     |
| Port coupé puis rétabli           | Reconnexion automatique                   |
| Rafale de `ALERT,100`             | Un seul email par fenêtre de cooldown     |
| Alerte avec SMTP configuré        | Email reçu                                |
