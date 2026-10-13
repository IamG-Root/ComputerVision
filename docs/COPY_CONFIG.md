# Importare la configurazione di un modulo o server esistente

Dalla directory della nuova installazione:

```bash
make copy_config_module SOURCE=../ComputerVision/module/config.py
```

Per percorsi con spazi:

```bash
make copy_config_module SOURCE="../vecchia installazione/module/config.py"
```

Per il server:

```bash
make copy_config_server SOURCE=../ComputerVision/server/config.py
```

`copy_config_module` aggiorna solo `module/config.py`; `copy_config_server` aggiorna
solo `server/config.py`. Il precedente `copy_config` resta un alias di
`copy_config_module`. La sorgente
rimane intatta. Il target usa Python di sistema (variabile PYTHON del Makefile),
non richiede dipendenze aggiuntive e può essere eseguito prima di `make module`.
In make gli argomenti posizionali sono altri target: usare `SOURCE=...`, non
`make copy_config ../ComputerVision/module/config.py`.

## Comportamento

- Importa i parametri presenti sia nella sorgente sia nella destinazione.
- Mantiene i parametri presenti soltanto nella destinazione. Quindi, partendo
  dalla vecchia configurazione, restano `CLOCK_SYNCHRONIZED = False` e
  `PROTOCOL_VERSION = 2`, o i valori già impostati nella nuova installazione.
- Se anche la sorgente contiene questi due parametri, li importa come gli altri.
- Sul server mantiene i nuovi parametri assenti nella sorgente, inclusi
  `TRACK_POLICY`, `CLASS_POLICIES` e le finestre temporali di fusione.
- Ignora e segnala parametri presenti soltanto nella sorgente.
- Conserva commenti e disposizione della destinazione. Mantiene espressioni
  come `TOPIC = "CV/" + MODULE_NAME` quando i nomi referenziati vengono importati.
- Legge i file con AST: non esegue import, funzioni o altro codice. Supporta
  valori letterali, contenitori, riferimenti a parametri già dichiarati e costruttori dati `dict(chiave=valore, ...)` e semplici
  operazioni `+`, `-`, `*`, `/`. Costrutti non supportati producono un errore prima
  della scrittura; non vengono ignorati silenziosamente.
- Prima della scrittura crea un backup accanto alla destinazione, con nome
  `config.py.backup-...`, e lo stampa. La sostituzione del file è atomica.
- Se il contenuto è già uguale non scrive né crea altri backup.

Viene importato anche MODEL_PATH: se la vecchia configurazione puntava a un
percorso diagnostico o assoluto, verificarlo. Per usare il modello della nuova
installazione il valore abituale è `models/swift_ncnn_model`.

Anteprima senza scrittura:

```bash
python tools/copy_config.py --source ../ComputerVision/module/config.py --dry-run
```

Esempio di installazione completa (configurare a modulo fermo):

```bash
git clone --branch patch https://github.com/IamG-Root/ComputerVision.git tentativo
cd tentativo
make module
make export_models
make copy_config_module SOURCE=../ComputerVision/module/config.py
./launcher.sh module debug
```

Per una migrazione del server, usare `make server` al posto di `make module`,
omettere `make export_models`, quindi eseguire `make copy_config_server SOURCE=...`
e avviare `./launcher.sh server`.

Anteprima server:

```bash
python tools/copy_config.py --source ../ComputerVision/server/config.py \
  --destination server/config.py --dry-run
```

Il percorso relativo della sorgente è interpretato rispetto alla directory in
cui make esegue il target. Non aggiungere al commit la configurazione specifica
del singolo edge né i relativi backup; conservarli nell'installazione locale.
