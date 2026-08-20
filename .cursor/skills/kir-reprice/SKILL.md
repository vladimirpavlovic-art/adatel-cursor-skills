---
name: kir-reprice
description: Deterministički engine za KIR cenovnik repricing, old/new OPEX mapping, ugovornu klasifikaciju i bulk reconciliation. Use when the user mentions KIR kartice, KIR cenovnik, reprice, repricing, OPEX cenovnik, old/new mapping, Art. 3.5, reconciliation report, or asks to refactor/run the KIR cenovnik konverter.
---

# ADATEL KIR Reprice & Reconciliation Engine v2

Refaktoriši postojeću logiku KIR cenovnik konvertera u deterministički engine za
old/new OPEX mapping, repricing, ugovornu klasifikaciju i bulk reconciliation.

Ovo **nije** generički LLM spreadsheet agent. Parsiranje, numerika i validacija
moraju biti deterministički — implementirani u kodu, ne u proznom zaključivanju.

## Non-goals

- Nema LLM procene cena, šifara, datuma ni ugovornog statusa.
- Nema "pametnog" popunjavanja praznih polja.
- Nema fuzzy matcha kao izvora istine (dozvoljen je samo kao predlog u exception queue).

## Input

Svi ulazi su eksplicitni; ništa se ne izvodi iz podrazumevanih vrednosti.

| Ulaz | Opis |
| --- | --- |
| KIR xlsx kartica | originalni source workbook |
| stari Telekom OPEX cenovnik | old price list |
| novi Telekom OPEX cenovnik | new price list |
| old↔new mapping tabela | veza između starih i novih šifara |
| effective dates | datumi važenja po cenovniku i po kartici |
| commercial-rules tabela | konfigurabilna, uključujući Art. 3.5 parametre |
| execution/signature/status metadata | izvršenje, potpis, status kartice |

Ako bilo koji obavezan ulaz nije prisutan ili nije čitljiv, engine se zaustavlja
sa jasnom greškom. Ne nastavljaj sa parcijalnim ulazom.

## Pipeline

Koraci se izvršavaju redom. Svaki korak ima proverljiv izlaz.

1. **Parse source workbook** — deterministički parser, bez heuristike nad
   layoutom koja nije eksplicitno konfigurisana.
2. **Canonical line-item ledger** — svaka stavka dobija stabilan identitet
   (šifra, opis, količina, jedinična cena, iznos, poreklo: sheet + red).
3. **Reprodukuj originalni source total** — izračunaj total iz ledgera.
4. **Hard stop** — ako izračunati source total != workbook total, **STOP**.
   Ne repricing, ne mapping, ne report. Prijavi razliku i lokaciju odstupanja.
5. **Map old/new codes** — svaka stavka dobija tačno jednu klasifikaciju:
   `EXACT`, `MAPPED`, `SPLIT_MERGE`, `REVIEW`.
6. **Technical value** — izračunaj po odgovarajućem cenovniku (old ili new),
   biranom na osnovu effective date, ne na osnovu pretpostavke.
7. **Contractual value** — izračunaj **odvojeno** od technical value. Dve
   vrednosti se nikada ne mešaju u istoj koloni.
8. **Art. 3.5 rule** — 70% verifikovane DOT→Telekom stope. Primenjuje se
   **samo** kada su i base i effective-date condition potvrđeni.
9. **Out-of-scope** — stavke van scope-a idu u `EXTRA` ili `REVIEW`. Nikada se
   ne primenjuje Art. 3.5 automatski na out-of-scope stavke.
10. **Exception queue** — sve što je `SPLIT_MERGE`, `REVIEW`, `EXTRA`, ili ima
    nepotvrđen Art. 3.5 uslov, ulazi u queue sa razlogom.
11. **Output** — XLSX reconciliation report + machine-readable audit file
    (JSON/CSV) sa punim tragom po stavci.

## Klasifikacija mappinga

- `EXACT` — old šifra postoji identično u novom cenovniku.
- `MAPPED` — 1:1 veza potvrđena mapping tabelom.
- `SPLIT_MERGE` — 1:N ili N:1 veza; ide u exception queue uz predloženu
  dekompoziciju, ali se ne zaključuje automatski.
- `REVIEW` — nema potvrđene veze, ili je veza dvosmislena.

## Art. 3.5 gate

Primeni 70% stopu isključivo kada su oba uslova eksplicitno potvrđena:

1. **Base condition** — verifikovana DOT→Telekom bazna stopa za tu stavku.
2. **Effective-date condition** — datum kartice pada u važeći period.

Ako je bilo koji uslov nepotvrđen: `REVIEW`, sa navedenim uslovom koji fali.
Nema delimične primene, nema podrazumevanog "verovatno važi".

## Output

**XLSX reconciliation report** — po stavci: source vrednosti, klasifikacija,
technical value, contractual value, primenjena pravila, delta, status.

**Audit file** — machine-readable, dovoljan za rekonstrukciju svake izračunate
cifre: ulazni red, izabrani cenovnik, primenjena pravila, međurezultati.

Oba izlaza moraju biti reproducibilna: isti ulaz → bajt-identičan rezultat
(osim eksplicitnog timestamp polja).

## Obavezni golden testovi

Engine se ne smatra ispravnim dok sva tri ne prolaze:

- **A** — jedna zatvorena OLD-price kartica.
- **B** — jedna zatvorena NEW-price kartica.
- **C** — trenutnih 5 KG kartica: source total mora biti **499.594,04 RSD**.

Test C je regression guard za korak 3/4. Ako padne, problem je u parsiranju ili
sumiranju, ne u repricingu — ne "popravljaj" ga podešavanjem repricing logike.

## Hard rules

- Nikada ne nagađaj šifru, cenu, datum ili ugovorni status.
- Nepotvrđeno ≠ nula. Nepotvrđeno ide u exception queue.
- Numerika ide preko decimalne aritmetike, ne float-a; zaokruživanje je
  eksplicitno i definisano na jednom mestu.
- Mismatch source totala je hard stop, ne warning.
- Technical i contractual vrednost ostaju razdvojene kroz ceo pipeline.
- Svaka izlazna cifra mora imati trag do ulaznog reda i primenjenog pravila.
