# La falla de entropía en COLDCARD y el barrido de ~594.5 BTC: informe del incidente

**Fecha de corte:** 31 de julio de 2026
**Autor:** investigación independiente, defensiva. Ver `DISCLAIMER.md`.
**Repositorio:** todo lo citado acá (commits, evidencia on-chain, builds, código) está en este repositorio, verificable por cualquiera.

Este informe distingue lo que está **confirmado por código o por la blockchain**, lo que es **preliminar** (viene de una fuente confiable pero no fue re-derivado de forma independiente) y lo que es **inferencia** (una conclusión razonable, no una prueba directa). Esa clasificación aparece entre paréntesis después de cada afirmación importante.

## Qué pasó

El 30 de julio de 2026, alguien vació aproximadamente 594.5 BTC desde 500 direcciones de Bitcoin en cuestión de minutos. Las víctimas usaban wallets de hardware COLDCARD. La causa no fue un ataque físico ni una falla de Bitcoin: fue un error en cómo el firmware de COLDCARD generaba las claves secretas de esas wallets.

Una wallet de Bitcoin depende de un número aleatorio inicial (la "semilla") del que se derivan todas sus claves. Si ese número no es realmente impredecible, alguien puede reconstruirlo y robar los fondos sin necesidad de tocar el dispositivo. Eso fue, en esencia, lo que ocurrió acá.

Coinkite (el fabricante) y Block publicaron advisories técnicos el 30 y 31 de julio (`coinkite-mk3-advisory`, `coinkite-entropy-backgrounder`, `block-engineering-report` en `references/sources.yml`). Este informe no repite esos textos sin más: cada afirmación técnica de acá fue verificada de forma independiente contra el código fuente público y contra la blockchain.

## Cómo funcionaba el bug (CONFIRMADO en código)

El firmware de COLDCARD debía usar el generador de números aleatorios por hardware del chip STM32 para crear las semillas. Dos cosas se combinaron para que eso no pasara:

1. La configuración de la placa define una macro (`MICROPY_HW_ENABLE_RNG`) en `0`, para indicar "no uses el generador estándar de MicroPython, tenemos el nuestro".
2. La librería criptográfica del proyecto (`libNgU`) chequea si esa macro *está definida*, no si vale distinto de cero. Como sí está definida (en `0`), el chequeo pasa igual.

El resultado: en vez de usar el generador de hardware real, el sistema terminaba usando el generador de respaldo por software de MicroPython, llamado Yasmarang. Yasmarang no es criptográficamente seguro. Se inicializa con datos como el identificador único del chip y temporizadores internos, valores que no son secretos y que, en muchos casos, se pueden acotar o adivinar.

En los modelos más nuevos (Mk4, Mk5, Q) se agregó una capa extra: se mezclaban datos de dos elementos seguros. Pero, verificado directamente en el código (`shared/mk4.py`, `evidence/commits/findings.md` sección 5), esa mezcla se reducía a hashear los datos y usar apenas los primeros 4 bytes del resultado para "resembrar" una sola palabra del estado interno de Yasmarang. Es decir: aun con esa mejora, quedaba un límite de 32 bits de entropía efectiva en el peor caso, muy por debajo del objetivo de 128 bits.

## Lo que verifiqué yo mismo

### 1. Los commits del arreglo, más uno que el advisory no menciona

El aviso oficial cita un commit de introducción del bug y uno del arreglo. Clonando el repositorio de Coldcard en GitHub y revisando el historial completo (no solo los dos commits señalados), encontré:

- El commit de introducción (`b18723dd`, 1 de marzo de 2021) migró la generación de semillas de un módulo propio de COLDCARD a `ngu.random`, la librería que terminó siendo vulnerable. La macro problemática ya existía antes de ese cambio; lo que cambió fue qué código la consumía.
- El commit de arreglo (`ca724637`, 30 de julio de 2026) corrige la pista estándar de Mk4/Mk5/Q.
- **Existe un tercer commit no mencionado en el advisory**: `b987de50`, de otro desarrollador, el mismo día, que aplica un arreglo equivalente pero en una rama separada ("Edge"). Los dos commits están en líneas de historia distintas, ninguno es ancestro del otro.

### 2. La versión de arreglo para Mk3 todavía no tiene tag público

El advisory y el changelog del propio repositorio dicen que la versión `4.2.0` corrige el problema en el modelo Mk3. Al revisar los 182 tags del repositorio público, **no existe ningún tag `4.2.0`**, en ninguna rama, a la fecha de esta verificación. El commit con el arreglo equivalente para Mk3 existe, pero en una rama sin fusionar y sin versión asignada todavía. Esto no significa que el aviso sea falso, pero sí que el release para Mk3 no estaba publicado como tag verificable al momento de escribir esto (`RESEARCH_GAPS.md`, ítem G-1).

### 3. Reconstrucción independiente del robo on-chain

En vez de usar la lista de transacciones publicada por terceros, reconstruí el barrido desde cero:

