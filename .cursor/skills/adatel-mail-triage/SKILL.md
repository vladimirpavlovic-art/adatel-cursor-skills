---
name: adatel-mail-triage
description: Thread-level Gmail triage and business-state reasoning for vladimir.pavlovic@adatel.rs (Business / Codex). Use for ADATEL inbox triage, unread review, work readiness, KIR/document closeout, billing readiness, responsibility attribution, disputes, escalations, meeting packs, or safe mark-read decisions.
---

# ADATEL Mail Triage — Thread State & Lifecycle v2

Ovaj skill je namenjen isključivo nalogu
`vladimir.pavlovic@adatel.rs` (Business / Codex). Radi nad poslovnim Gmail nitima,
ne nad izolovanim porukama. Primarni zadatak je da rekonstruiše trenutno poslovno
stanje niti, objasni promenu i predloži proverljivu sledeću akciju.

## Scope i sigurnosna pravila

- Pre čitanja ili izmene proveri da je aktivni nalog
  `vladimir.pavlovic@adatel.rs`. Ako nije, zaustavi se i prijavi mismatch.
- Ne šalji mail, ne kreiraj draft, ne menjaj read/unread, label ili Drive sadržaj
  bez eksplicitnog zahteva korisnika.
- Klasifikacija nije dokaz izvršenja, potpisa, odobrenja, fakturisanja ili
  plaćanja. Svaki takav zaključak mora imati eksplicitni signal u niti ili
  povezanom dokumentu.
- Ne nagađaj činjenice, odgovornost, nameru, rok ili autoritet. Koristi `UNKNOWN`
  kada dokaz nije dovoljan.
- Citiraj signal kratkim neutralnim opisom; ne reprodukuj nepotrebne lične ili
  poverljive podatke.
- Jedna poslovna nit je jedna jedinica triage-a, čak i kada sadrži mnogo poruka.

## Režimi

Podržani režimi:

1. `STANDARD_TRIAGE` — kompletno stanje i delta po poslovnoj niti.
2. `UNREAD_REVIEW` — kuriranje unread niti uz stabilne redne brojeve.
3. `MEETING_PACK` — Client/Partner Meeting Pack izveden iz istog thread state-a.

Ako korisnik ne navede režim, koristi `STANDARD_TRIAGE`. Ne mešaj rezultate
različitih režima bez jasnih odeljaka.

## Pipeline

Korake izvršavaj ovim redom:

1. potvrdi nalog i opseg pretrage;
2. prikupi sve poruke kandidata, Gmail metadata i dostupne priloge/linkove;
3. grupiši poruke u poslovne niti;
4. sortiraj svaku nit hronološki;
5. izdvoji događaje i činjenice sa izvorom;
6. redukuj ceo tok u thread state;
7. primeni readiness, lifecycle, billing, responsibility i dispute pravila;
8. odredi prioritet, blocker i sledeću akciju;
9. renderuj izlaz iz reduciranog stanja;
10. tek na eksplicitan zahtev izvrši dozvoljene mutacije uz mark-read safety gate.

Poslednji mail nikada ne zamenjuje niti briše raniji kontekst. On samo dodaje,
menja, rešava ili osporava činjenice koje se mogu povezati sa dokazom.

## Grupisanje poslovnih niti

### Primarni ključ

Koristi Gmail `threadId` kada postoji. Prosleđivanje, odgovor i promena subject
prefiksa (`Re:`, `Fwd:`) ostaju u istoj Gmail niti.

### Minimax grouping guard

Zadrži postojeći Minimax princip: napravi najmanji broj grupa koji sprečava
mešanje različitih poslovnih tema.

- Spoji poruke samo kada postoji jak strukturni signal: isti `threadId`, isti
  KIR/card/order broj, ista lokacija/element uz kontinuirani posao, ili eksplicitna
  referenca na prethodnu poruku.
- Ne spajaj samo zbog istog pošiljaoca, klijenta, regiona ili sličnog subject-a.
- Razdvoji jednu Gmail nit u više poslovnih tema samo kada postoje nezavisni
  scope, lokacija i akcija bez zajedničkog ishoda.
- Kada je grupisanje neizvesno, zadrži Gmail nit i dodaj
  `grouping_confidence: LOW`; ne stvaraj lažnu preciznost.
