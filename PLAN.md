# 📋 PLAN.md — helios-solver

> Para la vista general en inglés ver [`README.md`](README.md).

> `IDEA.md` responde **qué** y **por qué**. Este documento responde **cómo**, **en qué orden** y **cómo sé que ya terminé**.
> Regla de oro: ninguna tarea entra aquí si no tiene entregable verificable. Si no se puede testear o graficar, no es una tarea, es un deseo.

**Estado:** 🎯 **M1 alcanzado — Gate 1→2 cerrado.** Fase 1 completa (T-1.1 a T-1.9, E1-E5). Próximo: Fase 2 (búsqueda global) o cerrar T-1.5/T-1.6 primero.
**Última actualización:** 2026-07-29
**Milestone activo:** M2 — ventana de lanzamiento auto-descubierta (Fase 2)

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

**✅ Cerrado (2026-07-29).** T-0.1 a T-0.8 completas, 8/8 tests en verde
(`tests/test_hohmann.py`, `tests/test_dynamics.py`, `tests/test_ephemeris.py`
nuevo para T-0.7). D-1 se resolvió en `jplephem` directo contra un kernel
SPK propio (ni `pykep` ni `hapsira` importan limpiamente — ver
[`docs/adr/0001`](docs/adr/0001-orbital-mechanics-library.md)); el error de
posición contra Horizons real es de ~10 m, muy por debajo de la tolerancia
de 1000 km.

---

## 3. Fase 1 — Baseline clásico (camino a M1)

**Objetivo del gate:** LA IMAGEN, con rendezvous real y verificada por integración.

### Escalera de realismo (D-4)
Cada escalón es un commit con su propia imagen guardada en `benchmarks/`. No se sube un escalón hasta que el anterior converge.

1. **E1** ✅ — 2D, órbitas circulares coplanares, empuje constante, tiempo de vuelo fijo. `benchmarks/e1_constant_tangential_thrust.png`.
2. **E2** ✅ — 2D, dirección de empuje variable (control discretizado), tiempo fijo. `benchmarks/e2_optimized_steering.png`.
3. **E3** ✅ — 2D, tiempo de vuelo libre. `benchmarks/e3_free_tof.png`: TOF y dirección optimizados juntos (restricciones duras + minimizar TOF = maximizar masa final, objetivo genuino a diferencia de E2); TOF óptimo ≈ 169.2 días (vs. 180 fijo en E2), m_f/m_0 ≈ 75.1 % (vs. 73.6 % en E2). A diferencia de E2, aquí **sí converge al mismo óptimo** desde distintas semillas — ver `tests/test_e3_scenario.py`.
4. **E4** ✅ — 3D con efemérides reales, fechas fijas. `benchmarks/e4_real_ephemerides.png`: salida = estado real de la Tierra (`ephemeris.py`) el 2029-01-01, objetivo = posición real de Marte el 2029-09-14 (TOF=256 días; ventana verificada — ángulo Tierra-Sol-Marte ~170.6°, cerca del ideal de Hohmann de 180°, no una fecha arbitraria). Control genuinamente 3D (`alpha` y `beta` libres). Error de posición final ~6 km (tolerancia 1000 km, mismo estándar que T-0.7). Solo posición, no velocidad — eso es E5.
5. **M1** ✅ — 3D, rendezvous completo (posición **y** velocidad). `benchmarks/e5_rendezvous.png` = `benchmarks/m1_spiral.png` (T-1.8, LA IMAGEN): salida real de la Tierra 2029-01-01, rendezvous con Marte 2029-12-17 (TOF=350 días — no los 256 heredados de E4; ver hallazgo de búsqueda de TOF abajo). Error final \|Δr\| = 1.67 km, \|Δv\| = 0.0002 m/s (tolerancia T-1.7: 1000 km / 1 m/s — cumplido con 3+ órdenes de magnitud de margen). Verificado a `rtol=1e-12` (T-1.9). m_f/m_0 = 62.2 % (por debajo del ~80 % idealizado de §3 abajo — ver nota).

**Hallazgo de la búsqueda de TOF para M1:** el TOF de 256 días heredado de E4 (bueno para *posición sola*) resultó demasiado corto para rendezvous completo — con ese TOF, ningún número de segmentos, semillas, o control de throttle acercó la solución combinada posición+velocidad a nada razonable (millones de km, miles de m/s), mientras que el matching de *solo* velocidad en aislamiento convergía perfecto (descarta bug de unidades). Un barrido de TOF confirmó que 350-400 días — el rango que este mismo documento ya anticipaba como referencia — sí convergen limpio. Formulación final en dos etapas: arranque con dirección-solamente + objetivo blando combinado, luego refinamiento con throttle libre + restricciones duras + maximizar masa. Detalle completo en el docstring de `benchmarks/e5_rendezvous.py`.

