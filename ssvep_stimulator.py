"""
SSVEP Stimulator — Precision Timing UI
With High-Speed OSC Feedback Listener
"""

import pygame
import time
import sys
import threading
from pythonosc import dispatcher, osc_server

# ──────────────────────── CONFIG ────────────────────────
WIDTH, HEIGHT = 900, 700
FPS = 120 # Increased for smoother timing checks

TARGETS = {
    "TOP":    {"freq": 15.0, "pos": (WIDTH//2 - 60, 60), "color": (255, 255, 255)},
    "LEFT":   {"freq": 10.0, "pos": (120, HEIGHT//2 - 60), "color": (255, 255, 255)},
    "RIGHT":  {"freq": 12.0, "pos": (WIDTH - 240, HEIGHT//2 - 60), "color": (255, 255, 255)},
    "BOTTOM": {"freq": 7.0,  "pos": (WIDTH//2 - 60, HEIGHT - 180), "color": (255, 255, 255)},
}

BOX_SIZE = 120
active_selection = "None"

def osc_worker():
    global active_selection
    def handler(address, target):
        global active_selection
        if target != active_selection:
            print(f"Selection changed to: {target}")
            active_selection = target

    disp = dispatcher.Dispatcher()
    disp.map("/select", handler)
    server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", 5240), disp)
    server.serve_forever()

def main():
    threading.Thread(target=osc_worker, daemon=True).start()

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MIND CONTROL — Stable SSVEP")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Outfit", 20, bold=True)
    big_font = pygame.font.SysFont("Outfit", 54, bold=True)

    start_ticks = pygame.time.get_ticks()
    
    running = True
    while running:
        # Use pygame ticks for more stable 0..1 timing
        current_ms = pygame.time.get_ticks() - start_ticks
        current_sec = current_ms / 1000.0
        
        screen.fill((15, 15, 15)) 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # ──────────────────────── DRAW TARGETS ────────────────────────
        for name, data in TARGETS.items():
            freq = data["freq"]
            # state = floor(t * 2 * f) % 2
            state = int(current_sec * 2 * freq) % 2
            
            is_active = (active_selection == name)
            
            # Highlight Logic
            if is_active:
                glow_val = int(127 + 127 * abs(time.time() % 1 - 0.5) * 2) # Pulse glow
                pygame.draw.rect(screen, (0, glow_val, 0), (data["pos"][0]-12, data["pos"][1]-12, BOX_SIZE+24, BOX_SIZE+24), 8)
                color = (200, 255, 200) if state == 1 else (0, 100, 0)
            else:
                color = (200, 200, 200) if state == 1 else (40, 40, 40)
            
            pygame.draw.rect(screen, color, (*data["pos"], BOX_SIZE, BOX_SIZE))
            
            # Label
            label = font.render(f"{name} ({freq}Hz)", True, (255, 255, 255) if is_active else (140, 140, 140))
            screen.blit(label, (data["pos"][0], data["pos"][1] - 30))

        # ──────────────────────── STATUS BAR ────────────────────────
        if active_selection != "None":
            msg = f"SELECTING: {active_selection}"
            status = big_font.render(msg, True, (0, 255, 0))
            screen.blit(status, (WIDTH//2 - 200, HEIGHT//2 - 30))
        else:
            info = font.render("Focus on a frequency to begin...", True, (100, 100, 100))
            screen.blit(info, (WIDTH//2 - 130, HEIGHT//2))
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