1. Partiendo únicamente de la dirección pública donde se consolidaron los fondos (`bc1qq85v2c926eg6pgxhwp6q7lf6cnsz80qs3fcu9r`), consulté su historial completo en la blockchain.
2. Encontré que esa dirección recibió los fondos del robo en una sola transacción de 341 entradas, dentro del rango de bloques asociado al incidente (960188-960191).
3. Todas esas 341 entradas venían de una única dirección intermedia. Rastreé el historial completo de esa dirección intermedia (502 transacciones) y clasifiqué cada una por altura de bloque.

Resultado: **500 transacciones, 1.324 UTXO consumidos, ~594.48 BTC movidos**, dentro de la misma ventana de bloques reportada públicamente. Estos números coinciden, con la única diferencia siendo redondeo, con lo publicado por Atlas21 (`atlas21-onchain` en `references/sources.yml`), pero fueron derivados de forma independiente, transacción por transacción, no copiados de esa fuente. El detalle completo, con cada TXID, está en `evidence/onchain/drain-transactions.csv` y el método paso a paso en `evidence/onchain/methodology.md`.

### 4. Prueba compilada del bug, no solo lectura de código

Para no quedarme en el análisis de código, compilé desde cero, con el mismo toolchain Docker que documenta el propio proyecto:

- La versión vulnerable (`v5.0.0`, Mk4/Mk5, enero de 2022).
- La versión ya corregida (`v5.6.0`, Mk4/Mk5, 31 de julio de 2026).

Con `arm-none-eabi-nm` (una herramienta que lista qué función quedó en qué archivo compilado) confirmé, sobre los binarios reales:

| | Build vulnerable | Build corregido |
|---|---|---|
| ¿Quién define la función que da el número "aleatorio"? | El generador de respaldo de MicroPython (el débil) | El código de la placa que habla con el hardware real |
| Chequeo automático del propio proyecto (`rng-code-check`) | No existía en esta versión | Corrió solo, sin errores |

El detalle completo, con hashes SHA-256 de cada binario y cada log de compilación, está en `evidence/builds/vulnerable/` y `evidence/builds/patched/`.

## Línea de tiempo

| Fecha | Evento |
|---|---|
| 2021-03-01 | Commit que introduce la ruta vulnerable (`ngu.random`) |
| 2021-03-17 | Primera versión pública con el bug (Mk3, v4.0.0) |
| 2022-01-17 | Primera versión Mk4 con el mismo problema (v5.0.0) |
| 2026-07-30, ~01:36-01:51 UTC | Barrido de ~594.5 BTC en la ventana de bloques 960188-960191 (confirmado contra los timestamps reales de esos bloques) |
| 2026-07-30/31 | Coinkite y Block publican los advisories técnicos |
| 2026-07-31 | Se publican las versiones corregidas: 5.6.0 (Mk4/Mk5), 1.5.0Q (Q), 6.6.0X y 6.6.0QX (Edge). Mk3 (4.2.0) anunciada pero sin tag público a esta fecha |

## Qué hacer si tenés una COLDCARD

- No generes semillas nuevas con firmware anterior a la versión corregida de tu modelo.
- Actualizá desde la fuente oficial (`coldcard.com/downloads`) y verificá la firma.
- Generá una semilla completamente nueva después de actualizar. Actualizar el firmware no repara una semilla ya existente.
- Migrá los fondos a la wallet nueva, empezando con un monto chico de prueba.

## Qué no está probado (limitaciones)

- Que las 500 direcciones fueran, todas, wallets COLDCARD comprometidas específicamente por este bug. La coincidencia temporal y la evidencia de código son fuertes, pero no hay un peritaje público que confirme cada caso individual (`INFERENCIA`).
- No existe, a esta fecha, un identificador CVE público para esta vulnerabilidad (confirmado consultando directamente la API de NVD).
- Este informe no incluye, y nunca va a incluir, código capaz de recuperar semillas reales o robar fondos de terceros. Todo el trabajo de reproducción usa datos sintéticos o Bitcoin regtest.

## Fuentes principales

- Advisory oficial de Coinkite: https://blog.coinkite.com/coldcard-mk3-seed-generation-warning/
- Análisis técnico de Coinkite: https://blog.coinkite.com/entropy-technical-backgrounder/
- Análisis técnico de Block: https://engineering.block.xyz/blog/predictable-rng-fallback-and-32-bit-reseed-in-coldcard-firmware
- Repositorio oficial del firmware: https://github.com/Coldcard/firmware
- Investigación on-chain inicial de Atlas21: https://atlas21.com/594-bitcoin-drained-15-minutes-theft/

Lista completa, con nivel de confiabilidad de cada fuente, en `references/sources.yml`.

## Agradecimientos

A Coinkite y al equipo de Block por publicar advisories técnicos detallados en medio de un incidente en curso, y a Atlas21 por la investigación on-chain inicial que sirvió como punto de partida para la reconstrucción independiente de este informe.