**Sobre el 62.2 % vs. el ~80 % idealizado:** PLAN.md §3 ya avisa que un resultado por debajo de 0.70 sugiere "control ineficiente" — exactamente lo que pasa aquí (el arranque de la búsqueda usa empuje siempre al máximo). El **criterio real de aceptación de T-1.7 es la precisión del rendezvous, no la fracción de masa**, y ese sí se cumple con margen amplio. Cerrar la brecha de eficiencia es explícitamente trabajo de T-1.5 (multi-start) y Fase 2 (búsqueda global), no de este escalón.

| ID | Tarea | Entregable | Criterio de aceptación | Estado |
|---|---|---|---|---|
| T-1.1 | `dynamics.py`: EDO en unidades canónicas (r, v, m) con empuje | módulo + tests | Con `T=0` reproduce T-0.6; con empuje tangencial constante la energía crece monótona | ✅ |
| T-1.2 | Transcripción Sims-Flanagan propia, N segmentos, matching en el punto medio | `transcription.py` | Con la solución de Hohmann como entrada, el defecto de matching es ~0 | ✅ |
| T-1.3 | Función objetivo + restricciones para SLSQP | `solvers/local.py` | Gradientes por diferencias finitas validados contra derivada analítica en un caso trivial | ✅ |
| T-1.4 | Resolver E1 y E2 | imágenes en `benchmarks/` | Converge desde al menos 3 semillas distintas al mismo óptimo (±1 % en masa final) | ✅ E1 (`benchmarks/e1_constant_tangential_thrust.png`) y E2 (`benchmarks/e2_optimized_steering.png`, SLSQP con restricciones duras). La parte de masa final del criterio se cumple literalmente (spread ~1e-16 entre semillas), pero **el perfil de dirección óptimo no es único** — auditoría con tres formulaciones de objetivo distintas confirma un subespacio de soluciones de 6 grados de libertad (2 restricciones, 8 variables); semillas distintas convergen de forma precisa a las restricciones pero a perfiles distintos entre sí (~ver `benchmarks/e2_optimized_steering.py` y `tests/test_e2_scenario.py`). Es la no-convexidad que anticipa IDEA.md §2, no un bug — motiva T-1.5/Fase 2 en vez de confiar en un solo SLSQP local |
| T-1.5 | Multi-start paralelo con `joblib` | `solvers/multistart.py` | 200 semillas en paralelo, reporte de tasa de convergencia por semilla | |
| T-1.6 | Migrar a IPOPT (`cyipopt`) si SLSQP se atasca | flag `--solver=ipopt` | Mismo óptimo que SLSQP en E2, o mejor, en menos iteraciones | |
| T-1.7 | Subir a E4/E5 con efemérides reales | commits por escalón | Restricción de rendezvous satisfecha: \|Δr\| < 1000 km y \|Δv\| < 1 m/s | ✅ E4 y E5/M1 (ver escalera arriba) — \|Δr\|=1.67 km, \|Δv\|=0.0002 m/s |
| T-1.8 | 🎯 **`viz.py` — LA IMAGEN** | `benchmarks/m1_spiral.png` | Órbitas en gris, espiral en color, flechas de empuje escaladas por magnitud, anotaciones: fechas, Δv efectivo, m_f/m_0, TOF | ✅ `benchmarks/m1_spiral.png` |
| T-1.9 | Verificación final por integración de alta precisión | `tests/test_e5_scenario.py` (el entregable original decía `test_m1_solution.py`; se unificó con el archivo de escenario de E5, mismo contenido) | La solución del optimizador, re-integrada con `rtol=1e-12`, cumple el rendezvous. **Ninguna solución se publica sin este paso** | ✅ |

**Caso de referencia a fijar en Fase 1** (el IDEA.md dejó el número cortado — cerrarlo aquí):
Isp = 3000 s, T_max = 0.5 N, m_0 = 1000 kg, TOF ≈ 300–400 días → **m_f ≳ 800 kg (≥ 80 %)**.
Cálculo de cordura con Tsiolkovsky: si Δv efectivo del bajo empuje ≈ 5.5–6.5 km/s con Isp 3000 s (v_e ≈ 29.4 km/s), entonces m_f/m_0 = exp(−Δv/v_e) ≈ 0.80–0.83. **Consistente.** Si el resultado sale muy por encima de 0.85, sospechar que el rendezvous no es real (probablemente solo cruza la órbita). Si sale por debajo de 0.70, sospechar control ineficiente o demasiadas revoluciones.

**🚦 Gate 1 → 2:** `m1_spiral.png` existe, T-1.9 en verde, y el README muestra la imagen.

