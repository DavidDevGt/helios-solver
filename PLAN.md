# 📋 PLAN.md — helios-solver

> Para la vista general en inglés ver [`README.md`](README.md).

> `IDEA.md` responde **qué** y **por qué**. Este documento responde **cómo**, **en qué orden** y **cómo sé que ya terminé**.
> Regla de oro: ninguna tarea entra aquí si no tiene entregable verificable. Si no se puede testear o graficar, no es una tarea, es un deseo.

**Estado:** Fase 0 — no iniciada
**Última actualización:** _(fecha)_
**Milestone activo:** M1 — La Imagen (espiral convergida con rendezvous real)

---

## 0. Cómo se usa este documento

- Las tareas tienen ID estable (`T-1.3`). No se renumeran; si una muere, se marca ~~tachada~~ con el motivo.
- Cada tarea tiene **entregable** (archivo/commit) y **criterio de aceptación** (cómo se verifica).
- Entre fases hay **gates**: si el gate no pasa, no se abre la fase siguiente. Esto es lo que evita el scope creep.
- Las decisiones abiertas viven en §7 (registro de decisiones). Se cierran con una línea, no con una reunión conmigo mismo.
- Cadencia realista de proyecto personal: **~8–10 h/semana**. Las semanas del IDEA.md se leen como *unidades de esfuerzo*, no como calendario.

---

## 1. Decisiones a cerrar antes de escribir código

Estas cuatro bloquean todo lo demás. Objetivo: cerrarlas en la primera sesión, sin investigación infinita.

| ID | Decisión | Opciones | Recomendación de arranque | Bloquea |
|---|---|---|---|---|
| D-1 | Librería de mecánica orbital | `pykep` / `poliastro` (hoy mantenido como `hapsira`) / propio | **pykep**, con timebox de 60 min de instalación. Si no compila, `hapsira` + `jplephem` y seguir | T-0.2, T-0.4 |
| D-2 | Gestor de entorno | `uv` / `conda` / `pixi` | **uv** si D-1 resuelve por wheel; **conda/pixi** si hay que compilar pykep o cyipopt | T-0.1 |
| D-3 | Unidades internas | SI (m, kg, s) / canónicas adimensionales (AU, TU) | **Canónicas adimensionales** en el solver, SI solo en la frontera (I/O y viz). El optimizador se comporta mucho mejor con magnitudes ~1 | T-1.1, todo el solver |
| D-4 | Alcance del MVP físico | 2D coplanar circular / 3D con efemérides reales | **Empezar 2D coplanar circular** y subir realismo por capas (§3, escalera de realismo) | T-1.2 en adelante |

> Nota: la mayoría de fracasos en este tipo de proyecto no son de física, son de **escalado numérico**. D-3 es la decisión de mayor impacto y la más fácil de subestimar.

---

## 2. Fase 0 — Setup y validación

**Objetivo del gate:** el entorno es reproducible y la física base está verificada contra valores cerrados. Cero optimización todavía.

| ID | Tarea | Entregable | Criterio de aceptación |
|---|---|---|---|
| T-0.1 | Repo + entorno + estructura de `src/helios` según §6 de IDEA.md | `pyproject.toml`, lockfile, árbol de paquetes | `git clone` + un comando → tests corren en máquina limpia |
| T-0.2 | Instalar y humear la librería orbital (D-1) | `notebooks/00_smoke.ipynb` | Posición de la Tierra para una fecha conocida se imprime sin error |
| T-0.3 | CI en GitHub Actions: lint + tests + cobertura | `.github/workflows/ci.yml` | PR con test roto queda en rojo. Verificado a propósito con un commit que falla |
| T-0.4 | Módulo `ephemeris.py`: estado de Tierra y Marte en función de la fecha | `src/helios/ephemeris.py` | Cubierto por T-0.7 |
| T-0.5 | Test de Hohmann heliocéntrico impulsivo | `tests/test_hohmann.py` | Δv de partida ≈ 2.94 km/s, de llegada ≈ 2.65 km/s, total ≈ 5.6 km/s, tolerancia 1 %. Tiempo de transferencia ≈ 259 días |
| T-0.6 | Test de conservación de energía sin empuje | `tests/test_dynamics.py` | Deriva relativa de energía < 1e-10 en 1 año simulado con DOP853 (`rtol=1e-12`) |
| T-0.7 | Test de efemérides contra JPL Horizons | `tests/test_ephemeris.py` + CSV de referencia | Error de posición < 1000 km vs. valores de Horizons *congelados en un fixture* (sin llamadas de red en CI) |
| T-0.8 | Fijar semillas y determinismo | `src/helios/rng.py` | Dos corridas del mismo test dan bit-idénticos los mismos números |

