# ITRA: IT Risk Assessment

ITRA (IT Risk Assessment) è un'applicazione web progettata per la gestione e l'esecuzione di valutazioni annuali del rischio informatico. Il sistema permette di definire un'anagrafica "master" di componenti tecnologici, minacce e controlli, e di utilizzarla come template per creare "campagne" di valutazione annuali, che rappresentano snapshot immutabili nel tempo.

## Indice

- Architettura
- Stack Tecnologico
- Concetti Fondamentali
- Logiche di Business e Funzionalità Principali
- Dettaglio Moduli e Modelli
- Interfaccia di Amministrazione (Django Admin)
- API REST
- Installazione e Avvio
- Possibili Sviluppi Futuri

## Architettura

Il progetto segue un'architettura disaccoppiata (decoupled), ideale per ambienti enterprise moderni, con una netta separazione tra backend e frontend.

-   **Backend**: Un'applicazione basata su **Django** e **Django REST Framework**. Espone API RESTful per la gestione di tutte le entità del dominio e serve la potente interfaccia di amministrazione di Django per la gestione dei dati.
-   **Frontend**: Un'applicazione Single Page Application (SPA) sviluppata con **Vine** (o framework JavaScript simile, es. Vue.js, React, Angular) che interagisce con il backend tramite le API per offrire un'esperienza utente ricca e reattiva.

La struttura del repository riflette questa separazione:
```
itra/
├── backend/      # Applicazione Django (API + Admin)
├── frontend/     # Applicazione SPA (Vine)
└── README.md
```

## Stack Tecnologico

### Backend
-   **Linguaggio**: Python
-   **Framework**: Django
-   **API**: Django REST Framework
-   **Database**: PostgreSQL (raccomandato in produzione), SQLite (per sviluppo)
-   **Librerie Chiave**:
    -   `django-simple-history`: Per il versioning e la storicizzazione dei modelli.
    -   `django-import-export`: Per funzionalità di import/export nell'admin.
    -   `django-mptt`: Per la gestione efficiente di strutture ad albero (es. Catene Tecnologiche).
    -   `numpy` (opzionale): Utilizzato per calcoli avanzati sulle matrici.

### Frontend
-   **Framework**: Vine (o framework JavaScript simile, es. Vue.js, React, Angular)
-   **Gestore Pacchetti**: npm / yarn

## Concetti Fondamentali

L'architettura si basa su una distinzione cruciale tra dati **Master** e dati di **Campagna**.

*   **Dati Master**: Oggetti di anagrafica (Scenari, Minacce, Asset, etc.) non associati a nessuna campagna specifica (il loro campo `campagna` è `NULL`). Rappresentano il template di base, la "verità" corrente che può essere modificata nel tempo.
*   **Dati di Campagna**: Copie esatte dei dati master create al momento del lancio di una nuova campagna. Ogni oggetto clonato è legato alla campagna specifica, garantendo che le valutazioni di un anno siano basate su una fotografia precisa e immutabile dell'infrastruttura e dei rischi di quell'anno.

## Logiche di Business e Funzionalità Principali

*   **Popolamento Automatico delle Campagne**: Alla creazione di una nuova `Campagna`, il suo metodo `popola_from_master()` viene eseguito per clonare tutti gli oggetti "master" (`campagna=NULL`), rispettando le dipendenze tra modelli.

*   **Struttura Tecnologica degli Asset**: Ogni `Asset` possiede una "struttura tecnologica" implementata come un albero gerarchico (`django-mptt`). Questa struttura è composta da oggetti `NodoStruttura`. Ogni `NodoStruttura` è esclusivo per l'albero di un `Asset`, ma fa riferimento a un `ElementType` che è un componente condiviso e riutilizzabile (es. "Database", "Server Applicativo"). Questo permette di definire architetture complesse e specifiche per ogni asset, riutilizzando al contempo le definizioni e le matrici di rischio dei componenti tecnologici di base.

