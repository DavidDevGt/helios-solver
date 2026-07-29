# 🛰️ helios-solver

> Documento de diseño (el **qué** y **por qué**). Para la vista general en
> inglés ver [`README.md`](README.md); para el **cómo** y el orden de
> ejecución ver [`PLAN.md`](PLAN.md).

> **Optimización de trayectorias espaciales de bajo empuje, acelerada por GPU.**
> Objetivo de la primera milestone: una espiral Tierra→Marte optimizada por mi propio código, renderizada como una imagen que se explica sola.

---

## 1. Visión

Los motores de propulsión eléctrica (iónicos, efecto Hall) no hacen maniobras impulsivas: empujan de forma continua durante meses, con milinewtons de fuerza. La trayectoria óptima deja de ser una elipse de Hohmann y se convierte en una **espiral continua** cuyo perfil de empuje hay que descubrir resolviendo un problema de control óptimo no convexo.

Este es un problema abierto de *software*, no de física: las ecuaciones se conocen desde hace un siglo, pero encontrar la mejor trayectoria es computacionalmente brutal. Las competencias GTOC (Global Trajectory Optimisation Competition, la "olimpiada" de mecánica orbital organizada por ESA/JPL) las ganan los equipos con mejor ingeniería de optimización, paralelización y cómputo.

**Tesis del proyecto:** un ingeniero de software con GPUs propias puede competir en este espacio construyendo mejores solvers — y en particular, usando *surrogates* neuronales para evaluar tramos de trayectoria en microsegundos en lugar de integrarlos numéricamente.

## 2. El problema, formalmente

Minimizar el consumo de propelente (o el tiempo de vuelo) de una nave con empuje continuo limitado que va de la órbita de la Tierra a la órbita de Marte:

```
Estado:      x(t) = [r, v, m]           (posición ℝ³, velocidad ℝ³, masa)
Control:     u(t) = [T, α, β]           (magnitud de empuje y dirección)
Dinámica:    ṙ = v
             v̇ = -μ r/|r|³ + (T/m) û    (gravedad solar + empuje)
             ṁ = -T/(Isp · g₀)          (consumo de propelente)
Restricciones:
             0 ≤ T ≤ T_max              (empuje acotado)
             x(t₀) = estado de la Tierra en t₀
             x(t_f) = estado de Marte en t_f     (rendezvous)
Objetivo:    max m(t_f)                 (llegar con la máxima masa posible)
```

Por qué es difícil:
- **No convexo**: miles de mínimos locales (¿cuántas revoluciones da la espiral? ¿1.5? ¿2.5? cada una es una "cuenca" distinta).
- **Sensible**: pequeños cambios en el control temprano cambian todo el final (dinámica caótica a largo plazo).
- **Caro de evaluar**: cada trayectoria candidata requiere integrar EDOs durante cientos de días simulados.
- **Ventanas de lanzamiento**: t₀ y t_f también son variables de decisión (las efemérides de los planetas entran al problema).

## 3. MVP — "la imagen que se explica sola"

Una sola imagen (matplotlib, vista polar del plano de la eclíptica):

- Órbitas de la Tierra y Marte en gris.
- La espiral de transferencia en color, con el **vector de empuje dibujado como flechitas** a lo largo de la trayectoria (se ve dónde el optimizador decide empujar y dónde hace coasting).
- Anotaciones: fecha de salida, fecha de llegada, Δv efectivo, masa final / masa inicial, tiempo de vuelo.

Criterio de éxito del MVP: la trayectoria **converge a rendezvous real** (posición Y velocidad de Marte, no solo cruzar su órbita) con un propelente consumido consistente con la literatura (~
para un caso tipo: Isp 3000 s, T_max ~0.5 N, nave de 1000 kg → masa final ≳ 80%).

## 4. Fases

### Fase 0 — Setup y validación (semana 1)
- [ ] Repo, entorno (`uv` o `conda`), CI con tests desde el día 1.
- [ ] Instalar `pykep` (ESA). Alternativa pura-Python si da guerra compilando: `poliastro` + efemérides de `jplephem`.
- [ ] **Sanity check**: reproducir una transferencia de Hohmann Tierra-Marte impulsiva y comparar Δv contra el valor de libro (~5.6 km/s desde órbitas). Si esto no cuadra, nada de lo que siga vale.
- [ ] Efemérides reales (SPICE kernels DE440 o las built-in de pykep).

### Fase 1 — Baseline con métodos clásicos (semanas 2-4)
- [ ] Modelo dinámico propio: integrador RK (usar `scipy.integrate.solve_ivp` con DOP853, o heyoka/Taylor si se necesita precisión).
- [ ] **Transcripción directa**: discretizar el control en N segmentos (método de Sims-Flanagan, el estándar de la industria — pykep lo trae como `sims_flanagan`).
- [ ] Resolver con NLP: `scipy.optimize.minimize` (SLSQP) primero; migrar a **IPOPT** (via `cyipopt`) cuando SLSQP se quede corto.
- [ ] Multi-start: lanzar cientos de optimizaciones desde semillas aleatorias en paralelo (`multiprocessing` / `joblib`) para escapar de mínimos locales. Aquí ya se usa todo el CPU del homelab.
- [ ] 🎯 **Milestone: LA IMAGEN.** Espiral convergida + flechas de empuje + métricas.

### Fase 2 — Búsqueda global seria (semanas 5-8)
- [ ] Integrar `pygmo` (de los mismos autores de pykep): evolución diferencial, CMA-ES, self-adaptive DE, con **archipiélagos en paralelo** (island model — mapea directo a múltiples cores/máquinas).
- [ ] Ampliar el problema: fecha de salida libre dentro de una ventana de 2 años → el optimizador descubre solo la ventana de lanzamiento.
- [ ] Benchmark interno: tabla de (método × tiempo de cómputo × calidad de solución). Esto es contenido publicable en el README.

