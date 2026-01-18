import pandas as pd
import plotly.express as px
import streamlit as st

from src.data.collector import GitHubCollector
from src.db.mongo_client import mongo_client

# Configuration de la page
st.set_page_config(page_title="GitHub Issues Tower", layout="wide")

st.title("🚀 GitHub Issues MLOps Tower")

# --- Sidebar : Contrôles ---
st.sidebar.header("Actions")

if st.sidebar.button("Lancer la collecte (Incrémentale)"):
    st.sidebar.info("Démarrage du collecteur...")

    # On instancie le collecteur
    collector = GitHubCollector()

    # On crée une barre de progression
    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()

    # On lance la collecte
    try:
        # Note : Pour faire proprement, on devrait lancer ça dans un thread
        # mais pour l'interface admin simple, ça suffit.
        collector.run()
        st.sidebar.success("Collecte terminée !")
    except Exception as e:
        st.sidebar.error(f"Erreur : {e}")

# --- Section 1 : KPIs en temps réel ---
st.subheader("📊 État de la Base de Données")

# Connexion Mongo
if mongo_client.is_healthy():
    st.success("MongoDB Atlas : Connecté ✅")
    collection = mongo_client.get_collection("raw_issues")

    # Récupération des stats (Aggrégation Mongo pour la perf)
    total_issues = collection.count_documents({})
    unique_repos = len(collection.distinct("repository_url"))

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Issues", f"{total_issues:,}")
    col2.metric("Repos Cibles", unique_repos)
    col3.metric("DB Size (approx)", "X MB")  # On pourrait calculer la taille
else:
    st.error("MongoDB Atlas : Déconnecté ❌")
    st.stop()

# --- Section 2 : Analyse des Données ---
st.divider()

# On charge un échantillon pour les graphs (pas tout pour aller vite)
# On récupère juste les champs nécessaires
cursor = collection.find(
    {}, {"repository_url": 1, "created_at": 1, "labels.name": 1}
).limit(5000)
df = pd.DataFrame(list(cursor))

if not df.empty:
    # Nettoyage rapide pour l'affichage
    df["repo_name"] = df["repository_url"].apply(
        lambda x: x.split("/")[-2] + "/" + x.split("/")[-1]
    )
    df["created_at"] = pd.to_datetime(df["created_at"])

    # Graphique 1 : Issues par Repo
    st.subheader("Distribution par Repository")
    repo_counts = df["repo_name"].value_counts().reset_index()
    repo_counts.columns = ["Repo", "Count"]
    fig_repo = px.bar(
        repo_counts,
        x="Repo",
        y="Count",
        color="Repo",
        title="Nombre d'issues collectées par Repo",
    )
    st.plotly_chart(fig_repo, use_container_width=True)

    # Graphique 2 : Timeline
    st.subheader("Volumétrie temporelle")
    df_time = df.set_index("created_at").resample("M").size().reset_index(name="count")
    fig_time = px.line(
        df_time,
        x="created_at",
        y="count",
        title="Évolution du nombre d'issues créées (Mensuel)",
    )
    st.plotly_chart(fig_time, use_container_width=True)

    # Graphique 3 : Top Labels
    st.subheader("Labels les plus fréquents")
    # Aplatir la liste des labels
    all_labels = []
    for labels in df["labels"]:
        if isinstance(labels, list):
            for label in labels:
                all_labels.append(label["name"])

    if all_labels:
        labels_df = pd.DataFrame(all_labels, columns=["Label"])
        top_labels = labels_df["Label"].value_counts().head(15).reset_index()
        top_labels.columns = ["Label", "Count"]
        fig_labels = px.bar(
            top_labels, x="Count", y="Label", orientation="h", title="Top 15 Labels"
        )
        st.plotly_chart(fig_labels, use_container_width=True)

else:
    st.warning("Aucune donnée dans la base. Lancez une collecte !")

# --- Section 3 : Aperçu des Données ---
st.divider()
st.subheader("🔍 Explorateur de Données (Raw)")
if st.checkbox("Afficher les dernières données brutes"):
    latest_data = list(collection.find().sort("updated_at", -1).limit(5))
    st.json(latest_data)