*   **Separazione Dati Master/Campagna nell'Admin**: Per garantire l'integrità dei dati, l'interfaccia di amministrazione è progettata per operare primariamente sui record "master".
    *   Le viste elenco per le anagrafiche principali (`Asset`, `Controllo`, etc.) mostrano di default solo i record master (`campagna` è NULL). Un filtro (`Tipo di Record`) permette di visualizzare tutti i record.
    *   Accedendo al **Dashboard di una Campagna**, tutte le viste elenco e i moduli di modifica vengono automaticamente filtrati per mostrare solo i dati pertinenti a quella campagna, garantendo un contesto di lavoro isolato e coerente.

*   **Creazione di `ElementType` Base e Derivati**: Un `ElementType` può essere creato in due modi:
    *   **Base** (`is_base=True`): Un componente fondamentale la cui matrice di rischio (minacce vs. controlli) è definita manualmente.
    *   **Derivato** (`is_base=False`): Un componente astratto la cui matrice di rischio è **calcolata automaticamente** aggregando le matrici dei suoi componenti figli. Quando si definiscono i componenti di un `ElementType` derivato, non è possibile selezionare l'elemento stesso per prevenire cicli di ricorsione.

*   **Assegnazione dei Controlli alle Matrici**: Un `Controllo` è intrinsecamente legato a un singolo `ElementType` tramite il suo campo `elementtype`. Questa associazione definisce la "colonna" che il controllo rappresenta nella matrice di rischio di quell'`ElementType`. Per includere un controllo in una matrice, è necessario modificare l'oggetto `Controllo` e assegnarlo all'`ElementType` desiderato.

*   **Immutabilità delle Campagne Chiuse**: Nell'interfaccia di amministrazione, se una campagna ha `status = 'close'`, tutti i suoi dati diventano read-only per garantirne l'integrità storica.

*   **Storico dei Dati**: Tutti i modelli principali integrano `django-simple-history` per tracciare ogni creazione, modifica e cancellazione, fornendo un audit trail completo.

## Dettaglio Moduli e Modelli

Il backend è suddiviso in moduli Django, ognuno con una responsabilità specifica.

### `campagne`
L'app orchestratrice del sistema, gestisce le campagne di valutazione.
*   **`Campagna`**: Modello centrale che definisce una valutazione annuale.
    *   `anno` (PositiveIntegerField): Anno della campagna.
    *   `descrizione` (CharField): Descrizione testuale della campagna.
    *   `data_inizio` / `data_fine` (DateField): Periodo di validità della campagna.
    *   `status` (CharField): Stato della campagna ('open' o 'close').
    *   `perimetro` (ManyToManyField): Asset inclusi nella valutazione.

### `assets`
Gestisce le istanze concrete di sistemi e applicazioni.
*   **`Asset`**:
    *   `nome` (CharField): Nome univoco dell'asset all'interno della sua campagna (o tra i master).
    *   `struttura_tecnologica` (Albero MPTT di `NodoStruttura`): Rappresenta l'architettura tecnologica dell'asset. Non è un campo diretto, ma una relazione inversa ai nodi che compongono l'albero.
    *   `cmdb` (CharField): ID di riferimento nel Configuration Management Database (CMDB).
    *   `descrizione` (TextField): Descrizione dettagliata dell'asset.
    *   `utente_responsabile` / `responsabile_applicativo` (ForeignKey a `User`): Figure di responsabilità.
    *   `legal_entity` (CharField): Entità legale di appartenenza.
    *   `campagna` (ForeignKey): La campagna a cui l'asset è associato (`NULL` per i record master).