**🚦 Gate 0 → 1:** T-0.5, T-0.6 y T-0.7 en verde en CI.
Si el Δv de Hohmann no cuadra al 1 %, **hay un bug de unidades o de signo**. Ninguna trayectoria bonita más adelante compensa esto: es exactamente el fallo silencioso que describe §7 del IDEA.md.

---

## 3. Fase 1 — Baseline clásico (camino a M1)

**Objetivo del gate:** LA IMAGEN, con rendezvous real y verificada por integración.

### Escalera de realismo (D-4)
Cada escalón es un commit con su propia imagen guardada en `benchmarks/`. No se sube un escalón hasta que el anterior converge.

1. **E1** — 2D, órbitas circulares coplanares, empuje constante, tiempo de vuelo fijo.
2. **E2** — 2D, dirección de empuje variable (control discretizado), tiempo fijo.
3. **E3** — 2D, tiempo de vuelo libre.
4. **E4** — 3D con efemérides reales, fechas fijas.
5. **E5** — 3D, rendezvous completo (posición **y** velocidad) → M1.

| ID | Tarea | Entregable | Criterio de aceptación |
|---|---|---|---|
| T-1.1 | `dynamics.py`: EDO en unidades canónicas (r, v, m) con empuje | módulo + tests | Con `T=0` reproduce T-0.6; con empuje tangencial constante la energía crece monótona |
| T-1.2 | Transcripción Sims-Flanagan propia, N segmentos, matching en el punto medio | `transcription.py` | Con la solución de Hohmann como entrada, el defecto de matching es ~0 |
| T-1.3 | Función objetivo + restricciones para SLSQP | `solvers/local.py` | Gradientes por diferencias finitas validados contra derivada analítica en un caso trivial |
| T-1.4 | Resolver E1 y E2 | imágenes en `benchmarks/` | Converge desde al menos 3 semillas distintas al mismo óptimo (±1 % en masa final) |
| T-1.5 | Multi-start paralelo con `joblib` | `solvers/multistart.py` | 200 semillas en paralelo, reporte de tasa de convergencia por semilla |
| T-1.6 | Migrar a IPOPT (`cyipopt`) si SLSQP se atasca | flag `--solver=ipopt` | Mismo óptimo que SLSQP en E2, o mejor, en menos iteraciones |
| T-1.7 | Subir a E4/E5 con efemérides reales | commits por escalón | Restricción de rendezvous satisfecha: \|Δr\| < 1000 km y \|Δv\| < 1 m/s |
| T-1.8 | 🎯 **`viz.py` — LA IMAGEN** | `benchmarks/m1_spiral.png` | Órbitas en gris, espiral en color, flechas de empuje escaladas por magnitud, anotaciones: fechas, Δv efectivo, m_f/m_0, TOF |
| T-1.9 | Verificación final por integración de alta precisión | `tests/test_m1_solution.py` | La solución del optimizador, re-integrada con `rtol=1e-12`, cumple el rendezvous. **Ninguna solución se publica sin este paso** |

**Caso de referencia a fijar en Fase 1** (el IDEA.md dejó el número cortado — cerrarlo aquí):
Isp = 3000 s, T_max = 0.5 N, m_0 = 1000 kg, TOF ≈ 300–400 días → **m_f ≳ 800 kg (≥ 80 %)**.
Cálculo de cordura con Tsiolkovsky: si Δv efectivo del bajo empuje ≈ 5.5–6.5 km/s con Isp 3000 s (v_e ≈ 29.4 km/s), entonces m_f/m_0 = exp(−Δv/v_e) ≈ 0.80–0.83. **Consistente.** Si el resultado sale muy por encima de 0.85, sospechar que el rendezvous no es real (probablemente solo cruza la órbita). Si sale por debajo de 0.70, sospechar control ineficiente o demasiadas revoluciones.

**🚦 Gate 1 → 2:** `m1_spiral.png` existe, T-1.9 en verde, y el README muestra la imagen.

---

## 4. Fase 2 — Búsqueda global

| ID | Tarea | Entregable | Criterio de aceptación |
|---|---|---|---|
| T-2.1 | Envolver el problema como `pygmo.problem` | `solvers/global_.py` | El mismo problema corre en SLSQP local y en pygmo sin duplicar código |
| T-2.2 | Archipiélago: DE, self-adaptive DE, CMA-ES con migración | config en YAML | Encuentra el óptimo de E2 sin semilla informada |
| T-2.3 | Liberar fecha de salida en ventana de 2 años | parámetro `--launch-window` | El optimizador redescubre por su cuenta la ventana sinódica (~26 meses) |
| T-2.4 | Arnés de benchmarks reproducible | `benchmarks/run_all.py` + tabla en README | Tabla (método × wall-clock × mejor masa final × tasa de éxito), regenerable con un comando |
| T-2.5 | Perfilado: ¿dónde se va el tiempo? | `benchmarks/profile.md` | Cuantificado el % del tiempo en integración de EDOs — **este número justifica la Fase 3** |

