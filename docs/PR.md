# Ridurre duplicazioni e rinnovi di snapshot obsoleti nel tracking multi-camera

La baseline può assegnare più detection allo stesso ID locale, accumulare risultati
nella fusione tra camere e rinnovare presenze riutilizzando l'ultimo snapshot.
Questo branch sostituisce il percorso attivo con tracking locale uno-a-uno,
snapshot versionati e un tracker globale persistente con scadenza delle misure.

I serializzatori Unity e FIWARE sono preservati e verificati contro fixture della
baseline e AST originali. Il debug edge rimane disponibile con `--draw`, `--debug`
e la loro combinazione; chiudere la finestra non interrompe il tracking.

Validazione: 70 test software superati; replay sintetico baseline/nuovo e benchmark
CPU su x86_64 inclusi in `docs/`. Nessun test hardware, broker reale o consumer reale.
La guida dettaglia parametri, limiti, shadow, migrazione server-prima e rollback.
Non effettuare rilascio prima della taratura su latenze reali e della validazione
COMPAT-001/DEBUG-001 sull'installazione.
