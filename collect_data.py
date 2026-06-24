import serial, csv, time, numpy as np

PORT = "COM4"   # Linux: /dev/ttyUSB0
BAUD = 115200
FILE = "movement_data.csv"
WINDOW = 15     # lecturas por muestra

LABELS = ["ESTABLE", "SUAVE", "SACUDIDA"]

def extract_features(buf):
    arr = np.array(buf)
    ax, ay, az = arr[:,0], arr[:,1], arr[:,2]
    mag = np.sqrt(ax**2 + ay**2 + az**2)
    return [
        np.mean(mag), np.std(mag),
        np.max(mag) - np.min(mag),
        np.std(ax), np.std(ay), np.std(az),
    ]

print("Etiquetas: 0=ESTABLE  1=SUAVE  2=SACUDIDA")
label = LABELS[int(input("¿Cuál grabas? (0/1/2): "))]
n = int(input("¿Cuántas muestras? (recomendado 200): "))

ser = serial.Serial(PORT, BAUD, timeout=2)
time.sleep(2); ser.flushInput()
print(f"\n🔴 Grabando '{label}'... mueve el ESP32 según corresponda\n")

buf, count = [], 0
with open(FILE, "a", newline="") as f:
    writer = csv.writer(f)
    while count < n:
        try:
            line = ser.readline().decode().strip()
            parts = line.split(",")
            if len(parts) != 4: continue
            ax, ay, az = float(parts[0]), float(parts[1]), float(parts[2])
            buf.append([ax, ay, az])
            if len(buf) == WINDOW:
                features = extract_features(buf)
                writer.writerow(features + [label])
                count += 1
                print(f"  [{count}/{n}] ✔ {label}")
                buf = buf[WINDOW//2:]  # ventana deslizante
        except: continue

print(f"\n✅ Listo. Datos en {FILE}")
ser.close()