**✅ Cerrado (2026-07-29).** `benchmarks/m1_spiral.png` existe,
`tests/test_e5_scenario.py::test_e5_rendezvous_satisfies_t17_tolerance_at_t19_precision`
en verde, README actualizado con la imagen. m_f/m_0 = 62.2 % queda por
debajo del ~80 % de referencia (ver nota arriba); no bloquea el gate
porque el criterio de T-1.7/T-1.9 es precisión de rendezvous, no
eficiencia de propelente — cerrar esa brecha es explícitamente Fase 2.

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

El detalle completo (contexto/decisión/consecuencias) de cada fila vive en
[`docs/adr/`](docs/adr/README.md) — esta tabla es el índice corto.

| # | Fecha | Decisión | Motivo | Estado | ADR |
|---|---|---|---|---|---|
| 1 | 2026-07-29 | D-1: librería orbital | Ni `pykep` (wheel rota) ni `hapsira` (incompatible con astropy/numpy/scipy actuales) importan; `jplephem` directo contra un kernel propio si funciona y valida a ~10 m contra Horizons | aceptada | [0001](docs/adr/0001-orbital-mechanics-library.md) |
| 2 | — | D-2: gestor de entorno | Ya ejercida en la práctica: `pyproject.toml`/`uv.lock`/CI usan `uv` exclusivamente | aceptada | [0002](docs/adr/0002-environment-manager.md) |
| 3 | — | D-3: unidades canónicas | Condicionamiento numérico del NLP; ya implementada en `constants.py` (`DU_KM`/`TU_S`) | aceptada | [0003](docs/adr/0003-canonical-units.md) |
| 4 | — | D-4: escalera de realismo | Aislar bugs de física de bugs de optimización; usada consistentemente en README/PLAN | aceptada | [0004](docs/adr/0004-realism-ladder.md) |

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
| pykep no instala | 60 min sin wheel funcional | ~~Cambiar a `hapsira`/`jplephem`~~ — **ocurrió, y `hapsira` tampoco importa** (ver [ADR-0001](docs/adr/0001-orbital-mechanics-library.md)); fallback real: `jplephem` directo contra un kernel SPK propio |
| El NLP no converge nunca | 3 escalones fallidos seguidos en E1–E2 | Bajar a E1 con TOF fijo y control de 3 segmentos; si eso tampoco, es bug de gradientes/unidades, no del solver |
| Mínimos locales dominan | Multi-start con <5 % de convergencia | Adelantar T-2.1 (pygmo) antes de terminar M1 |
| Surrogate no generaliza | p99 de error > 10 % | Reducir dominio (§T-3.1), entrenar por regiones; si persiste, cerrar Fase 3 con resultado negativo documentado |
| Scope creep | Aparece la palabra "flyby", "Júpiter" o "3 cuerpos" antes de M3 | Al backlog congelado, sin discusión |
| Proyecto se enfría | 2 semanas sin commits | Volver a la tarea más pequeña abierta, no a la más interesante |

---

## 10. Próximas 3 acciones

~~1. Cerrar D-1 y D-2 con timebox de 60 minutos (T-0.1, T-0.2).~~
~~2. Escribir `tests/test_hohmann.py` antes que el integrador (T-0.5).~~
~~3. Poner el CI en rojo a propósito y luego en verde (T-0.3).~~
~~4. E2: optimizar la dirección de empuje por segmento con SLSQP.~~
~~5. E3: liberar el tiempo de vuelo.~~
~~6. E4: subir a 3D con efemérides reales, fechas fijas.~~
~~7. E5/M1: rendezvous completo (posición y velocidad) + T-1.9.~~
Hecho — **M1 alcanzado, Fase 1 completa** (ver escalera y Gate 1→2
arriba). Próximas 3 reales, ya en Fase 2:

1. T-1.5 (multi-start real) antes que Fase 2 formal: con E2-E5 ya
   convergiendo desde semillas individuales pero mostrando comportamiento
   no-convexo genuino (E2: perfiles distintos; M1: 62% en vez del ~80%
   idealizado por partir de un arranque ineficiente), correr cientos de
   semillas en paralelo con `joblib` es lo que decide si esa brecha se
   cierra con más cómputo o si hace falta búsqueda global de verdad.
2. T-2.1: envolver el problema (ya validado end-to-end en E5) como
   `pygmo.problem`, reusando `transcription.py`/`dynamics.py` sin
   duplicar la definición de objetivo/restricciones — igual que el
   local, per T-2.1.
3. T-2.5 antes que cualquier trabajo de Fase 3: perfilar dónde se va
   el tiempo de cómputo real (¿integración de EDOs? ¿evaluación de
   gradientes por diferencias finitas?) — la Fase 3 (surrogate) solo
   se justifica si ese número sale >70%, medido, no asumido.

---

## Backlog congelado (no antes de M3)

Flybys y asistencia gravitatoria · problema de 3 cuerpos / manifolds · misiones multi-asteroide · visualización 3D interactiva en web · low-thrust con perturbaciones (J2, presión de radiación) · optimización del integrador en CUDA a mano.