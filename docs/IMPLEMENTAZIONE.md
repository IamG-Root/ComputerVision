# Refactoring MC-MOT — relazione tecnica e guida di rilascio

Baseline: `e057a1199069d1468dd8ccd7824ae5f5570052f9`, branch upstream `main`.
Branch locale: `refactor/mcmot`. Data delle verifiche: 12 ottobre 2026.

## Stato della consegna

Implementazione integrata nei due entry point esistenti, con test software e replay
eseguiti. Non è una validazione dell'installazione: non erano disponibili Raspberry,
camera, display, broker dell'impianto, consumer Unity/FIWARE, telemetrie reali o ground
truth reale. Non sono stati effettuati deployment, merge o modifiche all'impianto.
Le soglie sono valori iniziali da tarare; non sono prestazioni garantite.

## Audit della baseline

L'edge acquisiva con Picamera2, ridimensionava con OpenCV, eseguiva YOLO NCNN e
proiettava il centro inferiore della bounding box sul pavimento. Un'associazione
al primo centro vicino manteneva gli ID locali. Il JSON edge era una lista di
`id`, `class`, `position`, senza età, sequenza o sessione.

Il server conservava l'ultimo messaggio per modulo, raggruppava per classe,
fondeva sequenzialmente le camere con Munkres e associava il risultato al ciclo
precedente. Il ciclo pubblicava ogni circa 200 ms, oltre al tempo di elaborazione.
Il README, tutti i moduli Python, i requisiti, Makefile e launcher sono stati letti.
Il modello binario è conservato; non è stato eseguito senza il relativo runtime.

Difetti verificabili nel sorgente:

| Componente | Difetto | Correzione attiva |
|---|---|---|
| `compute_class` originale | Buffer accumulato e riutilizzato come righe mentre si aggiungono risultati | Motore persistente e batch consumati una volta |
| `compute` originale | Rielaborazione snapshot e rinnovo `last_update` con l'ora del ciclo | Sequenze, scadenza, timestamp dell'osservazione |
| Matching originale | Padding a zero; gate applicato dopo ottimizzazione | Gate prima di Hungarian e scelte unmatched esplicite |
| Tracking edge | Due detection possono scegliere lo stesso ID | Assegnazione uno-a-uno con predizione locale |
| Validazione edge | Tracce non osservate vengono ripubblicate come reali | Solo tracce confermate osservate nel frame corrente |
| Contatori edge | Reset ogni 1001 frame; ID riutilizzabili | Sequenza monotona e sessione UUID per processo |
| Callback server | JSON/topic malformati senza gestione | Validazione atomica e limiti |
| MQTT | Connessione iniziale fallita senza loop; reconnect dal callback | `connect_async`, loop Paho e stop anche offline |
| Launcher | Argomenti multipli ignorati | Inoltro di tutti i flag, alias `draw` e `debug` preservati |
| Makefile | Rimozione NumPy dopo installazione | NumPy esplicito e nessuna disinstallazione automatica |
| Visualizer server | Legge `class` anziché `category`; Tk dal thread MQTT | Contratto POS corretto, coda e aggiornamento GUI nel thread principale |
| Proiezione inversa | Due valori normalmente, tre su errore | Due valori anche su errore, senza cambiare coordinate valide |

Le cause quantitative dei ghost nell'impianto, la qualità YOLO, il rumore effettivo,
le occlusioni e la frequenza degli scambi di ID non sono verificabili senza dati reali.

## Contratto pubblico invariato — COMPAT-001

`server/legacy_output.py` contiene i due metodi originali, preservati senza variazioni.
La suite confronta AST, fixture ottenute dalla baseline, tipi mediante JSON serializzato,
topic e chiamate reali di pubblicazione estratte dal main.

| Destinazione | Topic | Payload |
|---|---|---|
| Unity | `POS` | Array di `{id, category, position, timestamp}` |
| FIWARE | `/secret_key_cam/cam_1/attrs` | Un messaggio per entità: `{ident, classe, posx, posy, TimeInstant}` |