**🚦 Gate 2 → 3:** T-2.5 demuestra que >70 % del wall-clock se gasta integrando candidatos.
Si resulta que no, el surrogate no es la optimización correcta y hay que replantear la Fase 3 (optimizar la transcripción o el NLP en su lugar). Esta es una decisión basada en medición, no en el plan original.

---

## 5. Fase 3 — Surrogate neuronal

| ID | Tarea | Entregable | Criterio de aceptación |
|---|---|---|---|
| T-3.1 | Definir esquema de datos y normalización de entradas | `surrogate/schema.py` | Estados en elementos orbitales normalizados, no en cartesianas crudas (mejor generalización) |
| T-3.2 | Pipeline de generación masiva de tramos | `surrogate/datagen.py`, Parquet | ≥1e6 tramos, con partición train/val/test **por región del espacio de estados**, no aleatoria |
| T-3.3 | MLP baseline en PyTorch | `surrogate/model.py`, `train.py` | Error mediano < 1 % en masa consumida; reportar también el p99, no solo la media |
| T-3.4 | Integración de dos niveles en la búsqueda global | flag `--surrogate` | Descarta ≥90 % de candidatos con ≤5 % de falsos negativos sobre los buenos |
| T-3.5 | Medición end-to-end del speedup | `benchmarks/surrogate_speedup.md` | Speedup con **igual o mejor** calidad de solución. Si <2x, se documenta el resultado negativo y se cierra la fase |
| T-3.6 | Blog post / paper si T-3.5 > 10x | `docs/writeup.md` | Reproducible por un tercero desde el repo |

**Regla dura:** el surrogate nunca valida una solución final. Filtra; el integrador decide.

---

## 6. Fase 4 — GTOC

| ID | Tarea | Criterio de aceptación |
|---|---|---|
| T-4.1 | Implementar el enunciado de GTOC1 como problema en el framework | La función objetivo publicada se reproduce sobre una solución conocida |
| T-4.2 | Correr el pipeline completo y comparar con el leaderboard histórico | Resultado dentro del top-50 % |
| T-4.3 | Postmortem: qué faltó vs. los ganadores | Documento con brechas concretas |

---

## 7. Registro de decisiones

| # | Fecha | Decisión | Motivo | Estado |
|---|---|---|---|---|
| 1 | — | D-1: librería orbital | — | abierta |
| 2 | — | D-2: gestor de entorno | — | abierta |
| 3 | — | D-3: unidades canónicas | Condicionamiento numérico del NLP | propuesta |
| 4 | — | D-4: escalera de realismo | Aislar bugs de física de bugs de optimización | propuesta |

---

## 8. Definition of Done (aplica a toda tarea)

- [ ] Tests nuevos pasan y CI en verde.
- [ ] Sin números mágicos: constantes físicas en `constants.py` con fuente citada.
- [ ] Toda función que devuelve una cantidad física documenta **unidades** en el docstring.
- [ ] Si genera una figura, la figura queda versionada en `benchmarks/`.
- [ ] Si cambia un resultado numérico del README, el README se actualiza en el mismo commit.

---

## 9. Riesgos: disparador → acción

| Riesgo | Disparador observable | Acción inmediata |
|---|---|---|
| pykep no instala | 60 min sin wheel funcional | Cambiar a `hapsira`/`jplephem`; anotar D-1 y seguir |
| El NLP no converge nunca | 3 escalones fallidos seguidos en E1–E2 | Bajar a E1 con TOF fijo y control de 3 segmentos; si eso tampoco, es bug de gradientes/unidades, no del solver |
| Mínimos locales dominan | Multi-start con <5 % de convergencia | Adelantar T-2.1 (pygmo) antes de terminar M1 |
| Surrogate no generaliza | p99 de error > 10 % | Reducir dominio (§T-3.1), entrenar por regiones; si persiste, cerrar Fase 3 con resultado negativo documentado |
| Scope creep | Aparece la palabra "flyby", "Júpiter" o "3 cuerpos" antes de M3 | Al backlog congelado, sin discusión |
| Proyecto se enfría | 2 semanas sin commits | Volver a la tarea más pequeña abierta, no a la más interesante |

---

## 10. Próximas 3 acciones

1. Cerrar D-1 y D-2 con timebox de 60 minutos (T-0.1, T-0.2).
2. Escribir `tests/test_hohmann.py` **antes** que el integrador — es el oráculo de todo lo demás (T-0.5).
3. Poner el CI en rojo a propósito y luego en verde (T-0.3).

---

## Backlog congelado (no antes de M3)

Flybys y asistencia gravitatoria · problema de 3 cuerpos / manifolds · misiones multi-asteroide · visualización 3D interactiva en web · low-thrust con perturbaciones (J2, presión de radiación) · optimización del integrador en CUDA a mano.