Questo script permette di valutare e confrontare lo storico di più corsi universitari utilizzando le statistiche pubbliche di AlmaLaurea. 

Partendo dai file CSV grezzi esportati dal portale, lo strumento genera una dashboard web interattiva (HTML) per l'analisi visiva dei trend storici e delle performance degli atenei.

*Nota: Il programma è stato sviluppato con AI. L'autore nega responsabilità per eventuali imprecisioni di lettura/visualizzazione/impostazione. Riservato per uso personale.*
I file di esempio forniti in questa repository sono di proprietà di AlmaLaurea.

## 🛠️ Utilizzo

**Download e formato**
- Scaricare le indagini statistiche in formato CSV con delimitatore "," e separatore decimale "." dal portale AlmaLaurea, pagina dedicata al **Profilo dei Laureati**.
- I file devono seguire rigorosamente il formato `ateneo-anno.csv` (es. `unibo-2022.csv`, `sapienza-2023.csv`).
- Preferibilmente organizzare i file in sottocartelle, esempio: `UNICAS/unicas-2024.csv`

**Esecuzione**
- Lanciare lo script da terminale:
   ```python almalaurea_dashboard.py```
  
Visualizzare il file `Dashboard_AlmaLaurea.html` nel browser.