ID interi nel dominio 0–999; classi stringa invariate; posizione `[X,Z]` in metri.
Timestamp Unity: secondi Unix interi. FIWARE: `datetime.fromtimestamp(...).isoformat()`
locale, senza suffisso timezone, come la baseline. **Mantenere il timezone del server**:
normalizzarlo a UTC cambierebbe il comportamento del contratto.

Con zero entità Unity riceve `[]`, FIWARE zero messaggi. QoS 0 e retain false invariati.
Nessun campo di tracking viene aggiunto. Nessuna cancellazione FIWARE viene introdotta:
un consumer FIWARE che conserva l'ultima posizione continuerà a conservarla secondo
la propria politica. Smettere di pubblicare non equivale a cancellare la sua entità.
I timestamp ora riflettono l'ultima osservazione, senza rinnovo artificiale.

## Architettura nuova

- `tracking/local_tracker.py`: assegnazione gated nello spazio immagine; velocità
  stimata fra osservazioni, conferma consecutiva, occlusione e scadenza.
- `module/inference.py`: YOLO e proiezione esistente; eliminazione proiezioni non finite.
- `module/telemetry.py`: sessione UUID e snapshot v2, anche vuoto.
- `tracking/protocol.py`: validazione del messaggio prima di modificare lo stato.
- `server/processing.py`: ricezione concorrente protetta, coda limitata, riordino corto,
  elaborazione deterministica e adattamento delle geometrie opzionali.
- `tracking/global_tracker.py`: Kalman a velocità costante, gating spaziale e di
  Mahalanobis, associazione per camera, lifecycle e ID globali.
- `tracking/assignment.py`: Hungarian con unmatched espliciti, usando Munkres già
  presente nel server originale e aggiunto ai requisiti edge.
- `server/legacy_output.py`: confine pubblico invariato.
- `tracking/mqtt.py`: gestione comune dei client Paho.

Nessuna inferenza viene spostata sul server. Nessun modello aggiuntivo, database,
servizio cloud, video, immagine o embedding viene trasmesso.

### Associazione e fusione

Stato Kalman `[X,Z,vX,vZ]`; osservazione `[X,Z]`. Covarianza di misura dipendente
da confidence e quality; queste sono euristiche iniziali, non incertezze calibrate.
Il gate applica classe, età, distanza massima, velocità ammissibile e Mahalanobis.
La chiave locale coerente riduce il costo, ma non supera il gate fisico.

Ogni camera può correggere più tracce, una sola volta per detection e per traccia
nel batch. Più camere possono correggere la stessa traccia. Le camere e le detection
sono ordinate deterministicamente: invertire l'ordine di arrivo nello stesso batch
non cambia il risultato. Camere con nomi differenti possono cambiare l'ordine
numerico delle correzioni: non si rivendica invarianza alla rinomina delle camere.
Le correzioni sono sequenziali pesate, non una media geometrica indiscriminata.
Un termine minimo di covarianza limita l'eccesso di fiducia da camere correlate.

Gli snapshot entro 60 ms possono condividere un batch; non si presume simultaneità
esatta. Non c'è interpolazione delle singole detection all'interno di questa finestra:
a 3 m/s il disallineamento residuo può arrivare a 18 cm. Ridurre la finestra per
applicazioni che richiedono tolleranze più strette. Le osservazioni troppo tardive
rispetto al tempo già elaborato vengono scartate, senza correzioni retroattive.

### Lifecycle e ID

Tentative: richiede due osservazioni in istanti separati di almeno 80 ms. Otto camere
nello stesso istante non equivalgono a otto conferme. Confirmed: pubblicabile se
l'ultima misura è recente. Occluded: mantenuta internamente oltre publish_age.
Lost: oltre lost_age. Deleted: oltre delete_age, o scadenza di una candidata mai
confermata. Una vera osservazione coerente può riconfermare una traccia occlusa/persa.

