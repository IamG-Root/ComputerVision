# Esportazione NCNN riproducibile sui Raspberry Pi 5

Questa correzione si basa sul branch `patch` remoto `1f7cc0c`.
Il confronto sul Raspberry ha verificato che lo stesso ONNX e lo stesso ambiente
producono un modello eseguibile con PNNX 20260526, mentre l'export precedente con
PNNX 20260704 causa segmentation fault. Il modello riconvertito ha superato sia
tre inferenze sintetiche sia l'avvio dell'edge, incluse le modalità debug e draw.

## Installazione su un nuovo edge Linux ARM64

```bash
git clone --branch patch https://github.com/IamG-Root/ComputerVision.git
cd ComputerVision
make module
make export_models
# Configurare module/config.py per questo edge, come prima.
./launcher.sh module
```

Il target è `module`, non `model`. MODEL_PATH resta `models/swift_ncnn_model`.
Non è necessario attivare manualmente il virtualenv prima dei comandi make.
Serve accesso a Internet per le dipendenze e per il primo download di PNNX.
Gli eventuali auto-install dell'esportatore Ultralytics usano il pip del virtualenv.

## Modifiche distribuite

- Una sola riga modificata nel Makefile: la chiamata dentro `export_models`.
- `munkres==1.1.4` aggiunto a `requirements/module.txt`.
- `tools/export_ncnn.py`: download PNNX Linux ARM64 20260526 con verifica SHA256,
  export isolato e tre inferenze di verifica prima dell'attivazione.
- Test automatici e questa documentazione.

Le altre regole del Makefile, compresa `uninstall_numpy`, sono invariate.
`requirements/server.txt`, codice di tracking, payload MQTT, calibrazione e GUI
sono invariati rispetto a `1f7cc0c`. Non sono inclusi virtualenv, configurazioni
specifiche del Raspberry dell'utente o modelli NCNN preesportati.

## Cosa fa make export_models

1. Verifica di essere su Linux ARM64 e controlla il modello .pt.
2. Scarica/cachea l'archivio ufficiale in `logs/pnnx/`, verificando il SHA256
   anche quando usa la cache. Non seleziona la release più recente.
3. Estrae solo l'eseguibile verificato in una directory temporanea e imposta
   directory di lavoro e PATH per forzarne l'uso in Ultralytics 8.3.217.
   Non riutilizza eventuali PNNX presenti nel progetto o nel virtualenv.
4. Esporta una copia del .pt e controlla la presenza dei file NCNN e metadata.
5. Esegue tre inferenze sintetiche in un sottoprocesso (timeout 180 secondi).
6. Solo dopo il successo attiva `models/<nome>_ncnn_model`. Un modello precedente
   viene conservato in `logs/ncnn-backups/`. Un errore di attivazione ripristina
   il modello precedente, quando il ripristino filesystem è possibile.

Log completo per modello: `logs/<nome>.log`. Export, checksum o inferenza falliti
fanno terminare make con errore; il modello precedente rimane disponibile.
I modelli di una stessa invocazione sono pubblicati singolarmente: se il secondo
fallisce, il primo già verificato resta attivo. Non eseguire export concorrenti
né esportare mentre il modulo sta caricando il modello. `make clean` elimina
anche logs e relativi backup, come nella regola originale.

L'ONNX intermedio è temporaneo: questo comando pubblica soltanto il modello NCNN
verificato. Un eventuale vecchio `models/<nome>.onnx` non viene aggiornato.
La verifica sintetica intercetta il crash osservato, ma non misura l'accuratezza
delle detections. Le dipendenze indirette Python restano quelle risolte dai
requirements originali: questa correzione fissa PNNX, non congela tutto l'ambiente.

## Verifica del pacchetto

Verifica locale eseguita: 78 test superati. Verificati inoltre download reale,
SHA256 dell'archivio ufficiale ed eseguibile ELF AArch64 estratto. Il convertitore
ARM64 non è stato eseguito sulla macchina x86 usata per preparare il pacchetto.

```bash
python -m unittest discover -s tests -v
```

I test del wrapper verificano download/cache, checksum, isolamento, fallimento
export, segmentation fault simulato, timeout, backup/ripristino e propagazione
degli errori al Makefile. Sono test software: l'export ARM64 completo del nuovo
wrapper deve essere collaudato su un edge prima della distribuzione agli altri.

Fonte del convertitore:
https://github.com/pnnx/pnnx/releases/tag/20260526

SHA256 dell'archivio `pnnx-20260526-linux-aarch64.zip`:
`5ec705eba0f9bec09652f966244201f5af2bcf8657b1580c46028fe83183f8b1`