### Fase 3 — El surrogate neuronal (la contribución original) (semanas 9-16)
La idea: en la búsqueda global, el 99% del tiempo se va integrando EDOs de candidatos malos. Entrenar una red que **prediga el costo/factibilidad de un tramo de trayectoria sin integrarlo**:

- [ ] **Generación de datos**: pipeline que integra millones de tramos aleatorios (estado inicial, control, duración → estado final, masa consumida). Vergonzosamente paralelo → GPU/cluster del homelab. Guardar en Parquet.
- [ ] **Modelo**: MLP modesto primero (entrada: ~14 floats, salida: 7). PyTorch. Entrenar en la RTX local. Medir error vs. integrador real.
- [ ] **Integración al solver**: usar el surrogate como filtro barato en la búsqueda global (descartar el 95% de candidatos), integrar numéricamente solo los prometedores. Arquitectura de dos niveles: *screen with the net, verify with the integrator*.
- [ ] Medir el speedup real end-to-end. Si es >10x con igual calidad de solución → **esto es un paper / blog post técnico serio**.

### Fase 4 — GTOC como campo de pruebas (en adelante)
- [ ] Reproducir un problema GTOC pasado (GTOC1 es el clásico de entrada; los enunciados y soluciones ganadoras están publicados en el portal de ESA).
- [ ] Comparar mi mejor solución contra el leaderboard histórico.
- [ ] Participar en la próxima edición real.

## 5. Stack

| Capa | Herramienta | Por qué |
|---|---|---|
| Mecánica orbital | `pykep` / `poliastro` | Efemérides, Lambert, Sims-Flanagan ya resueltos |
| Integración EDO | `scipy` (DOP853) → `heyoka` | Precisión y velocidad cuando importe |
| Optimización local | SLSQP → IPOPT (`cyipopt`) | Estándar para NLP con restricciones |
| Búsqueda global | `pygmo` (islands) | Paralelización nativa, mismo ecosistema ESA |
| Surrogate | PyTorch + Parquet + `polars` | Entrena en la GPU local |
| Visualización | matplotlib (estático), plotly (interactivo) | La imagen es el producto |
| Infra | Docker, CI (GitHub Actions), tests con `pytest` | Ventaja competitiva de venir de QA |

## 6. Estructura del repo

```
helios-solver/
├── IDEA.md                  # este documento
├── src/helios/
│   ├── dynamics.py          # EDOs: gravedad + empuje + masa
│   ├── ephemeris.py         # posiciones de Tierra/Marte
│   ├── transcription.py     # Sims-Flanagan / colocación
│   ├── solvers/
│   │   ├── local.py         # SLSQP / IPOPT wrappers
│   │   └── global_.py       # pygmo archipelago
│   ├── surrogate/
│   │   ├── datagen.py       # generación masiva de tramos
│   │   ├── model.py         # MLP
│   │   └── train.py
│   └── viz.py               # LA imagen
├── tests/
│   ├── test_hohmann.py      # validación contra valores de libro
│   └── test_dynamics.py     # conservación de energía sin empuje
├── notebooks/
├── benchmarks/
└── data/                    # parquets del surrogate (gitignored)
```

## 7. Validación (el enfoque QA aplicado a física)

Los proyectos científicos fallan silenciosamente: un signo mal puesto produce trayectorias bonitas y falsas. Tests no negociables:

1. **Conservación de energía**: sin empuje, la energía orbital debe conservarse a ~1e-10 relativo en una integración de 1 año.
2. **Hohmann analítico**: el caso impulsivo debe coincidir con la fórmula cerrada.
3. **Round-trip de efemérides**: posición de la Tierra hoy vs. Horizons de JPL, error < km.
4. **Consistencia del surrogate**: error del modelo medido continuamente contra el integrador en un held-out set; el solver nunca acepta una solución final que no haya sido verificada por integración real.
5. **Reproducibilidad**: semillas fijas, resultados en CI.

## 8. Métricas de éxito

| Milestone | Métrica | Cuándo |
|---|---|---|
| M1 | Imagen de espiral convergida con rendezvous real | Semana 4 |
| M2 | Ventana de lanzamiento descubierta automáticamente | Semana 8 |
| M3 | Surrogate con >10x speedup end-to-end verificado | Semana 16 |
| M4 | Solución a un GTOC pasado dentro del top-50% histórico | Mes 6 |

## 9. Riesgos y mitigaciones

- **pykep no compila / wheels rotos** → fallback a poliastro puro-Python; la física es la misma.
- **El optimizador no converge nunca** → empezar con el problema *fácil*: órbitas circulares coplanares, sin efemérides reales, luego añadir realismo capa por capa.
- **El surrogate no generaliza** → reducir el dominio (normalizar estados a elementos orbitales, entrenar por regiones); en el peor caso el proyecto sigue siendo valioso hasta la Fase 2.
- **Scope creep** → la Fase 1 termina en LA IMAGEN. Nada de Júpiter, flybys ni 3 cuerpos hasta M3.

## 10. Por qué yo

- El cuello de botella del campo es ingeniería de software (paralelización, pipelines de datos, testing), no física nueva.
- Tengo GPU local para el surrogate y experiencia montando CI/CD — la mayoría de código académico no tiene ni tests.
- El stack (Python + C++ + optimización + GPU) es exactamente el portafolio que apunta a infraestructura de IA.
- GTOC ofrece un leaderboard objetivo y público: no hay que convencer a nadie, solo subir el número.

---

*"Las ecuaciones se conocen desde Tsiolkovsky. Lo que falta son mejores solvers."*