Predizioni e assenza di nuovi messaggi non rinnovano last_real. L'output conserva
l'ultima posizione filtrata, senza extrapolazione pubblica indefinita. Le tracce
interne mantengono velocità e covarianza per il matching successivo.

L'allocatore globale evita collisioni con ID ancora presenti. A esaurimento del
dominio legacy sospende le nascite e segnala il problema. Gli ID possono essere
riutilizzati dopo eliminazione, come consentito dal dominio finito originale.
Non sono persistenti al riavvio del server. Gli ID locali non si riutilizzano nello
stesso processo; una nuova sessione edge separa i contatori dopo un riavvio.
Nessuna identificazione personale o biometrica.

## Protocollo edge → server

Topic interno invariato `CV/<MODULE_NAME>`, nome univoco che inizia con `MODULE`.

```json
{"version":2,"module_id":"MODULE1","session_id":"uuid-per-processo",
 "frame_id":123,"capture_timestamp":1700000000.125,
 "clock_synchronized":false,"processing_age":0.18,
 "entities":[{"local_track_id":7,"class":"person","position":[1.2,3.4],
 "confidence":0.91,"bbox":[100,200,180,350],"track_state":"observed",
 "observation_age":0.0,"quality":1.0}]}
```

`bbox` è diagnostico, non usato nel matching server. La confidence viene da YOLO;
quality vale inizialmente 1 e può essere ridotta dal modello geometrico.
Solo `observed` con età zero alimenta il tracker: stati previsti, candidati e
occlusi non sono prove nuove. Le coordinate non finite e gli ID duplicati nello
stesso snapshot invalidano l'intero messaggio. Non sono accettati messaggi retained.

- Snapshot vuoto: un nuovo frame elaborato senza osservazioni; non è un guasto.
- Nessun messaggio: nessun rinnovo delle tracce; timeout monotoni.
- Modulo inattivo: le sue osservazioni non vengono ripetute.
- Riavvio: nuova sessione; coda precedente eliminata, ID locali separati.
- Duplicati/fuori ordine: frame non crescente nella sessione scartato.
- Sessione vecchia: le ultime 32 sessioni ritirate per camera sono rifiutate.
- Legacy v1: accettato come evento nuovo alla ricezione, consumato una sola volta.
  Non può distinguere retransmission da una misura statica legittima; non può
  verificare timestamp, sessione o detection previste. Migrare tutti gli edge.

Limiti default: 256 entità/snapshot, 256 KiB/payload, 256 snapshot in coda, 128 moduli.
La coda piena scarta il più vecchio elemento inserito. L'elenco moduli resta limitato
ma mantiene le sequenze anche durante inattività. Rinominare più di 128 moduli richiede
configurazione appropriata o riavvio controllato. Questi limiti sono protezioni,
non capacità real-time misurate per 128 camere.

## Tempo e sincronizzazione

Picamera2 fornisce SensorTimestamp dal sensore; viene convertito da CLOCK_BOOTTIME
all'orologio civile locale prima del ridimensionamento. In assenza di metadata,
il fallback è il tempo di ricezione del frame, meno accurato.

Verificare NTP/Chrony su tutti i nove dispositivi: `chronyc tracking` e
`chronyc sources -v`, stesso riferimento e offset misurati entro la tolleranza
richiesta. Configurazione del servizio e disponibilità pacchetti dipendono dall'OS
installato; non sono state modificate qui. Abilitare `CLOCK_SYNCHRONIZED=True`
solo dopo questa verifica e monitorare continuamente gli offset.

Con clock sincronizzato il server trasferisce capture_timestamp sulla propria
scala monotona usando l'ora di ricezione. Scarta acquisizioni oltre un secondo o
oltre 250 ms nel futuro. Con clock non sincronizzato usa il tempo di ricezione
meno processing_age, quindi evita di ignorare la latenza YOLO, ma **non conosce la
latenza di rete**. Non può dimostrare la freschezza di un pacchetto ritardato dalla
rete con orologi non sincronizzati. Il flag è configurato, non è una verifica NTP
automatica. Pacchetti con processing_age oltre MAX_SNAPSHOT_AGE sono scartati.

