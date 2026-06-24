# 🎯 Radar + Acelerómetro + ML

Proyecto con ESP32 que combina un sensor ultrasónico HC-SR04 y un acelerómetro ADXL345 para mostrar un radar animado y un cubo 3D en tiempo real, clasificando el movimiento con Machine Learning.

---

## 📸 Vista de la app

```
┌─────────────────────┬──────────────────┐
│   RADAR animado     │   Cubo 3D        │
│   con barrido       │   que rota       │
│   + puntos          │   según el       │
│   detectados        │   ADXL345        │
│                     │                  │
│  [ML: SACUDIDA 94%] │   🟥 rojo        │
└─────────────────────┴──────────────────┘
```

---

## 🧠 ¿Qué hace?

- El **radar** muestra la distancia medida por el HC-SR04 con barrido animado
- Un **cubo 3D** se tambalea en pantalla siguiendo el movimiento del ADXL345
- El **modelo ML** (Random Forest) clasifica en tiempo real el estado de movimiento y cambia el color de toda la escena:

| Estado | Color |
|--------|-------|
| 🟢 ESTABLE | Verde |
| 🟡 SUAVE | Amarillo |
| 🔴 SACUDIDA | Rojo |

---

## 🔌 Componentes

| Componente | Cantidad |
|---|---|
| ESP32 | 1 |
| HC-SR04 (ultrasónico) | 1 |
| ADXL345 (acelerómetro I2C) | 1 |
| Cables jumper | varios |
| Protoboard | 1 |

---

## 🔧 Conexiones

### ADXL345 → ESP32 (I2C)

| ADXL345 | ESP32 |
|---------|-------|
| VCC | 3.3V |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

### HC-SR04 → ESP32

| HC-SR04 | ESP32 |
|---------|-------|
| VCC | 5V |
| GND | GND |
| TRIG | GPIO 5 |
| ECHO | GPIO 18 |

---

## 📁 Estructura del proyecto

```
radar-accel/
├── esp32/
│   └── radar_accel.ino       ← código del ESP32
└── python/
    ├── collect_data.py       ← recolectar datos etiquetados
    ├── train_model.py        ← entrenar el modelo ML
    ├── app.py                ← app principal (radar + cubo + ML)
    ├── gestures.csv          ← datos de entrenamiento (generado)
    └── model.pkl             ← modelo entrenado (generado)
```

---

## 📦 Dependencias Python

```bash
pip install pyserial scikit-learn numpy pandas matplotlib seaborn pygame PyOpenGL PyOpenGL_accelerate
```

---

## 🚀 Flujo de uso

### 1. Flashear el ESP32
Abre `esp32/radar_accel.ino` en Arduino IDE y súbelo al ESP32.

**Librerías Arduino necesarias:** ninguna externa, solo `Wire.h` (incluida por defecto).

### 2. Recolectar datos de entrenamiento
Ejecuta `collect_data.py` tres veces, una por cada estado:

```bash
# Estado 0 — deja el ESP32 completamente quieto
python collect_data.py   # ingresa 0, 200 muestras

# Estado 1 — muévelo despacio y suavemente
python collect_data.py   # ingresa 1, 200 muestras

# Estado 2 — agítalo con fuerza
python collect_data.py   # ingresa 2, 200 muestras
```

### 3. Entrenar el modelo
```bash
python train_model.py
```
Esto genera `model.pkl` y muestra la matriz de confusión. Se espera un accuracy mayor al 95%.

### 4. Lanzar la app
```bash
python app.py
```

> ⚠️ Cambia `PORT = "COM3"` por el puerto correcto de tu ESP32.
> En Linux/Mac suele ser `/dev/ttyUSB0` o `/dev/tty.usbserial-XXXX`.

---

## 🤖 Machine Learning

### Algoritmo
**Random Forest Classifier** con 100 árboles.

### Features extraídas (por ventana de 15 muestras)

| Feature | Descripción |
|---------|-------------|
| `mag_mean` | Media de la magnitud del vector aceleración |
| `mag_std` | Desviación estándar de la magnitud |
| `mag_range` | Rango (max - min) de la magnitud |
| `std_x` | Desviación estándar del eje X |
| `std_y` | Desviación estándar del eje Y |
| `std_z` | Desviación estándar del eje Z |

### Resultados típicos
```
Accuracy CV-5: 0.985 ± 0.023
Precision / Recall: 1.00 en los 3 estados
```

---

## ⚙️ Configuración rápida

| Variable | Archivo | Descripción |
|----------|---------|-------------|
| `PORT` | `app.py`, `collect_data.py` | Puerto serial del ESP32 |
| `BAUD` | todos | Velocidad serial (115200) |
| `WINDOW` | `app.py`, `collect_data.py` | Tamaño de ventana ML (15 muestras) |
| `MAX_DIST` | `app.py` | Distancia máxima del radar en cm (200) |

---

## 🛠️ Posibles errores

| Error | Solución |
|-------|----------|
| `ModuleNotFoundError` | Instala la dependencia con `pip install <modulo>` |
| `SerialException` | Verifica que el puerto COM sea correcto y el ESP32 esté conectado |
| El radar se ve muy pequeño | Ajusta `CX`, `CY` y `MAX_R` en `draw_radar_surface()` |
| Modelo con baja accuracy | Graba más muestras o en condiciones más diferenciadas |

---

## 📜 Licencia

MIT — libre para usar, modificar y compartir.