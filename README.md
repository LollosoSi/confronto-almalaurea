# confronto-almalaurea

Questo script permette di valutare e confrontare lo storico di più corsi universitari con le statistiche pubbliche di AlmaLaurea. 

Partendo dai file CSV grezzi esportati dal portale, lo strumento decodifica la struttura gerarchica complessa dei dati e genera in automatico una dashboard web interattiva (HTML) per l'analisi visiva dei trend storici e delle performance degli atenei.

*Nota: La logica di parsing avanzato e l'interfaccia UI sono state sviluppate con il supporto dell'Intelligenza Artificiale.*

## ⚡ Caratteristiche principali

* **Zero dipendenze:** Scritto in Python puro, non richiede l'installazione di pacchetti esterni (nessun `pip install`).
* **Parsing intelligente:** Riconosce dinamicamente sezioni, sottogruppi e marcatori invisibili nei CSV di AlmaLaurea.
* **Dashboard interattiva:** Genera un file HTML autonomo con grafici a linee e a torta (powered by Plotly.js).
* **Executive Summary:** Raggruppa in automatico i KPI (Voto medio, Età, Tirocini, Soddisfazione) in schede di rapida consultazione.
* **Scala dinamica:** Adatta automaticamente l'asse Y in base alla metrica analizzata (es. 80-115 per i voti, 0-105 per le percentuali).

## 🛠️ Utilizzo

1. **Download:** Scaricare le indagini statistiche in formato CSV dal portale AlmaLaurea.
2. **Rinominare:** I file devono seguire rigorosamente il formato `ateneo-anno.csv` (es. `unibo-2022.csv`, `sapienza-2023.csv`).
3. **Setup:** Posizionare i file CSV nella stessa directory dello script Python.
4. **Esecuzione:** Lanciare lo script da terminale:
   ```bash
   python almalaurea_dashboard.py
5. **Analisi:** Aprire il file `Dashboard_AlmaLaurea.html` generato per visualizzare i risultati nel browser.
