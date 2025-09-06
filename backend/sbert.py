import pandas as pd
from sentence_transformers import SentenceTransformer, util

import json

# Carica i dati dal file JSON
with open("copilot.json", "r", encoding="utf-8") as f:
    data = json.load(f)

controlli_df = pd.DataFrame(data["controlli"])
minacce_df = pd.DataFrame(data["minacce"])

# Filtra i dati
controlli_df = controlli_df.dropna(subset=["ID Presidio", "Descrizione presidio", "Categoria Presidio"])
minacce_df = minacce_df.dropna(subset=["ID Minaccia", "Minaccia"])

# Prepara i testi
controlli_descrizioni = controlli_df["Descrizione presidio"].tolist()
minacce_descrizioni = minacce_df["Minaccia"].tolist()

# Carica modello SBERT
model = SentenceTransformer('all-MiniLM-L6-v2')
controlli_embeddings = model.encode(controlli_descrizioni, convert_to_tensor=True)
minacce_embeddings = model.encode(minacce_descrizioni, convert_to_tensor=True)

# Assegnazioni
assegnazioni = {f"{row['ID Minaccia']} - {row['Minaccia']}": set() for _, row in minacce_df.iterrows()}
spiegazioni = []
assegnati = set()

# Mappatura
for i, minaccia_row in minacce_df.iterrows():
    min_key = f"{minaccia_row['ID Minaccia']} - {minaccia_row['Minaccia']}"
    sim_scores = util.cos_sim(minacce_embeddings[i], controlli_embeddings)[0].tolist()
    controlli_df["similarity"] = sim_scores

    preventive = controlli_df[controlli_df["Categoria Presidio"] == "Preventive"].sort_values(by="similarity", ascending=False)
    detective = controlli_df[controlli_df["Categoria Presidio"] == "Detective"].sort_values(by="similarity", ascending=False)

    selected = pd.concat([preventive.head(2), detective.head(2)])
    for _, row in selected.iterrows():
        idx = row.name
        assegnazioni[min_key].add(idx)
        assegnati.add(idx)
        spiegazioni.append({
            "ID Minaccia": minaccia_row["ID Minaccia"],
            "Minaccia": minaccia_row["Minaccia"],
            "ID Controllo": row["ID Presidio"],
            "Controllo": row["Descrizione presidio"],
            "Categoria": row["Categoria Presidio"],
            "Motivazione": f"Similarità semantica SBERT: {row['similarity']:.2f}"
        })

# Assegna controlli non ancora assegnati
non_assegnati = controlli_df[~controlli_df.index.isin(assegnati)]
for idx, row in non_assegnati.iterrows():
    controllo_embedding = model.encode(row["Descrizione presidio"], convert_to_tensor=True)
    sim_scores = util.cos_sim(controllo_embedding, minacce_embeddings)[0].tolist()
    best_idx = sim_scores.index(max(sim_scores))
    best_minaccia_row = minacce_df.iloc[best_idx]
    min_key = f"{best_minaccia_row['ID Minaccia']} - {best_minaccia_row['Minaccia']}"
    assegnazioni[min_key].add(idx)
    spiegazioni.append({
        "ID Minaccia": best_minaccia_row["ID Minaccia"],
        "Minaccia": best_minaccia_row["Minaccia"],
        "ID Controllo": row["ID Presidio"],
        "Controllo": row["Descrizione presidio"],
        "Categoria": row["Categoria Presidio"],
        "Motivazione": f"Controllo non assegnato, associato semanticamente con SBERT (score: {max(sim_scores):.2f})"
    })

# Crea matrice
colonne = [f"{row['ID Presidio']} - {row['Descrizione presidio']}" for _, row in controlli_df.iterrows()]
matrice = pd.DataFrame("", index=assegnazioni.keys(), columns=colonne)
for minaccia, idx_set in assegnazioni.items():
    for idx in idx_set:
        controllo_id = controlli_df.loc[idx, "ID Presidio"]
        controllo_descrizione = controlli_df.loc[idx, "Descrizione presidio"]
        colonna_nome = f"{controllo_id} - {controllo_descrizione}"
        matrice.loc[minaccia, colonna_nome] = "X"

# Esporta
spiegazioni_df = pd.DataFrame(spiegazioni)

output_data = {
    "matrice": matrice.to_dict(orient="index"),
    "spiegazioni": spiegazioni_df.to_dict(orient="records")
}

output_file_path = "matrice_sbert_con_spiegazioni.json"
with open(output_file_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4)

print(f"Output saved to {output_file_path}")