## Parametri da tarare

| Parametro server | Default | Significato |
|---|---:|---|
| confirm_hits | 2 | Conferme temporali globali |
| publish_age | 0.6 s | Età massima pubblicabile |
| lost_age | 1.5 s | Passaggio a Lost |
| delete_age | 4 s | Durata massima recuperabile |
| max_distance | 1.2 m | Gate spaziale superiore |
| max_speed | 3 m/s | Gate dinamico |
| measurement_sigma | 0.15 m | Scala iniziale rumore di misura |
| acceleration | 1.5 m/s² | Rumore del modello di movimento |
| gate | 9.21 | Soglia Mahalanobis quadratica |
| REORDER_WINDOW | 0.08 s | Attesa minima prima dell'elaborazione |
| FUSION_WINDOW | 0.06 s | Ampiezza batch multi-camera |
| MAX_SNAPSHOT_AGE | 1 s | Età massima accettata |

`CLASS_POLICIES` sovrascrive queste voci per i nomi ESATTI delle classi del modello;
non vengono inventate mappature di classi. Per pallet statici si può ridurre acceleration,
ma rimangono mobili e associabili dopo uno spostamento. Tarare su telemetrie reali.

Edge: MAX_DISTANCE=50 pixel, MAX_FRAME_DIFF=10 frame, conferma dopo
MIN_VALID_SEEN_COUNT+1=5 osservazioni consecutive, come la soglia originale.
Questi valori dipendono da FPS e scala immagine. Con YOLO lento, acquisizione, inferenza,
buffering e periodo server possono già superare publish_age: **misurarli prima del
rilascio e tarare insieme publish_age, MAX_SNAPSHOT_AGE e conferme**, altrimenti si
possono sopprimere entità vere. Non aumentare i timeout senza misurare i ghost.

## Geometria e PDF allegato

Esaminate le tabelle e le planimetrie delle pagine 6 e 9–16, oltre alle specifiche
ottiche a pagina 8. Il riferimento descrive otto dispositivi perimetrali, altezza
5 m, inclinazioni 25–30°, FOV 51.4° × 39.4° e risoluzione 1640×1232.
Le tabelle usano anche `MAX` senza una mappatura numerica univoca degli assi runtime.
Le immagini mostrano sovrapposizioni e ostacoli, ma non poligoni di visibilità
rilevati con precisione. Non sono state trasformate in vincoli rigidi.

Il repository contiene una sola configurazione: altezza 2.545 m, pitch 35°,
FOV 53° × 41°, posizione 4.5/0.8, orientamento 1. Nessuno di questi valori è
stato sostituito con quello del PDF. Mancano gli otto file runtime effettivi.

`tracking.visibility.footprint` calcola un quadrilatero teorico da posizione,
altezza, inclinazione, FOV e orientamento nelle convenzioni esistenti. Ritorna
None se il FOV interseca l'orizzonte. `CAMERA_VISIBILITY` è vuoto di default.
Può contenere polygon, margin (metri) ed exclusions per modulo. Fuori area o
in zone occluse il peso viene ridotto, mai azzerato. Verificare sul campo i poligoni
prima dell'abilitazione; non rappresentano automaticamente tutte le occlusioni.

Il §6.3 del PDF descrive assenza di visualizzazione immagini, mentre il prompt
richiede esplicitamente il debug locale. È stata applicata la richiesta esplicita:
`--draw` resta temporaneo e locale. Questo scostamento deve essere recepito nella
documentazione dell'impianto. Nessun nuovo salvataggio immagini è stato introdotto;
lo strumento di raccolta immagini già esistente resta separato e non viene avviato.

## Debug — DEBUG-001

Comandi dalla radice del progetto:

```bash
cvenv/bin/python module/main.py
cvenv/bin/python module/main.py --draw
cvenv/bin/python module/main.py --debug
cvenv/bin/python module/main.py --draw --debug
./launcher.sh module draw debug
```

