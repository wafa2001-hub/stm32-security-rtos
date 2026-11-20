import logging
import os
import re
import smtplib
import ssl
import time
from datetime import datetime
from email.message import EmailMessage

import serial
from dotenv import load_dotenv

load_dotenv()

PORT = os.getenv("SERIAL_PORT", "COM4")
BAUD = int(os.getenv("BAUD", "115200"))
COOLDOWN = int(os.getenv("COOLDOWN", "60"))

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")

RE_ALERT = re.compile(r"^ALERT,(\d+)$")
RE_CPU = re.compile(r"^cpu=(\d+)%$")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bridge.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("bridge")


def send_email(alert_value, cpu):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = "[ALERTE] Attaque détectée sur STM32"
    body = (
        f"Une alerte a été détectée.\n\n"
        f"Date/heure : {now}\n"
        f"Valeur ALERT : {alert_value}\n"
        f"Charge CPU : {cpu if cpu is not None else 'inconnue'}%\n"
    )

    if not (SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_TO):
        log.warning("EMAIL simulé (SMTP non configuré): %s | %s",
                    subject, body.replace("\n", " "))
        return True

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_TO
    msg.set_content(body)

    try:
        ctx = ssl.create_default_context()
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx,
                                  timeout=15) as s:
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
                s.starttls(context=ctx)
                s.login(SMTP_USER, SMTP_PASS)
                s.send_message(msg)
        log.info("Email envoyé à %s", EMAIL_TO)
        return True
    except Exception as e:
        log.error("Échec envoi email: %s", e)
        return False


def handle_line(line, state):
    m = RE_CPU.match(line)
    if m:
        state["cpu"] = int(m.group(1))
        log.info("CPU = %d%%", state["cpu"])
        return

    m = RE_ALERT.match(line)
    if m:
        value = int(m.group(1))
        log.warning("ALERT reçu (valeur=%d, cpu=%s)", value, state["cpu"])
        now = time.time()
        if now - state["last_email"] >= COOLDOWN:
            if send_email(value, state["cpu"]):
                state["last_email"] = now
        else:
            reste = int(COOLDOWN - (now - state["last_email"]))
            log.info("Email ignoré (cooldown, encore %ds)", reste)
        return

    log.debug("Trame ignorée: %r", line)


def run():
    state = {"cpu": None, "last_email": 0.0}
    while True:
        try:
            log.info("Ouverture de %s @ %d", PORT, BAUD)
            with serial.Serial(PORT, BAUD, timeout=1) as ser:
                log.info("Connecté.")
                while True:
                    raw = ser.readline()
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if line:
                        handle_line(line, state)
        except serial.SerialException as e:
            log.error("Port série indisponible: %s. Nouvelle tentative dans 3s...", e)
            time.sleep(3)
        except KeyboardInterrupt:
            log.info("Arrêt demandé.")
            break


if __name__ == "__main__":
    run()