- U jednom run-u jednom izračunat `business_thread_key` ostaje stabilan:
  `threadId`, inače najjači dokument/lokacija ključ, inače deterministički hash
  normalizovanog subject-a i prvog message ID-a.

## Thread State Reducer

### Obavezni događaj po poruci

Za svaku poruku hronološki izvedi:

```yaml
message_event:
  message_id: string
  timestamp: RFC3339
  actor: ADATEL | DOT | TELEKOM | OTHER | UNKNOWN
  asserted_facts: []
  changed_facts: []
  resolved_facts: []
  disputed_facts: []
  requests: []
  commitments: []
  evidence_refs: []
```

Fact mora imati predmet i status, na primer:

```yaml
fact:
  key: scope.quantity
  value: 6
  status: ASSERTED | CONFIRMED | DISPUTED | SUPERSEDED | RESOLVED
  source_message_id: string
  confidence: HIGH | MEDIUM | LOW
```

Nova vrednost istog fact key-a ne briše staru. Obeleži staru vrednost kao
`SUPERSEDED`, poveži je sa novim source message ID-em i prikaži thread delta.
Kontradikcija bez jasnog autoritativnog razrešenja ostaje `DISPUTED`.

### Reducer akumulator

Za svaku nit vrati najmanje:

```yaml
thread_state:
  business_thread_key: string
  topic: string
  previous_state: WORK_LIFECYCLE
  new_state: WORK_LIFECYCLE
  state_change: string
  new_fact: []
  resolved_fact: []
  superseded_fact: []
  disputed_fact: []
  remaining_blocker: []
  next_action:
    owner: ADATEL | DOT | TELEKOM | SHARED | UNKNOWN
    action: string
    dependency: string | null
  flags: []
  responsibility: []
  evidence_refs: []
```

`previous_state` je stanje neposredno pre najnovijeg relevantnog događaja,
ne stanje iz prvog maila. `new_state` je stanje nakon primene tog događaja.
Ako poslednja poruka nema poslovni delta, `previous_state == new_state` i
`state_change: NO_CHANGE`.

`new_fact` sadrži samo činjenice prvi put uvedene ili sada potvrđene.
`resolved_fact` sadrži blocker/dispute koji je eksplicitno zatvoren.
`remaining_blocker` se ponovo računa iz svih aktivnih činjenica, ne samo iz
poslednje poruke.

### Precedence pravila

1. Eksplicitno novije razrešenje istog pitanja nadjačava raniju pretpostavku.
2. Potvrđen dokument nadjačava neformalnu procenu, ali ne dokazuje događaj koji
   dokument ne pokriva.
3. Eksplicitno prihvatanje odluke ostaje prihvaćeno čak i ako poruka otvara
   drugi operativni dispute.
4. Urgency signal utiče na flag/prioritet, nikada sam na readiness.
5. Client escalation ne dokazuje krivicu izvođača.
6. Tišina, nedostatak odgovora i CC lista nisu dokaz saglasnosti ili odgovornosti.

## Work lifecycle

Dozvoljena osnovna stanja su:

| State | Uslov |
| --- | --- |
| `NEW` | Nit je nova; nema dovoljno podataka za dalji status. |
| `INFO_MISSING` | Obavezni operativni input nedostaje, ali nije potvrđen spoljašnji hard blocker. |
| `READY_TO_WORK` | Svi primenljivi readiness gate uslovi su potvrđeni. |
| `IN_PROGRESS` | Postoji eksplicitan dokaz da je fizički/operativni rad počeo. |
| `EXECUTED_PENDING_CLOSEOUT` | Fizički rad je završen, ali closeout/potpis/broj/log nije kompletan. |
| `DOCUMENTATION_INCOMPLETE` | Dokumentacija je delimično primljena ili potvrđeno nedostaje. |
| `DOCUMENTATION_COMPLETE` | Sva propisana prateća dokumentacija je potvrđena. |
| `READY_TO_INVOICE` | Billing gate je ispunjen ili postoji eksplicitno ovlašćenje za račun. |
| `INVOICED` | Postoji eksplicitan dokaz da je račun izdat/poslat. |
| `CLOSED` | Poslovna nit je eksplicitno zatvorena; nema otvorene akcije. |

Stanja nisu prost linearni timestamp. Ako novi dokaz otkrije ranije skriveni
blocker, stanje može nazadovati uz obavezno objašnjenje `state_change`.
`PAID` je billing state; kada je potvrđen i nema drugih otvorenih pitanja,
work lifecycle može biti `CLOSED`.

