import serial, pickle, time, math, numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from collections import deque # Importante para evitar fugas de memoria

PORT = "COM4"
BAUD = 115200
WINDOW = 15

try:
    with open("model.pkl","rb") as f:
        model = pickle.load(f)
except Exception as e:
    print(f"Error cargando el modelo: {e}")
    exit()

# ── Colores por estado ML ──────────────────────────────────────
STATE_COLORS = {
    "ESTABLE":  (0.0, 1.0, 0.3),
    "SUAVE":    (1.0, 0.85, 0.0),
    "SACUDIDA": (1.0, 0.2, 0.2),
}

# ── Pygame + OpenGL setup ──────────────────────────────────────
pygame.init()
W, H = 900, 600
screen = pygame.display.set_mode((W, H), DOUBLEBUF | OPENGL | RESIZABLE)
pygame.display.set_caption("🎯 Radar + Acelerómetro + ML")

RADAR_W = 500
CUBE_W  = W - RADAR_W

pygame.font.init()
font_big = pygame.font.SysFont("monospace", 26, bold=True)
font_sm  = pygame.font.SysFont("monospace", 15)

# ── Serial ─────────────────────────────────────────────────────
try:
    ser = serial.Serial(PORT, BAUD, timeout=2)
    time.sleep(2); ser.flushInput()
except Exception as e:
    print(f"Error abriendo puerto serial: {e}")
    exit()

# ── Estado global ───────────────────────────────────────────────
# Usamos deque para mantener un tamaño máximo y evitar fugas de memoria
accel_buf = deque(maxlen=WINDOW) 
sweep_angle = 180.0
trail       = []
dist_points = []
ml_state    = "ESTABLE"
confidence  = 0.0
rot_x = rot_y = rot_z = 0.0
smooth_ax = smooth_ay = smooth_az = 0.0
clock = pygame.time.Clock()

# ── Cubo OpenGL ─────────────────────────────────────────────────
VERTS = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
         (-1,-1, 1),(1,-1, 1),(1,1, 1),(-1,1, 1)]
EDGES = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),
         (6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
FACES = [(0,1,2,3),(4,5,6,7),(0,1,5,4),
         (2,3,7,6),(0,3,7,4),(1,2,6,5)]

def draw_cube(color):
    r, g, b = color
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glBegin(GL_QUADS)
    for i, face in enumerate(FACES):
        shade = 0.4 + 0.1 * i
        glColor4f(r*shade, g*shade, b*shade, 0.6)
        for v in face:
            glVertex3fv(VERTS[v])
    glEnd()
    glBegin(GL_LINES)
    glColor4f(r, g, b, 1.0)
    for edge in EDGES:
        for v in edge:
            glVertex3fv(VERTS[v])
    glEnd()

def setup_3d(viewport_x):
    glViewport(viewport_x, 0, CUBE_W, H)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, CUBE_W / H, 0.1, 50)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0, 0, -5)
    glEnable(GL_DEPTH_TEST)

def render_cube(rx, ry, rz, color):
    setup_3d(RADAR_W)
    glClear(GL_DEPTH_BUFFER_BIT)
    glPushMatrix()
    glRotatef(rx, 1, 0, 0)
    glRotatef(ry, 0, 1, 0)
    glRotatef(rz, 0, 0, 1)
    draw_cube(color)
    glPopMatrix()