*   **`NodoStruttura`**: Un nodo nell'albero MPTT della struttura tecnologica di un `Asset`.
    *   `asset` (ForeignKey): L'asset a cui questo nodo appartiene.
    *   `element_type` (ForeignKey): Il tipo di componente tecnologico condiviso che questo nodo rappresenta.
    *   `parent` (TreeForeignKey): Il nodo genitore all'interno della stessa struttura dell'asset.
    *   `nome_specifico` (CharField): Un nome opzionale per sovrascrivere quello dell'ElementType in un contesto specifico.

### `elementtypes`
Definisce i mattoni astratti di una catena tecnologica e le loro matrici di rischio.
*   **`ElementType`**: Un tipo di componente (es. "database", "server").
    *   `is_base` (BooleanField): `True` se la sua matrice è definita manualmente; `False` se è "derivato" e la sua matrice è calcolata aggregando i suoi componenti.
    *   `minacce` (ManyToManyField): Definisce le **righe** della matrice di rischio per questo `ElementType`.
*   **`ValoreElementType`**: Rappresenta una **cella** nella matrice di rischio, collegando `ElementType`, `Minaccia` e `Controllo` con un `valore` numerico.

#### Gestione della Matrice di Rischio

La gestione della matrice di un `ElementType` di base è completamente integrata nella sua pagina di modifica nell'interfaccia di amministrazione, per un'esperienza utente fluida e condensata:

