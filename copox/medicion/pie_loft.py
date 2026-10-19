"""SENKU · pierna y pie como UNA pieza por secciones (Adán V46).

Hasta V45 el pie era una superficie implícita unida a la pierna con una mezcla suave: en el tobillo quedaba un aro (como
el borde de un calcetín) y el pie se leía como una caja alta con aletas. La auditoría artística de V45 pidió una sola
pieza por secciones que siga adan-pies-4-vistas: el tobillo es lo más ancho, el talón se bisela hacia la planta, el
empeine baja en una diagonal hasta los dedos y la planta no sobresale.

Aquí la superficie se arma directo, sin campo ni simplificado (sin rayas):
- La pierna son anillos de superelipse, igual a V42–V44 (aprobada): de `pierna` a `tobillo`, y dentro del short un 22 %
  más angosta.
- Bajo el tobillo, cada sección horizontal es un trapecio de esquinas redondeadas (vista desde arriba). Atrás va el talón,
  adelante el empeine; adentro el lado es recto, afuera se abre hacia los dedos. Su forma pasa de la de la pierna a la del
  pie en el primer cuarto: no hay unión, así que no hay aro.
- La planta es plana con un chaflán corto. Los dedos son cajas aparte, graduadas, con las puntas en diagonal y un poco
  caídas.
Todas las secciones tienen el mismo número de puntos, tomados por rayos desde su centro: los anillos se corresponden
y la malla es una rejilla limpia.
Marco de la pierna izquierda: x hacia afuera (+), frente +z, y arriba; centro de la pierna en (xc, zc).
"""
from __future__ import annotations

import numpy as np