### Paralelni flags

Dozvoljeni flagovi:

- `URGENT`
- `BLOCKED`
- `DISPUTED`
- `ON_HOLD`
- `CLIENT_ESCALATION`
- `COMMERCIAL_RISK`
- `AUTHORITY_CONFLICT`

Flag ne zamenjuje lifecycle. Na primer:
`INFO_MISSING + URGENT`, `IN_PROGRESS + BLOCKED` i
`EXECUTED_PENDING_CLOSEOUT + DISPUTED` su validne kombinacije.

Ukloni flag samo kada postoji eksplicitan dokaz da je razlog završen. Zabeleži
ga u `resolved_fact`.

## Ready-to-work gate

`URGENT != READY_TO_WORK`.

Pre `READY_TO_WORK` proveri sve primenljive stavke:

| Gate | Prihvatljiv dokaz |
| --- | --- |
| KIR / radni dokument | identifikovan dokument, broj ili potvrda da je izdat |
| Jednoznačan scope | element i rad bez kontradiktornih instrukcija |
| Količina | aktuelna količina eksplicitno potvrđena |
| Lokacija / element | dovoljno precizni za izvršenje |
| Materijal | raspoloživost/vrsta potvrđeni ili označeno da nije potreban |
| Pristup / mehanizacija | mogući i usaglašeni ili označeno da nisu potrebni |
| Telekom/client support | vlasnik i termin poznati ili potvrđeno da nije potreban |
| Prioritet i authority | nema otvorenog konflikta ko raspoređuje ekipu |

Za svaku stavku vrati `PASS`, `FAIL` ili `N/A` i evidence ref. `UNKNOWN` tretiraj
kao `FAIL`, ne kao implicitni prolaz.

- Nedostajući input bez potvrđenog spoljnog blokera:
  `INFO_MISSING`.
- Potvrđen hard blocker: odgovarajuće lifecycle stanje + `BLOCKED`.
- Konflikt instrukcija/autoriteta: `AUTHORITY_CONFLICT`; ne proglasi
  `READY_TO_WORK` dok nije razrešen.
- Urgent zahtev sa nepotpunim scope-om ostaje `INFO_MISSING + URGENT`.

## Billing state

Billing vodi kao odvojene, kumulativne činjenice:

```yaml
billing_state:
  work_executed: CONFIRMED | NOT_CONFIRMED
  signed: CONFIRMED | NOT_CONFIRMED
  documentation_complete: CONFIRMED | NOT_CONFIRMED
  ready_to_invoice: CONFIRMED | NOT_CONFIRMED
  invoiced: CONFIRMED | NOT_CONFIRMED
  paid: CONFIRMED | NOT_CONFIRMED
  evidence_refs: []
```

Pravila:

- `WORK_EXECUTED` ne implicira `SIGNED`.
- `SIGNED` ne implicira `DOCUMENTATION_COMPLETE`.
- `DOCUMENTATION_COMPLETE` ne implicira automatski `READY_TO_INVOICE` kada je
  potrebno dodatno komercijalno odobrenje.
- Potpisana KIR kartica ili grupni nalog bez obavezne Excel/supporting
  dokumentacije daje `DOCUMENTATION_INCOMPLETE`, ne `READY_TO_INVOICE`.
- Eksplicitno ovlašćenje poput „Možete poslati račun” je jak signal
  `READY_TO_INVOICE`, osim ako je u istoj ili kasnijoj poruci povučeno/uslovljeno.
- `INVOICED` zahteva dokaz slanja/izdavanja računa, ne samo spremnost.
- `PAID` zahteva potvrdu uplate/knjiženja, ne samo odsustvo prigovora.
- Uvek sačuvaj odvojene evidence refs za svaki billing korak.

## Responsibility attribution

Za svaki aktivni blocker klasifikuj:

```yaml
blocker:
  type: EXECUTION_FAILURE | MISSING_INPUT | DOCUMENTATION_DELAY | APPROVAL_DELAY | MATERIAL_BLOCKER | ACCESS_BLOCKER | CONFLICTING_PRIORITY_AUTHORITY
  responsible_party: ADATEL | DOT | TELEKOM | SHARED | UNKNOWN
  evidence_ref: string
  rationale: string
```

Attribution pravila:

- Dodeli stranu samo kada poruka/dokument direktno povezuje njenu obavezu i
  neizvršeni korak.