1.  **Gestione Righe (Minacce)**: Le minacce che compongono le righe della matrice possono essere aggiunte o rimosse tramite il selettore "Minacce" nella sezione "Configurazione Matrice".
2.  **Gestione Colonne (Controlli)**: I controlli che formano le colonne sono gestiti tramite la sezione "Controlli (colonne della matrice)" in fondo alla pagina. Qui è possibile aggiungere nuovi controlli, che verranno automaticamente associati a questo `ElementType`.
3.  **Gestione Valori**: Per gli `ElementType` di base, un editor a griglia per la matrice appare direttamente in fondo alla pagina di modifica. È possibile inserire, modificare o cancellare i valori numerici in ogni cella. Tutte le modifiche (all'`ElementType`, alle righe, alle colonne e ai valori) vengono salvate contemporaneamente con un unico click sul pulsante "Salva".

### `controlli`
Gestisce le misure di sicurezza e i processi.
*   **`Controllo`**:
    *   `nome` (CharField): Nome del controllo.
    *   `tipologia_controllo` (CharField): Scelta tra 'Tecnologico', 'Processo', etc.
    *   `peso_controllo` (FloatField): Calcolato automaticamente in base alla `tipologia_controllo`.
    *   `categoria_controllo` (CharField): 'preventive' o 'detective'.
    *   `elementtype` (ForeignKey): Il tipo di elemento a cui il controllo è associato, definendo una **colonna** della sua matrice.

    Il `peso_controllo` viene assegnato automaticamente in base alla `tipologia_controllo` secondo la seguente tabella:

| Tipologia Controllo      | Peso |
| ------------------------ |:----:|
| Documentale              | 0.4  |
| Tecnologico              | 0.5  |
| Processo                 | 0.6  |
| Misurazione base         | 0.8  |
| Misurazione intermedia   | 0.9  |
| Misurazione avanzata     | 1.0  |

### `minacce` e `scenari`
Definiscono i rischi.
*   **`Scenario`**: Descrizione di uno scenario di rischio (es. "Perdita di Dati").
*   **`Minaccia`**: Una minaccia specifica (es. "Accesso non autorizzato al DB"), collegata a uno `Scenario`.

## Interfaccia di Amministrazione (Django Admin)

L'interfaccia admin (`/admin`) è il cuore operativo per la gestione dei dati master e il monitoraggio delle campagne ed è stata potenziata per supportare il flusso di lavoro di ITRA.

*   **Import/Export**: Tutti i modelli principali supportano l'import/export di dati tramite `django-import-export`.
*   **Dashboard di Campagna**: Ogni campagna ha un link "Dashboard" che porta a una vista personalizzata con link a tutte le anagrafiche già filtrate per quella specifica campagna.
*   **Gestione Master/Campagna**: Un filtro personalizzato (`Tipo di Record`) permette di visualizzare di default solo i dati "Master", nascondendo la complessità dei dati clonati.
*   **Visualizzazione Matrici**: Nelle viste admin di `ChainTypeNode`, viene mostrata la dimensione della matrice di rischio associata.

## API REST

Il progetto espone `ViewSet` CRUD per tutti i modelli principali utilizzando **Django REST Framework**. Le API, disponibili sotto il prefisso `/api/`, supportano il filtraggio e sono il punto di contatto per il frontend e per integrazioni esterne.

**Endpoint Principali:**
*   `/api/assets/`
*   `/api/nodi-struttura/`
*   `/api/campagne/`
*   `/api/controlli/`
*   `/api/elementtypes/`
*   `/api/minacce/`
*   `/api/scenari/`

## Installazione e Avvio

### Prerequisiti

-   Python 3.8+
-   pip & `virtualenv`
-   Node.js e `npm` (per il frontend)
-   Un database (es. PostgreSQL, SQLite per sviluppo)

### Backend Setup

1.  **Navigare nella directory del backend**:
    ```sh
    cd itra/backend
    ```

2.  **Creare e attivare un ambiente virtuale**:
    ```sh
    python -m venv venv
    source venv/bin/activate  # Su Windows: venv\Scripts\activate
    ```

3.  **Installare le dipendenze**:
    *(Assicurarsi di avere un file `requirements.txt` nella directory `backend/`)*
    ```sh
    pip install -r requirements.txt
    ```

4.  **Applicare le migrazioni del database**:
    ```sh
    python manage.py migrate
    ```

5.  **Popolare il database con dati di test (consigliato)**:
    Il comando `seed_data` popola il DB con anagrafiche master, alberi tecnologici di esempio, asset e una `Campagna` 2024 già popolata. Crea anche un superuser `admin` (password `admin`).
    ```sh
    python manage.py seed_data --clean
    ```

6.  **Avviare il server di sviluppo del backend**:
    ```sh
    python manage.py runserver
    ```
    Il backend sarà accessibile su `http://127.0.0.1:8000`. L'admin è su `/admin`.

### Frontend Setup

*(Le seguenti istruzioni sono generiche per un'applicazione basata su npm)*

1.  **Navigare nella directory del frontend**:
    ```sh
    cd itra/frontend
    ```

2.  **Installare le dipendenze**:
    ```sh
    npm install
    ```

3.  **Avviare il server di sviluppo del frontend**:
    ```sh
    npm start
    ```
    L'applicazione frontend sarà accessibile su `http://localhost:3000` (o un'altra porta) e comunicherà con il backend.

### Comandi utili

1.  **Raprpesentazione grafica del DB delle classi .png**:
    ```sh
    python manage.py graph_models -a -o schema_modelli_completo.png
    oppure
    python manage.py graph_models campagne assets controlli elementtypes minacce scenari -g -o schema_logico.png
    ```  
2.  **Aggiornamento requiremets.txt**:
    ```sh
    pip freeze > requirements.txt
    ```  



## Possibili Sviluppi Futuri

*   **Configuratore Grafico per `ChainType`**: Sviluppare un'interfaccia frontend (es. con Vine, React o Vue.js) per creare e modificare graficamente le catene tecnologiche tramite drag-and-drop.
*   **Dashboard di Rischio per Asset**: Creare dashboard di riepilogo con grafici e statistiche sul rischio calcolato per ogni asset, basato sulla sua struttura tecnologica.
*   **Notifiche**: Implementare un sistema di notifiche per avvisare gli utenti di scadenze o assegnazioni di compiti.
*   **Ottimizzazione delle Prestazioni**: Per grandi volumi di dati, ottimizzare ulteriormente le query e considerare l'uso di task asincroni (es. con Celery) per il processo di clonazione delle campagne.
