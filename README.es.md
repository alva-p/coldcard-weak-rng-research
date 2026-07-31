# coldcard-weak-rng-research

Investigación independiente y defensiva sobre la falla de entropía del firmware de
COLDCARD divulgada el 2026-07-30/31 y el barrido coordinado de ~594.5 BTC observado el
mismo día. Todo acá es verificable: commits reales, datos reales de blockchain,
binarios compilados de verdad.

**[📄 Leé el informe (Español)](docs/es/report.md)** · **[📄 Read the report (English)](docs/en/report.md)**

## Qué es esto

El 30 de julio de 2026, alguien vació aproximadamente 594.5 BTC de 500 direcciones de
Bitcoin en unos quince minutos. Las víctimas usaban wallets de hardware COLDCARD, y la
causa raíz fue un bug de firmware que hacía predecibles secretos que deberían haber
sido aleatorios. Coinkite (el fabricante) y Block publicaron advisories oficiales. Este
repositorio no se limita a resumir esos avisos: re-deriva de forma independiente todo
lo que se puede re-derivar: los commits del arreglo, el flujo on-chain de los fondos
robados, y el bug en sí, compilado y probado con herramientas reales.

## Tres cosas que podés verificar vos mismo

1. **El código.** [`evidence/commits/findings.md`](evidence/commits/findings.md) verifica
   los commits del arreglo directamente contra el repositorio de firmware de Coldcard,
   incluyendo uno que el advisory oficial no menciona.
2. **El dinero.** [`evidence/onchain/`](evidence/onchain) rastrea el robo on-chain desde
   cero, partiendo únicamente de la dirección pública de consolidación, no de ninguna
   lista de transacciones ya publicada. Resultado: 500 transacciones, 1.324 UTXO,
   ~594.5 BTC, coincidiendo con lo reportado públicamente. Cada TXID está en
   [`drain-transactions.csv`](evidence/onchain/drain-transactions.csv).
3. **El build.** [`evidence/builds/`](evidence/builds) compila desde código fuente el
   firmware vulnerable y el parcheado, y usa `arm-none-eabi-nm` sobre los binarios
   reales para mostrar a qué función resolvía la llamada de "número aleatorio", antes y
   después del arreglo. Ver [`comparison.md`](evidence/builds/comparison.md).

## Qué no hay acá

Ningún PoC que recupere una semilla real, escanee direcciones vulnerables, o mueva
fondos que no sean del propio investigador, y nunca lo va a haber. Ver
[`DISCLAIMER.md`](DISCLAIMER.md). Un simulador sintético de RNG y una demostración en
Bitcoin regtest están planeados pero todavía no construidos; los ítems abiertos están
documentados sin vueltas en [`RESEARCH_GAPS.md`](RESEARCH_GAPS.md), incluyendo uno
importante: la versión de arreglo para Mk3 que anunció Coinkite (4.2.0) no tiene tag
publicado en git a la fecha de esta escritura.

## Fuentes

Cada afirmación se puede rastrear a una fuente primaria (código, commit, o datos
on-chain) o a una fuente secundaria con su nivel de confiabilidad indicado. Lista
completa en [`references/sources.yml`](references/sources.yml).

## Cómo citar este trabajo

```
Álvaro P., "La falla de entropía en COLDCARD y el barrido de ~594.5 BTC: informe del
incidente", coldcard-weak-rng-research, 2026-07-31.
https://github.com/alva-p/coldcard-weak-rng-research
```

## Licencia

El código está bajo MIT ([`LICENSE-CODE`](LICENSE-CODE)). Los informes y la
documentación están bajo CC BY 4.0 ([`LICENSE-DOCS`](LICENSE-DOCS)).

## Seguridad y alcance

¿Encontraste una vulnerabilidad, o algún secreto commiteado por error en este repo? Ver
[`SECURITY.md`](SECURITY.md). No abras un issue público con semillas, claves o datos de
víctimas reales.