- Kada dve strane imaju zavisne otvorene obaveze, koristi `SHARED`.
- Kada se zna da blocker postoji, ali ne i čija je ugovorna/operativna obaveza,
  koristi `UNKNOWN`.
- Razdvoji `EXECUTION_FAILURE` od `MISSING_INPUT`; nemogućnost početka zbog
  nedostajućeg inputa nije automatski neuspeh izvođača.
- Razdvoji fizičko izvršenje od `DOCUMENTATION_DELAY` i `APPROVAL_DELAY`.
- Client escalation dodaje `CLIENT_ESCALATION`, ali ne menja attribution bez
  dokaza.
- Konflikt direktnog field prioriteta i formalnog client-supervision rasporeda
  daje `CONFLICTING_PRIORITY_AUTHORITY`, `AUTHORITY_CONFLICT` i
  `SHARED` ili `UNKNOWN`, zavisno od dokaza.

## Dispute extraction

Za strateške, komercijalne i eskalacione niti obavezno vrati:

```yaml
dispute:
  accepted_facts: []
  disputed_facts: []
  resolved_issues: []
  open_issues: []
  decision_already_accepted: []
  requested_exception_or_carve_out: []
```

Razloži složenu poruku na atomic claims. „Prihvatamo stop novih radova, ali
lokacija X iz postojećeg naloga nije završena” znači:

- strateška odluka o novim radovima: `ACCEPTED`;
- postojeća lokacija X: `OPEN/DISPUTED`;
- poruka nije odbijanje strateške odluke;
- zahtev da se X tretira odvojeno može biti `requested_exception_or_carve_out`.

Ne sažimaj celu nit kao „partner odbija odluku” ako je glavni decision eksplicitno
prihvaćen. Rešen issue ne vraćaj u open bez novog kontradiktornog dokaza.

## Drive structural signals

Drive signal dopunjuje thread state, ali ne zamenjuje poslovni dokaz.

- Zabeleži tip, naziv, lokaciju, owner-a, version/modified metadata i vezu sa
  thread key-em kada su dostupni.
- Postojanje fajla dokazuje samo da fajl postoji, ne da je potpisan, kompletan
  ili odobren.
- Strukturni obrazac foldera može podići confidence grupisanja, ali ne sme sam
  zaključiti lifecycle ili billing state.
- Nedostajući očekivani fajl je signal za proveru; `DOCUMENTATION_INCOMPLETE`
  postavi tek kada zahtev/obrazac jasno pokazuje da je fajl obavezan.
- Ne premeštaj, preimenuj, deli niti menjaš Drive dokumente bez eksplicitnog
  zahteva.

## Compliance qualification

Pre visokorizičnog zaključka navedi kvalifikator:

- `VERIFIED` — direktan eksplicitni dokaz;
- `SUPPORTED` — više saglasnih posrednih signala;
- `UNVERIFIED` — nema dovoljno dokaza;
- `CONFLICTING` — izvori se ne slažu.

Compliance/legal/contractual tvrdnje bez izvornog dokumenta ostaju
`UNVERIFIED`. Ne pretvaraj operativnu formulaciju u pravno priznanje krivice,
waiver, acceptance ili ugovornu obavezu. Surface-uj rok, vlasnika i rizik samo
kada su eksplicitni.

## Prioritet i next action

Prioritet odredi odvojeno od lifecycle-a:

- `P0` — bezbednost, zakonski/compliance rok ili potvrđen neposredan veliki
  poslovni prekid;
- `P1` — urgent/client escalation, blokiran aktivni rad ili neposredan
  commercial risk;
- `P2` — redovna operativna akcija, dokumentacija ili odobrenje;
- `P3` — informativno/watch bez trenutne akcije.

`next_action` mora biti jedna konkretna proverljiva radnja, sa owner-om i
zavisnošću. Ako owner nije dokazan, koristi `UNKNOWN` i napiši da treba potvrditi
vlasnika. Ne izmišljaj rok.

## STANDARD_TRIAGE output

Prvo prikaži sažetak:

| # | Topic/thread | Priority | Previous → New | Flags | Remaining blocker | Next action |
| --- | --- | --- | --- | --- | --- | --- |

Zatim za svaku nit prikaži:

1. `business_thread_key` i obuhvaćene poruke;
2. `previous_state`, `new_state`, `state_change`;
3. `new_fact`, `resolved_fact`, `superseded_fact`, `remaining_blocker`;
4. readiness gate tabelu kada rad još nije počeo;
5. billing state kada je izvršenje/dokumentacija/račun relevantan;
6. responsibility attribution za svaki blocker;
7. dispute extraction za strateške/eskalacione niti;
8. `next_action` i ključne evidence refs;
9. confidence/compliance qualifier za neizvesne tvrdnje.

Jedan broj pripada jednoj poslovnoj niti. Koristi isti redosled u svim detaljnim
sekcijama tog run-a.

## UNREAD_REVIEW mode

Output mora biti tačno:

| # | Topic/thread | Priority | State | Why keep unread | Action |
| --- | --- | --- | --- | --- | --- |

Dozvoljeni `Action` enum:

- `KEEP_UNREAD` — postoji konkretna neizvršena akcija korisnika/ADATEL-a ili
  neposredan P0/P1 blocker koji zahteva pažnju;
- `WATCH` — akcija je kod druge strane, ali nit ima otvoren rizik/dependency;
- `READ_CLOSE` — nema otvorene akcije ni razloga za aktivno praćenje.

Pravila:

- Jedna poslovna nit = jedan red, bez obzira na broj unread poruka.
- Brojeve dodeli jednom nakon konačnog sortiranja (priority, zatim najnoviji
  relevantni događaj, zatim `business_thread_key`) i zamrzni ih do kraja run-a.
- Nova poruka u već numerisanoj niti ne dobija novi broj u istom run-u.
- `Why keep unread` mora navesti aktivnu akciju/blocker, ne samo „važno”.
- Za `READ_CLOSE` koristi `Why keep unread: —`.
- Predloženi `READ_CLOSE` nije dozvola za mark-read.

## Mark-read safety

Pre bilo kakvog mark-read poziva:

1. zahtev mora biti eksplicitan;
2. prikaži tačan konačan skup thread ID-eva i pripadajuće `READ_CLOSE` redove;
3. isključi `KEEP_UNREAD`, `WATCH`, nepoznato i sve što nije prikazano korisniku;
4. menjaj stanje na nivou niti da ne ostanu skrivene unread poruke;
5. neposredno pre mutacije ponovo proveri da nije stigla nova poruka;
6. ako se nit promenila, preskoči je i prijavi razlog;
7. izvrši najmanju potrebnu mutaciju i vrati rezultat po thread ID-u.

Nikada ne koristi broad query kao mutacioni skup. Ne markiraj sve rezultate kao
pročitane zato što je triage završen.

## Client/Partner Meeting Pack

`MEETING_PACK` se izvodi iz već reduciranih thread state-ova; ne radi novu,
nekonzistentnu klasifikaciju.

Paket sadrži:

1. odluke već prihvaćene;
2. otvorene odluke i dispute;
3. workstream tabelu: lifecycle, flags, blocker, responsibility;
4. dokumentaciju i billing pipeline;
5. requested exceptions/carve-outs;
6. akcije po owner-u (`ADATEL`, `DOT`, `TELEKOM`, `SHARED`, `UNKNOWN`);
7. authority conflicts i commercial/compliance risks;
8. kratke evidence refs za svaku tačku.

Ne predstavljaj open issue kao dogovorenu odluku i ne vraćaj prihvaćenu odluku
u pregovore samo zato što postoji povezana operativna žalba.

## Anonimizovani regression fixtures

Ovi fixture-i su normativni acceptance testovi. Svaka buduća izmena skill-a mora
zadržati očekivane rezultate.

### TEST A — urgent scope mutates

**Chronology**

1. P1: urgent zahtev za zamenu 3 drvena stuba.
2. P2: elementi se menjaju na betonske.
3. P3: količina se menja na 6 stubova.
4. P4: KIR/kartica još nije izdata.
5. P5: potvrđeno je izvršenje svih 6 betonskih stubova.

**Expected**

- istorija čuva `3 wooden` kao `SUPERSEDED`, ne kao važeći scope;
- važeći scope pre izvršenja je `6 concrete`;
- P1 ne daje `READY_TO_WORK` samo zbog `URGENT`;
- P4 pokazuje blocker za radni dokument;
- P5 daje najmanje `WORK_EXECUTED`; lifecycle je
  `EXECUTED_PENDING_CLOSEOUT` dok closeout nije potvrđen;
