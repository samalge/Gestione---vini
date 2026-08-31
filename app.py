import streamlit as st
import json
import os
import pandas as pd

st.set_page_config(page_title="Gestione Cantina - Vini e Birra", layout="wide")
st.title("🍾 Gestione Inventario: Vini e Birra")

DB_FILE = "inventario_cantina.json"

# --- FUNZIONI DATABASE INVENTARIO ---
def carica_inventario():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    # Default initial inventory if file is empty
    return {
        "Vini Rossi": {},
        "Vini Bianchi": {},
        "Bollicine / Spumanti": {},
        "Birre Artigianali": {}
    }

def salva_inventario(dati):
    with open(DB_FILE, "w") as f:
        json.dump(dati, f, indent=4)

db_inventario = carica_inventario()

# --- 🔐 SECURE SESSION LOGIN / LOGOUT SYSTEM ---
st.sidebar.header("🔐 Accesso Amministratore")

if "cantina_admin_logged_in" not in st.session_state:
    st.session_state["cantina_admin_logged_in"] = False

if not st.session_state["cantina_admin_logged_in"]:
    psw_input = st.sidebar.text_input("Inserisci Password di Sicurezza:", type="password", key="cantina_psw_field")
    if st.sidebar.button("🔓 Sblocca Modifiche"):
        if psw_input == "Samuelmark123#":
            st.session_state["cantina_admin_logged_in"] = True
            st.rerun()
        else:
            st.sidebar.error("❌ Password errata!")
else:
    st.sidebar.success("🔒 Modalità Modifica Attiva")
    
    # Reset Database Button hidden behind admin authentication
    if st.sidebar.button("⚠️ RESETTA INTERO INVENTARIO", help="Cancella tutti i prodotti e azzera le scorte"):
        struttura_vuota = {"Vini Rossi": {}, "Vini Bianchi": {}, "Bollicine / Spumanti": {}, "Birre Artigianali": {}}
        salva_inventario(struttura_vuota)
        st.sidebar.success("✅ Inventario azzerato!")
        st.rerun()
        
    if st.sidebar.button("🔒 Blocca e Esci"):
        st.session_state["cantina_admin_logged_in"] = False
        st.rerun()

st.sidebar.markdown("<hr style='margin: 10px 0; border: 0.5px solid #555;'>", unsafe_allow_html=True)


# --- 📥 PANNELLO DI CARICO / SCARICO PRODOTTI (SOLO SE LOGGATO) ---
if st.session_state["cantina_admin_logged_in"]:
    st.header("📦 Registra Movimento Scorte (Carico / Scarico)")
    
    col_cat, col_prod, col_mov, col_qta = st.columns(4)
    
    with col_cat:
        categoria_scelta = st.selectbox("1. Seleziona Categoria:", list(db_inventario.keys()))
        
    # Ottieni la lista dei prodotti presenti nella categoria scelta
    prodotti_in_categoria = list(db_inventario[categoria_scelta].keys())
    opzioni_selezione_prodotto = ["➕ NUOVO PRODOTTO (Inserisci a mano...)"] + prodotti_in_categoria
    
    with col_prod:
        # 🔴 CORREZIONE RIGIDA: Definita ed allineata la variabile per evitare il NameError alla riga 104
        producto_carico_scelto = st.selectbox("2. Scegli Prodotto:", opzioni_selezione_prodotto)
        
    # Se l'utente seleziona di inserire un nuovo prodotto a mano
    if producto_carico_scelto == "➕ NUOVO PRODOTTO (Inserisci a mano...)":
        nome_nuovo_prodotto = st.text_input("Inserisci il Nome/Cantina del Nuovo Prodotto:", placeholder="es. Chianti Classico DOCG - Antinori").strip()
    else:
        nome_nuovo_prodotto = producto_carico_scelto

    with col_mov:
        tipo_movimento = st.radio("3. Tipo Operazione:", ["🟢 Carico (+ Scorte)", "🔴 Scarico (- Venduto)"])
        
    with col_qta:
        quantita_movimento = st.number_input("4. Quantità (Bottiglie/Fusti):", min_value=1, value=6, step=1)
        
    if st.button("💾 REGISTRA MOVIMENTO NEL DATABASE", type="primary"):
        if nome_nuovo_prodotto == "":
            st.error("⚠️ Inserisci un nome valido per il prodotto prima di salvare.")
        else:
            # Recuperiamo l'inventario aggiornato dal file
            database_attuale = carica_inventario()
            
            # Se il prodotto non esiste ancora nella categoria, lo inizializziamo a zero
            if nome_nuovo_prodotto not in database_attuale[categoria_scelta]:
                database_attuale[categoria_scelta][nome_nuovo_prodotto] = 0
                
            quantita_attuale = database_attuale[categoria_scelta][nome_nuovo_prodotto]
            
            # Applichiamo l'operazione matematica di carico o scarico
            if "Carico" in tipo_movimento:
                nuova_quantita = quantita_attuale + quantita_movimento
            else:
                nuova_quantita = quantita_attuale - quantita_movimento
                if nueva_quantita < 0:
                    nuova_quantita = 0 # Evita scorte negative accidentali
                    
            database_attuale[categoria_scelta][nome_nuovo_prodotto] = nuova_quantita
            salva_inventario(database_attuale)
            st.success(f"✅ Aggiornato con successo: {nome_nuovo_prodotto} ➡️ {nuova_quantita} unità disponibili!")
            st.rerun()

else:
    st.info("💡 Per inserire nuovi arrivi, modificare le quantità delle bottiglie o scaricare il venduto, inserisci la password amministratore nella barra laterale sinistra.")


# --- 📊 VISUALIZZAZIONE SCHERMO COMPLETO: STATO DELLE SCORTE DELLA CANTINA ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.header("📋 Registro Giacenze e Scorte Attuali della Cantina")

# Controlliamo se ci sono effettivamente prodotti registrati
inventario_vuoto = True
for cat in db_inventario:
    if db_inventario[cat]:
        inventario_vuoto = False
        break

if inventario_vuoto:
    st.warning("⚠️ Al momento non ci sono bottiglie registrate nella cantina. Sblocca il sistema a sinistra per iniziare il carico della merce.")
else:
    # Creiamo schede visive separate per ordinare i vini e le birre
    schede_categorie = st.tabs(list(db_inventario.keys()))
    
    for i, nome_categoria in enumerate(db_inventario.keys()):
        with schede_categorie[i]:
            prodotti_dettaglio = db_inventario[nome_categoria]
            
            if not prodotti_dettaglio:
                st.info(f"Nessun prodotto inserito nella categoria {nome_categoria}.")
            else:
                # Convertiamo i dati in formato tabella ordinata (DataFrame)
                lista_tabellare = []
                for nome_vino_birra, qta in prodotti_dettaglio.items():
                    # Segnalazione visiva di allerta se le scorte scendono sotto le 3 bottiglie
                    stato_allerta = "🟢 Scorte Regolari" if qta >= 3 else "🚨 SOTTO SCORTA (Ordinare!)"
                    if qta == 0:
                        stato_allerta = "❌ ESAURITO"
                        
                    lista_tabellare.append({
                        "Nome Prodotto / Cantina": nome_vino_birra,
                        "Bottiglie Disponibili": f"{qta} pz",
                        "Stato Magazzino": stato_allerta
                    })
                    
                df_categoria = pd.DataFrame(lista_tabellare)
                st.dataframe(df_categoria.set_index("Nome Prodotto / Cantina"), use_container_width=True)