Verde: osservata confermata. Arancione: candidata/occlusa, etichetta esplicita.
Bounding box, confidence, classe, ID, punto di proiezione e X/Z sono sovrapposti
su una copia del frame. Una traccia occlusa mostra l'ultimo box, non una nuova
misura. Il clic conserva la lettura delle coordinate. `q` o la chiusura finestra
spengono solo la diagnostica; SIGINT/SIGTERM chiudono l'applicazione.

Headless: messaggio e tracking senza GUI. Il controllo preliminare OpenCV avviene
in un processo breve per isolare eventuali abort del backend Qt. Il debug testuale
usa logging e funziona via SSH: inferenza, associazioni, stati, posizione,
frame/acquisizione, tempi/FPS, MQTT e rifiuti server. Nessun salvataggio automatico.

## Verifica eseguita

`docs/tests.txt`: 70 test unittest superati sul computer di sviluppo. Comprendono
contratti, publisher vuoto/multiplo, 1/2/3/8 camere, persone vicine e incrocio sintetico,
classi diverse, outlier, lifecycle, handoff, staticità, ID capacity, snapshot malformati,
stale, duplicati, riavvii, timestamp, protocolli, tutti i flag, headless, finestra chiusa,
frame non mutato, camera indisponibile e MQTT offline/ripristino mediante mock.
I mock non equivalgono a test hardware o broker reali.

```bash
python -m unittest discover -s tests -v
python tools/replay.py tests/fixtures/replay.jsonl --engine baseline --output baseline.jsonl
python tools/replay.py tests/fixtures/replay.jsonl --engine new --output new.jsonl
python tools/metrics.py tests/fixtures/truth.jsonl new.jsonl
python tools/benchmark.py
```

Replay sintetico identico: 3 camere, 2 persone, 15 frame, ultimo evento a 2.8 s,
tick server 200 ms, sei secondi di coda senza osservazioni. Input v1 per confronto
comune; il replay può adattare v2 alla baseline. Nessuna latenza di rete simulata
in questo scenario. Output integrali e metriche sono nei file JSON/JSONL in docs.

| Risultato sintetico | Baseline | Nuovo |
|---|---:|---:|
| Numero massimo pubblicato | 4 | 2 |
| Ultimo tick non vuoto | 8.0 s | 3.2 s |
| True positive per tick | 30 | 26 |
| False positive per tick | 134 | 4 |
| False negative per tick | 0 | 4 |
| ID switches | 12 | 0 |
| Detection duplicate | 30 | 0 |
| IDF1 | 0.2371 | 0.8667 |

Le mancate rilevazioni iniziali sono il costo della conferma e del buffering; le
false presenze finali riflettono il breve periodo di tolleranza. L'errore medio
nuovo è circa 3.6 cm in questo percorso artificiale con ritardo di un tick: non
misura l'accuratezza della calibrazione reale. Le metriche sono calcolate con
matching classe/distanza a 0.5 m, conteggi per tick e associazione globale IDF1;
non sono una certificazione MOTChallenge. Non vengono riportati tassi di falsi
positivi su veri negativi non definiti per questo scenario.

Benchmark `docs/benchmark.json`: Linux x86_64, Python 3.12.14, NumPy 2.3.5;
40 cicli per scenario, otto camere, senza YOLO, broker o GUI. p95 circa 0.63 ms
con 1 oggetto, 7.24 ms con 10 e 30.64 ms con 25. RSS massimo del processo circa
24–25 MiB. Il RSS è cumulativo nel processo, non memoria isolata per scenario.
CPU seconds e wall seconds sono registrati; non estrapolare questi numeri al Pi 4.
La complessità Hungarian e il doppio ciclo dei costi richiedono misure al carico reale.
Latenza end-to-end, traffico MQTT effettivo e CPU/RAM dei Raspberry sono da misurare.

## Installazione, shadow e rollback