- thread delta prepoznaje svaku mutaciju scope-a.

### TEST B — CAV ready for invoice

**Chronology**

1. Kartica je usaglašena.
2. Materijal je razdužen.
3. Partner piše: „Možete poslati račun.”

**Expected**

- billing `ready_to_invoice: CONFIRMED`;
- lifecycle `READY_TO_INVOICE`;
- kartica i razduženje ostaju zasebni evidence refs;
- nema implicitnog `INVOICED` niti `PAID`.

### TEST C — signed but incomplete

**Chronology**

1. Primljeni su potpisani KIR i grupni nalog.
2. Potvrđeno je da nedostaju grupni Excel i supporting dokumentacija.

**Expected**

- billing `signed: CONFIRMED`;
- billing `documentation_complete: NOT_CONFIRMED`;
- lifecycle `DOCUMENTATION_INCOMPLETE`;
- nije `READY_TO_INVOICE`.

### TEST D — strategic stop + operational dispute

**Chronology**

1. ADATEL najavljuje stop novih regionalnih radova.
2. Partner eksplicitno prihvata odluku, ali osporava status nezavršene postojeće
   lokacije L-17 i traži da se ona završi.

**Expected**

- strateška stop odluka je u `decision_already_accepted`;
- lokacija L-17 je u `open_issues` i `disputed_facts`;
- L-17 može biti `requested_exception_or_carve_out`;
- rezultat ne tumači poruku kao odbijanje strateške odluke.

### TEST E — work executed but closeout missing

**Chronology**

1. Fizički rad je potvrđeno završen.
2. Kartica čeka zvanični broj.
3. Dnevni log čeka potpis.

**Expected**

- billing `work_executed: CONFIRMED`;
- lifecycle `EXECUTED_PENDING_CLOSEOUT`;
- official number i log signature su odvojeni remaining blockers;
- nije `DOCUMENTATION_COMPLETE` niti `READY_TO_INVOICE`.

### TEST F — authority conflict

**Chronology**

1. Partner koordinator direktno daje terenski prioritet ekipi.
2. Interni koordinator navodi da raspored ekipe dolazi od client supervision-a.
3. Nema dokaza ko ima konačni autoritet za ovaj nalog.

**Expected**

- flag `AUTHORITY_CONFLICT`;
- blocker type `CONFLICTING_PRIORITY_AUTHORITY`;
- responsibility `SHARED` ako su potvrđene međuzavisne obaveze, inače
  `UNKNOWN`;
- nije automatski contractor/ADATEL fault;
- nije `READY_TO_WORK` dok authority nije razrešen.

## Regression guardovi

Pored testova A–F, svaka validacija mora potvrditi:

- Minimax grouping ne spaja različite poslovne teme;
- Drive strukturni signal ne postaje lažni dokaz potpisa/kompletnosti;
- compliance qualification ne daje pravni zaključak bez dokaza;
- Meeting Pack čuva accepted-vs-open razdvajanje;
- mark-read se ne izvršava bez eksplicitnog zahteva i ponovne provere niti;
- urgency nikada sama ne prolazi readiness gate;
- potpis nikada sam ne dokazuje billing readiness.

## Validation procedure

Pošto je skill prozni rule engine, validiraj ga fixture-by-fixture:

1. redukuj poruke hronološki;
2. zabeleži očekivani i dobijeni lifecycle, flags, facts, billing i responsibility;
3. zahtevaj potpuno poklapanje normativnih assertions iz testova A–F;
4. pokreni postojeće repo testove ako test harness postoji;
5. pokreni regression guardove iz prethodnog odeljka;
6. prijavi svako odstupanje; ne menjaj expected rezultat da bi test prošao.

## Changelog

### v2.0.0 — 2026-08-20

- uveden thread-state reducer sa istorijom facts i explicitnim state delta;
- razdvojeni readiness i urgency;
- razdvojeni work, signature, documentation, invoice i payment billing signali;
- uvedena evidence-based responsibility attribution po blocker tipu;
- dispute model razdvaja prihvaćene odluke od otvorenih pitanja;
- dodat `UNREAD_REVIEW` sa deduplikacijom niti i stabilnim brojevima;
- dodati anonimizovani real-world regression fixture-i A–F;
- očuvani guardovi za Minimax grouping, Drive structural signals, compliance
  qualification, Client/Partner Meeting Pack i mark-read safety.