def _ss(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def _superelipse(a, b, p, ang):
    c, s = np.cos(ang), np.sin(ang)
    r = 1.0 / ((np.abs(c) / a) ** p + (np.abs(s) / b) ** p) ** (1 / p)
    return np.stack([r * c, r * s], 1)


def _rayos_poligono(P, ang, centro):
    """Para cada ángulo, el punto del contorno convexo P (N,2 cerrado implícito) sobre el rayo desde centro."""
    out = np.zeros((len(ang), 2))
    A = P; B = np.roll(P, -1, 0)
    for k, t in enumerate(ang):
        d = np.array([np.cos(t), np.sin(t)])
        e = B - A; w = A - centro
        den = d[0] * e[:, 1] - d[1] * e[:, 0]
        ok = np.abs(den) > 1e-12
        s = np.where(ok, (w[:, 0] * e[:, 1] - w[:, 1] * e[:, 0]) / np.where(ok, den, 1), -1)   # distancia sobre el rayo
        u = np.where(ok, (w[:, 0] * d[1] - w[:, 1] * d[0]) / np.where(ok, den, 1), -1)         # posición en la arista
        m = ok & (s > 0) & (u >= -1e-9) & (u <= 1 + 1e-9)
        out[k] = centro + d * (s[m].max() if m.any() else 0.0)
    return out


def _redondeado(Q, r, n=10):
    """Polígono convexo Q (antihorario) con esquinas de radio r (suma de Minkowski del polígono encogido y un círculo)."""
    m = len(Q)
    N = []
    for i in range(m):
        e = Q[(i + 1) % m] - Q[i]
        N.append(np.array([e[1], -e[0]]) / np.linalg.norm(e))          # normal hacia afuera (antihorario)
    N = np.array(N)
    # polígono encogido: rectas desplazadas r hacia adentro, intersección de consecutivas
    Qi = []
    for i in range(m):
        n0, n1 = N[i - 1], N[i]
        p0, p1 = Q[i] - n0 * r, Q[i] - n1 * r
        A = np.array([[n0[0], n0[1]], [n1[0], n1[1]]])
        Qi.append(np.linalg.solve(A, [n0 @ p0, n1 @ p1]))
    pts = []
    for i in range(m):
        a0 = np.arctan2(N[i - 1][1], N[i - 1][0]); a1 = np.arctan2(N[i][1], N[i][0])
        while a1 < a0:
            a1 += 2 * np.pi
        for a in np.linspace(a0, a1, n):
            pts.append(Qi[i] + r * np.array([np.cos(a), np.sin(a)]))
    return np.array(pts)


class PiernaPieLoft:
    def __init__(self, xc, zc, y_arriba, y_tobillo, y_oculta, pierna=(0.049, 0.050), tobillo=(0.045, 0.046), p=2.8,
                 talon_z=-0.032, punta_z=0.150, largo_dedos=0.040, alto_dedos=0.022, abre_afuera=0.016,
                 abre_adentro=0.002, talon_angosta=0.12, maleolo=0.14, chaflan=0.0035,
                 dedos=(1.45, 1.0, 0.92, 0.82), hueco=0.0032, escalon=0.007, caida=0.3, segmentos=56):
        self.xc, self.zc = xc, zc
        self.y_arriba, self.y_t, self.y_oculta = y_arriba, y_tobillo, y_oculta
        self.pierna, self.tobillo, self.p = np.asarray(pierna), np.asarray(tobillo), p
        self.talon_z, self.punta_z, self.largo_dedos, self.alto_dedos = talon_z, punta_z, largo_dedos, alto_dedos
        self.abre_afuera, self.abre_adentro, self.talon_angosta, self.maleolo = abre_afuera, abre_adentro, talon_angosta, maleolo
        self.chaflan = chaflan
        self.dedos, self.hueco, self.escalon, self.caida = dedos, hueco, escalon, caida
        self.ang = np.linspace(-np.pi / 2, 1.5 * np.pi, segmentos, endpoint=False)   # empieza atrás al centro (−z)
        self.z_base = punta_z - largo_dedos                                           # cara frontal del pie (base de los dedos)

    # --- pierna -------------------------------------------------------------------------------------------
    def seccion_pierna(self, y):
        t = np.clip((self.y_arriba - y) / (self.y_arriba - self.y_t), 0, 1)
        a, b = self.pierna + (self.tobillo - self.pierna) * t
        o = _ss((y - self.y_oculta) / 0.012)                                          # dentro del short, más angosta
        a, b = a * (1 - 0.22 * o), b * (1 - 0.22 * o)
        P = _superelipse(a, b, self.p, self.ang)
        return np.c_[self.xc + P[:, 0], np.full(len(P), y), self.zc + P[:, 1]]

    # --- pie ----------------------------------------------------------------------------------------------
    def limites_pie(self, y):
        """Esquinas del trapecio (vista desde arriba) a la altura y, en el marco de la pierna (x, z relativos).
        Hoja de pies: el talón sigue la línea de atrás de la pierna (no sale); a media altura el pie se abre a los lados
        (lo más ancho) y abajo se bisela hacia la planta; el empeine es una diagonal del frente del tobillo a los dedos."""
        a, b = self.tobillo
        t = 1 - y / self.y_t                                                          # 0 tobillo, 1 planta
        abre = self.maleolo * np.exp(-((t - 0.55) / 0.28) ** 2)                       # el talón se abre a los lados
        bisel = 1 - self.talon_angosta * _ss((t - 0.78) / 0.22)                       # y se bisela hacia la planta
        zb = -b - 0.003 * np.sin(np.pi * np.clip(t, 0, 1)) + 0.003 * _ss((t - 0.8) / 0.2)
        s = np.clip((self.y_t - y) / (self.y_t - self.alto_dedos), 0, 1)
        zf = b + (self.z_base - self.zc - b) * s
        ah = a * (1 + abre) * bisel
        fin = -(a * (1 + 0.5 * abre) + self.abre_adentro * t) * (0.5 + 0.5 * bisel)   # adentro casi recto
        fout = a * (1 + 0.5 * abre) + self.abre_afuera * _ss(s)                       # afuera se abre hacia los dedos
        return np.array([[-ah, zb], [ah, zb], [fout, zf], [fin, zf]]), t

    def seccion_pie(self, y):
        Q, t = self.limites_pie(y)
        a, b = self.tobillo
        # Q en orden antihorario visto desde arriba con ejes (x, z): atrás-adentro, atrás-afuera, frente-afuera, frente-adentro
        r = 0.0055 * (1 - t) + 0.0035 * t                                            # aristas suaves pero planos marcados
        R = _redondeado(Q, r)
        c = Q.mean(0)
        Pq = _rayos_poligono(R, self.ang, c)
        Ps = _superelipse(a, b, self.p, self.ang)                                     # la sección de la pierna en el tobillo
        w = _ss(t / 0.15)
        P = Ps * (1 - w) + Pq * w
        return np.c_[self.xc + P[:, 0], np.full(len(P), y), self.zc + P[:, 1]]

    # --- malla --------------------------------------------------------------------------------------------
    def alturas(self):
        y1 = np.arange(self.y_arriba, self.y_oculta + 0.02, -0.008)
        y2 = np.arange(self.y_oculta + 0.02, self.y_t, -0.006)
        y3 = np.linspace(self.y_t, self.chaflan, 22)
        return np.unique(np.r_[y1, y2, y3])[::-1]

    def malla(self):
        ys = self.alturas()
        anillos = [self.seccion_pierna(y) if y > self.y_t else self.seccion_pie(y) for y in ys]
        # chaflán de la planta: último anillo metido `chaflan` hacia el centro, en y = 0
        u = anillos[-1].copy(); c = u.mean(0)
        dx = u[:, [0, 2]] - c[[0, 2]]
        dx /= np.maximum(np.linalg.norm(dx, axis=1, keepdims=True), 1e-9)
        u[:, [0, 2]] -= dx * self.chaflan; u[:, 1] = 0.0
        anillos.append(u)
        M = len(self.ang)
        V = np.vstack(anillos)
        T = []
        for i in range(len(anillos) - 1):
            for k in range(M):
                a, b = i * M + k, i * M + (k + 1) % M
                c_, d = a + M, b + M
                T += [[a, c_, b], [b, c_, d]]
        # tapas: arriba (escondida en el short) y planta (vértices propios: arista dura)
        n0 = len(V)
        V = np.vstack([V, anillos[0].mean(0)[None]])
        T += [[n0, (k + 1) % M, k] for k in range(M)]
        base = len(V)
        V = np.vstack([V, anillos[-1], anillos[-1].mean(0)[None]])
        cen = base + M
        T += [[cen, base + k, base + (k + 1) % M] for k in range(M)]
        T = np.array(T, np.int64)
        planta = np.zeros(len(V), bool); planta[base:] = True
        return V, T, planta

    def dedos_malla(self):
        """Cajas de los dedos (rejilla por secciones a lo largo de z), del lado de adentro (el gordo) hacia afuera."""
        Q, _ = self.limites_pie(0.0)
        x_in, x_out = self.xc + Q[3, 0], self.xc + Q[2, 0]
        w_tot = (x_out - x_in) - self.hueco * (len(self.dedos) - 1) - 0.004
        anchos = np.array(self.dedos) / sum(self.dedos) * w_tot
        x0 = x_in + 0.002
        Vs, Ts = [], []
        n = 0
        for i, w in enumerate(anchos):
            largo = self.largo_dedos * (1.0 if i == 0 else 0.92 - 0.06 * (i - 1))
            alto = self.alto_dedos * (1.1 if i == 0 else 0.9)
            z_fin = self.punta_z - self.escalon * i / max(len(anchos) - 1, 1)
            z_ini = self.z_base - 0.006
            zs = np.linspace(z_ini, z_fin - 0.0015, 7)
            anillos = []
            for z in zs:
                tz = np.clip((z - self.z_base) / max(z_fin - self.z_base, 1e-6), 0, 1)
                h = alto * (1 - self.caida * tz)
                r = min(0.0035, w / 3, h / 3)
                Qd = np.array([[x0 + w, 0.0], [x0 + w, h], [x0, h], [x0, 0.0]])            # (x, y), antihorario
                R = _redondeado(Qd, r, n=5)
                Pr = _rayos_poligono(R, np.linspace(0, 2 * np.pi, 24, endpoint=False), Qd.mean(0))
                anillos.append(np.c_[Pr[:, 0], Pr[:, 1], np.full(len(Pr), z)])
            # punta: un anillo más chico y una tapa
            M = 24
            V = np.vstack(anillos)
            T = []
            for k_ in range(len(anillos) - 1):
                for k in range(M):
                    a, b = k_ * M + k, k_ * M + (k + 1) % M
                    T += [[a, b, a + M], [b, b + M, a + M]]
            tip = anillos[-1].copy(); c = tip.mean(0)
            tip = c + (tip - c) * [0.75, 0.75, 1]; tip[:, 2] = z_fin
            V = np.vstack([V, tip, c[None] * [1, 1, 0] + [0, 0, z_fin]])
            L = len(anillos)
            for k in range(M):
                a, b = (L - 1) * M + k, (L - 1) * M + (k + 1) % M
                T += [[a, b, a + M], [b, b + M, a + M]]
            ct = len(V) - 1
            T += [[(L) * M + k, (L) * M + (k + 1) % M, ct] for k in range(M)]
            T += [[0 + (k + 1) % M, 0 + k, len(V) - 1] for k in range(0)]               # la base queda dentro del pie
            Vs.append(V); Ts.append(np.array(T, np.int64) + n); n += len(V)
            x0 += w + self.hueco
        return np.vstack(Vs), np.vstack(Ts)
