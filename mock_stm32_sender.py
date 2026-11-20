import argparse
import random
import time

import serial


def main():
    parser = argparse.ArgumentParser(description="Simulateur STM32 (mock)")
    parser.add_argument("--port", default="COM5")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--attack-every", type=int, default=15,
                        help="Attaque toutes les N secondes")
    parser.add_argument("--attack-duration", type=int, default=3,
                        help="Durée de l'attaque en secondes")
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=1)
    print(f"[MOCK] Connecté sur {args.port} @ {args.baud}")

    start = time.time()
    attack_until = 0

    try:
        while True:
            now = time.time()
            elapsed = now - start

            # Déclenche une attaque périodique
            if int(elapsed) % args.attack_every == 0 and now > attack_until + 1:
                attack_until = now + args.attack_duration
                print("[MOCK] >>> ATTAQUE")

            if now < attack_until:
                cpu = random.randint(90, 99)
                ser.write(f"cpu={cpu}%\n".encode())
                ser.write(b"ALERT,100\n")
                print(f"[MOCK] cpu={cpu}% + ALERT,100")
            else:
                cpu = random.randint(20, 40)
                ser.write(f"cpu={cpu}%\n".encode())
                print(f"[MOCK] cpu={cpu}%")

            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[MOCK] Arrêt")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