1. Conservare checkout originale e tutte le configurazioni runtime su ogni dispositivo.
2. Usare una copia separata per questo branch; Python >=3.10, raccomandato l'ambiente
   Raspberry Pi OS già funzionante. Picamera2/OpenCV/libcamera provengono dall'OS.
   Il repository non definisce una versione OS; ARM non è stato verificato qui.
3. Eseguire `make server` / `make module` negli ambienti appropriati. I requisiti YOLO,
   ONNX, NCNN, Paho e Shapely preesistenti sono preservati. Munkres è aggiunto all'edge,
   NumPy è esplicito. Verificare il binario NCNN sulla specifica architettura.
4. Ripristinare i valori runtime dei config senza perdere i nuovi parametri.
   Non usare `MODULEX` per più dispositivi; MQTT richiede client ID univoci.
5. Eseguire i test software e poi le prove hardware sotto elencate.
6. Per osservare senza pubblicare: `python server/main.py --shadow --debug`.
   Usa client ID SERVER_SHADOW e non si connette al publisher FIWARE. Il server
   produttivo rimane l'unico publisher. In shadow `--draw` legge ancora POS del
   publisher produttivo: non mostra il risultato candidato; usare replay e log.
7. Migrare PRIMA il server, che accetta v1 e v2. Migrare poi un edge alla volta.
   Non inviare v2 a un server originale: non lo comprende.
8. Per attivare il nuovo publisher, arrestare l'originale prima di avviare il nuovo
   senza `--shadow`. Mai due publisher autorevoli in parallelo.
9. Rollback: fermare gli edge v2, ripristinare gli edge originali o impostare
   PROTOCOL_VERSION=1 e riavviarli; poi ripristinare il server originale e la sua
   configurazione. Conservare gli ambienti precedenti evita rollback dei pacchetti.
   Riavviare il server azzera lo stato e può cambiare gli ID: programmare il passaggio.

Nessuna PR remota è stata creata. Il branch e il pacchetto permettono revisione e
applicazione; la disponibilità di scrittura remota non è stata verificata.

## Prove hardware e criteri di rilascio

- Eseguire almeno 30 minuti con otto camere e carico massimo previsto; misurare
  `pidstat -r -u -p <pid> 1`, tempi server, età delle osservazioni e traffico broker.
- Verificare frame reali, colori e timestamp sensore sui Pi 5; tutti e quattro i
  modi CLI; SSH headless; `q`, chiusura finestra, SIGINT e SIGTERM; riapertura camera.
- Disconnettere broker prima dell'avvio, durante tracking, poi ripristinare;
  nessuna coda stale deve riapparire. Provare perdita di singola camera e riavvio.
- Persona singola, due persone affiancate, incrocio, occlusioni da macchinari,
  passaggio tra camere, entrata/uscita, pallet statico e poi mosso, muletto in moto.
- Registrare SOLO telemetrie e annotazioni di riferimento per replay. Campionare
  con ID di verità indipendenti, senza identificare personalmente gli operatori.
- Confrontare FP/FN, duplicati, switches, IDF1, errore di posizione, durata ghost,
  latenza acquisizione/pubblicazione. Definire soglie di accettazione prima del test.
- Confermare sul consumer reale che array vuoto, tipi, timestamp, topic e cardinalità
  siano invariati. Qualunque regressione COMPAT-001 o DEBUG-001 blocca il rilascio.
- Misurare deriva orologi e verificare il comportamento quando NTP è indisponibile.

Restano ambiguità inevitabili senza appearance: traiettorie identiche, occlusioni
lunghe e reingressi fuori dal timeout non garantiscono continuità dell'ID. Il sistema
non è certificato per funzioni safety-critical: servono validazione dell'impianto,
analisi di rischio e verifiche richieste dal processo di sicurezza applicabile.

## Riferimenti API verificati

- https://docs.libcamera.org/master/internal-api/namespacelibcamera_1_1controls.html
  per SensorTimestamp e CLOCK_BOOTTIME.
- https://eclipse.dev/paho/clients/python/docs/ per loop e riconnessione.

Questi riferimenti non sostituiscono le verifiche sulle versioni installate.
