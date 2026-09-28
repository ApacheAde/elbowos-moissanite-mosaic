#!/usr/bin/env python3
"""Moissanite Mosaic — neon falling 2x2 match arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "MOISSANITE MOSAIC"
HANDLE = "x.com/ElbowOS"
COLS, ROWS = 6, 10
CELL = 132
OX = (W - COLS * CELL) // 2
OY = 360
VOID = (6, 10, 18)
WELL = (10, 18, 32)
CYAN = (48, 240, 255)
MAG = (255, 64, 168)
LIME = (168, 255, 72)
ICE = (236, 248, 255)
AMETH = (176, 96, 255)
GOLD = (255, 214, 96)
SLAG = (255, 72, 96)
PAL = (CYAN, MAG, LIME, AMETH)


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=6):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 62)
        self.font_md = pygame.font.Font(None, 42)
        self.font_sm = pygame.font.Font(None, 30)
        self.reset()

    def reset(self) -> None:
        self.grid = [[None] * COLS for _ in range(ROWS)]
        self.score = 0
        self.combo = 0
        self.pulse = 0.0
        self.fall = 0.0
        self.over = False
        self.cool = 0.0
        self.sparks: list[Spark] = []
        self.stars = [(random.randrange(W), random.randrange(H), random.uniform(0.3, 2.0)) for _ in range(80)]
        self.piece = self._new()
        self.nextp = self._new()

    def _new(self):
        return {"c": random.randint(0, COLS - 2), "r": -2, "g": [[random.choice(PAL) for _ in range(2)] for _ in range(2)]}

    def burst(self, x, y, col, n=12) -> None:
        for _ in range(n):
            a = random.random() * 6.2832
            s = random.uniform(80, 380)
            self.sparks.append(Spark(x, y, s * math.cos(a), s * math.sin(a),
                                     random.uniform(0.2, 0.5), col, random.randint(3, 8)))

    def _cell_ok(self, c, r, ignore=None) -> bool:
        if c < 0 or c >= COLS or r >= ROWS:
            return False
        if r < 0:
            return True
        return self.grid[r][c] is None

    def _fits(self, p, dc=0, dr=0) -> bool:
        for i in range(2):
            for j in range(2):
                if not self._cell_ok(p["c"] + j + dc, p["r"] + i + dr):
                    return False
        return True

    def _lock(self) -> None:
        p = self.piece
        for i in range(2):
            for j in range(2):
                r, c = p["r"] + i, p["c"] + j
                if 0 <= r < ROWS and 0 <= c < COLS:
                    self.grid[r][c] = p["g"][i][j]
                    cx = OX + c * CELL + CELL // 2
                    cy = OY + r * CELL + CELL // 2
                    self.burst(cx, cy, p["g"][i][j], 8)
        self._clear()
        self.piece = self.nextp
        self.nextp = self._new()
        if not self._fits(self.piece):
            self.over = True
            self.cool = 1.6

    def _clear(self) -> None:
        hit = True
        chain = 0
        while hit:
            hit = False
            mark = [[False] * COLS for _ in range(ROWS)]
            for r in range(ROWS - 1):
                for c in range(COLS - 1):
                    a = self.grid[r][c]
                    if a and a == self.grid[r][c + 1] == self.grid[r + 1][c] == self.grid[r + 1][c + 1]:
                        mark[r][c] = mark[r][c + 1] = mark[r + 1][c] = mark[r + 1][c + 1] = True
                        hit = True
            if not hit:
                break
            n = 0
            for r in range(ROWS):
                for c in range(COLS):
                    if mark[r][c]:
                        col = self.grid[r][c]
                        self.grid[r][c] = None
                        n += 1
                        self.burst(OX + c * CELL + CELL // 2, OY + r * CELL + CELL // 2, col or ICE, 10)
            for c in range(COLS):
                stack = [self.grid[r][c] for r in range(ROWS) if self.grid[r][c] is not None]
                for r in range(ROWS):
                    self.grid[r][c] = None
                for i, val in enumerate(reversed(stack)):
                    self.grid[ROWS - 1 - i][c] = val
            chain += 1
            self.combo += 1
            self.score += n * (12 + chain * 8)

    def _cycle(self) -> None:
        g = self.piece["g"]
        self.piece["g"] = [[g[1][0], g[0][0]], [g[1][1], g[0][1]]]

    def autoplay(self) -> None:
        if self.over:
            if self.cool <= 0:
                self.reset()
            return
        p = self.piece
        best, bc, brot = -1, p["c"], 0
        saved = [row[:] for row in p["g"]]
        for rot in range(4):
            for c in range(COLS - 1):
                test = {"c": c, "r": p["r"], "g": [row[:] for row in p["g"]]}
                if not self._fits(test):
                    continue
                score = 0
                for i in range(2):
                    for j in range(2):
                        rr, cc = p["r"] + i, c + j
                        col = p["g"][i][j]
                        for dr, dc in ((1, 0), (0, 1), (0, -1), (-1, 0), (1, 1), (1, -1)):
                            r2, c2 = rr + dr, cc + dc
                            if 0 <= r2 < ROWS and 0 <= c2 < COLS and self.grid[r2][c2] == col:
                                score += 3
                        score += (ROWS - max(0, rr)) * 0.15
                if score > best:
                    best, bc, brot = score, c, rot
            self._cycle()
        p["g"] = saved
        for _ in range(brot):
            self._cycle()
        if p["c"] < bc and self._fits(p, dc=1):
            p["c"] += 1
        elif p["c"] > bc and self._fits(p, dc=-1):
            p["c"] -= 1
        elif p["c"] == bc and random.random() < 0.35 and self._fits(p, dr=1):
            p["r"] += 1

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.cool = max(0.0, self.cool - dt)
        if self.record:
            self.autoplay()
        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            alive.append(sp)
        self.sparks = alive
        if self.over:
            return
        speed = 0.55 - min(0.28, self.score * 0.0004)
        self.fall += dt
        if self.fall >= speed:
            self.fall = 0.0
            if self._fits(self.piece, dr=1):
                self.piece["r"] += 1
            else:
                self._lock()

    def handle(self, ev) -> None:
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key == pygame.K_r:
            self.reset()
        if self.over:
            return
        if ev.key in (pygame.K_LEFT, pygame.K_a) and self._fits(self.piece, dc=-1):
            self.piece["c"] -= 1
        if ev.key in (pygame.K_RIGHT, pygame.K_d) and self._fits(self.piece, dc=1):
            self.piece["c"] += 1
        if ev.key in (pygame.K_DOWN, pygame.K_s) and self._fits(self.piece, dr=1):
            self.piece["r"] += 1
        if ev.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
            self._cycle()

    def _gem(self, s, x, y, col, glow=False) -> None:
        pad = 10
        box = pygame.Rect(x + pad, y + pad, CELL - pad * 2, CELL - pad * 2)
        if glow:
            pygame.draw.rect(s, col, box.inflate(10, 10), border_radius=18)
        pygame.draw.rect(s, col, box, border_radius=16)
        hi = tuple(min(255, c + 70) for c in col)
        pygame.draw.rect(s, hi, box.inflate(-28, -48).move(-8, -10), border_radius=8)
        pygame.draw.rect(s, ICE, box, 2, border_radius=16)

    def draw(self, s: pygame.Surface) -> None:
        s.fill(VOID)
        for sx, sy, sc in self.stars:
            tw = 10 + int(12 * math.sin(self.pulse * 2 + sx))
            pygame.draw.circle(s, (18 + tw, 28 + tw, 46 + tw), (sx, int((sy + self.pulse * 18 * sc) % H)), 1 if sc < 1 else 2)
        pygame.draw.rect(s, WELL, (OX - 18, OY - 18, COLS * CELL + 36, ROWS * CELL + 36), border_radius=28)
        pygame.draw.rect(s, CYAN, (OX - 18, OY - 18, COLS * CELL + 36, ROWS * CELL + 36), 3, border_radius=28)
        for r in range(ROWS):
            for c in range(COLS):
                x, y = OX + c * CELL, OY + r * CELL
                pygame.draw.rect(s, (16, 28, 44), (x + 4, y + 4, CELL - 8, CELL - 8), 1, border_radius=12)
                if self.grid[r][c]:
                    self._gem(s, x, y, self.grid[r][c])
        p = self.piece
        if not self.over:
            flick = 0.55 + 0.45 * math.sin(self.pulse * 10)
            for i in range(2):
                for j in range(2):
                    rr, cc = p["r"] + i, p["c"] + j
                    if rr < 0:
                        continue
                    x, y = OX + cc * CELL, OY + rr * CELL
                    col = tuple(int(v * flick) for v in p["g"][i][j])
                    self._gem(s, x, y, col, glow=True)
        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x), int(sp.y)), max(1, int(sp.r * sp.life * 2)))
        title = self.font_lg.render(TITLE, True, ICE)
        s.blit(title, title.get_rect(center=(W // 2, 72)))
        handle = self.font_sm.render(HANDLE, True, CYAN)
        s.blit(handle, handle.get_rect(center=(W // 2, 122)))
        meta = self.font_md.render(f"SCORE  {self.score}    COMBO  {self.combo}", True, LIME)
        s.blit(meta, meta.get_rect(center=(W // 2, 178)))
        nxt = self.font_sm.render("NEXT", True, AMETH)
        s.blit(nxt, (OX, 248))
        for i in range(2):
            for j in range(2):
                col = self.nextp["g"][i][j]
                box = pygame.Rect(OX + 92 + j * 46, 228 + i * 46, 40, 40)
                pygame.draw.rect(s, col, box, border_radius=8)
                pygame.draw.rect(s, ICE, box, 1, border_radius=8)
        hint = self.font_sm.render("A/D slide   W cycle   S drop   R reset", True, ICE)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 46)))
        if self.over:
            over = self.font_md.render("THE LATTICE SHATTERED", True, SLAG)
            s.blit(over, over.get_rect(center=(W // 2, 280)))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/MOISSANITE_MOSAIC_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