# ── Radar 2D ────────────────────────────────────────────────────
def draw_radar_surface(dist, state):
    global sweep_angle, trail, dist_points

    surf = pygame.Surface((RADAR_W, H), pygame.SRCALPHA)
    surf.fill((10, 15, 20))

    CX, CY = RADAR_W // 2, int(H * 0.75)
    MAX_R = min(RADAR_W // 2, int(H * 0.75)) - 30
    MAX_DIST = 200

    color_map = {
        "ESTABLE":  (0, 255, 80),
        "SUAVE":    (255, 220, 0),
        "SACUDIDA": (255, 60, 60),
    }
    radar_color = color_map.get(state, (0,255,80))

    for r in [MAX_R//4, MAX_R//2, 3*MAX_R//4, MAX_R]:
        pygame.draw.circle(surf, (0,50,20), (CX,CY), r, 1)
        d_lbl = font_sm.render(f"{int(MAX_DIST*r/MAX_R)}cm", True, (60,100,60))
        surf.blit(d_lbl, (CX+r+2, CY-12))

    for ang in range(0, 181, 30):
        rad = math.radians(ang)
        ex = int(CX + MAX_R * math.cos(rad))
        ey = int(CY - MAX_R * math.sin(rad))
        pygame.draw.line(surf, (0,40,15), (CX,CY), (ex,ey), 1)
        lbl = font_sm.render(f"{ang}°", True, (60,100,60))
        surf.blit(lbl, (ex-8, ey-8))

    pygame.draw.arc(surf, radar_color, (CX-MAX_R, CY-MAX_R, MAX_R*2, MAX_R*2), 0, math.pi, 2)

    trail.append((sweep_angle, 220))
    trail = [(a, alpha-7) for a, alpha in trail if alpha > 0]
    for angle, alpha in trail:
        rad = math.radians(angle)
        ex = int(CX + MAX_R * math.cos(rad))
        ey = int(CY - MAX_R * math.sin(rad))
        a = max(0, min(255, int(alpha)))
        color = (0, a, int(a*0.3))
        pygame.draw.line(surf, color, (CX,CY), (ex,ey), 2)

    rad = math.radians(sweep_angle)
    ex = int(CX + MAX_R * math.cos(rad))
    ey = int(CY - MAX_R * math.sin(rad))
    pygame.draw.line(surf, radar_color, (CX,CY), (ex,ey), 2)

    if dist and 0 < dist <= MAX_DIST:
        dist_points.append((sweep_angle, dist, 60))
    dist_points = [(a,d,life-1) for a,d,life in dist_points if life > 0]
    for angle, d, life in dist_points:
        r_px = int((d / MAX_DIST) * MAX_R)
        rad = math.radians(angle)
        px = int(CX + r_px * math.cos(rad))
        py = int(CY - r_px * math.sin(rad))
        alpha = int(255 * life / 60)
        c = tuple(int(x * alpha/255) for x in radar_color)
        pygame.draw.circle(surf, c, (px, py), 5)

    # HUD posicionado a la derecha de la superficie del radar
    hud_x_start = RADAR_W - 280
    pygame.draw.rect(surf, (15,15,25), (hud_x_start, 5, 270, 60), border_radius=8)
    state_txt = font_big.render(f"Estado: {state}", True, radar_color)
    surf.blit(state_txt, (hud_x_start + 10, 12))
    conf_txt = font_sm.render(f"Conf: {confidence:.1f}% Dist: {dist if dist and dist>0 else '--'}cm", True, (180,180,180))
    surf.blit(conf_txt, (hud_x_start + 10, 42))

    sweep_angle -= 3
    if sweep_angle < 0:
        sweep_angle = 180

    return surf

# ── Generar la textura UNA SOLA VEZ fuera del bucle ──────────────
radar_tex = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, radar_tex)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
glBindTexture(GL_TEXTURE_2D, 0)

# ── Loop principal ──────────────────────────────────────────────
running = True
current_dist = -1

while running:
    for e in pygame.event.get():
        if e.type == QUIT:
            running = False

    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            parts = line.split(",")
            if len(parts) == 4:
                ax = float(parts[0])
                ay = float(parts[1])
                az = float(parts[2])
                d  = float(parts[3])
                current_dist = d if d > 0 else current_dist

                # Suavizar lecturas (Indentación corregida)
                alpha = 0.15
                smooth_ax = alpha*ax + (1-alpha)*smooth_ax
                smooth_ay = alpha*ay + (1-alpha)*smooth_ay
                smooth_az = alpha*az + (1-alpha)*smooth_az

                tilt_x = math.degrees(math.asin(max(-1, min(1,  smooth_ax))))  
                tilt_y = math.degrees(math.asin(max(-1, min(1,  smooth_ay))))
                
                rot_x = tilt_x   
                rot_y =  -tilt_y   
                rot_z = 0         

                # ML (El buffer ahora está limitado automáticamente por deque)
                accel_buf.append([ax, ay, az])
                if len(accel_buf) == WINDOW:
                    arr = np.array(accel_buf)
                    axv, ayv, azv = arr[:,0], arr[:,1], arr[:,2]
                    mag = np.sqrt(axv**2 + ayv**2 + azv**2)
                    feats = [[
                        np.mean(mag), np.std(mag), np.max(mag)-np.min(mag),
                        np.std(axv), np.std(ayv), np.std(azv)
                    ]]
                    proba = model.predict_proba(feats)[0]
                    idx = np.argmax(proba)
                    ml_state  = model.classes_[idx]
                    confidence = proba[idx] * 100
    except Exception as e:
        print(f"Error procesando datos seriales o ML: {e}")

    # Renderizado General
    glViewport(0, 0, W, H)
    glClearColor(0.04, 0.06, 0.08, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Lado Derecho: Cubo 3D
    cube_color = STATE_COLORS.get(ml_state, (0.0,1.0,0.3))
    render_cube(rot_x, rot_y, rot_z, cube_color)

    # Lado Izquierdo: Radar 2D usando actualización de textura eficiente
    radar_surf = draw_radar_surface(current_dist, ml_state)
    radar_data = pygame.image.tostring(radar_surf, "RGBA", True)

    glViewport(0, 0, RADAR_W, H)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    glOrtho(0, RADAR_W, 0, H, -1, 1)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    # Actualizar la textura preexistente (sin fugas ni congelamientos)
    glBindTexture(GL_TEXTURE_2D, radar_tex)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, RADAR_W, H, 0, GL_RGBA, GL_UNSIGNED_BYTE, radar_data)
    glEnable(GL_TEXTURE_2D)
    
    glBegin(GL_QUADS)
    glTexCoord2f(0,0); glVertex2f(0,0)
    glTexCoord2f(1,0); glVertex2f(RADAR_W,0)
    glTexCoord2f(1,1); glVertex2f(RADAR_W,H)
    glTexCoord2f(0,1); glVertex2f(0,H)
    glEnd()
    
    glDisable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, 0) # Desvincular por seguridad

    pygame.display.flip()
    clock.tick(30)

ser.close()
pygame.quit()