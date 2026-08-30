import streamlit as st
import json
import os
from datetime import datetime

st.set_page_config(page_title="Gestione Vini", layout="wide")
st.title("🍷 Cantina Vini & Registro Storico")

DB_FILE = "stato_vini.json"
LOG_FILE = "storico_vini.json"

PASSWORD_SEGRETA = "Samuelmark123#"

if "autenticato" not in st.session_state:
    st.session_state.autenticato = False

def carica_vini():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    # Vini di esempio iniziali (puoi cancellarli o modificarli dall'app)
    return {
        "201": {"nome": "Brunello di Montalcino", "scorta": 6, "soglia_minima": 2},
        "202": {"nome": "Chianti Classico", "scorta": 12, "soglia_minima": 3},
        "203": {"nome": "Prosecco DOCG", "scorta": 24, "soglia_minima": 6}
    }

def salva_vini(inventario):
    with open(DB_FILE, "w") as f:
        json.dump(inventario, f)

def carica_log():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def salva_log(lista_log):
    with open(LOG_FILE, "w") as f:
        json.dump(lista_log, f)

def aggiungi_evento(azione, codice, nome, quantita, operatore, motivo=""):
    logs = carica_log()
    nuovo_evento = {
        "orario": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "azione": azione,
        "codice": codice,
        "nome": nome,
        "quantita": quantita,
        "operatore": operatore,
        "motivo": motivo
    }
    logs.insert(0, nuovo_evento)
    salva_log(logs[:100])

inventario = carica_vini()

# BARRA LATERALE: ACCESSO TITOLARE BLINDATO
st.sidebar.header("🔐 Area Riservata Titolare")

st.markdown(
    """
    <style>
    button[title="Show password"], button[title="Hide password"] {
        display: none !important;
    }
    input[type="password"]::-ms-reveal {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

if not st.session_state.autenticato:
    password_inserita = st.sidebar.text_input("Inserisci password titolare:", type="password", key="pwd_field")
    if password_inserita == PASSWORD_SEGRETA:
        st.session_state.autenticato = True
        st.rerun()
    elif password_inserita != "":
        st.sidebar.error("❌ Password errata!")
else:
    st.sidebar.success("🔓 Accesso autorizzato!")
    
    if st.sidebar.button("🔒 Esci e Blocca Area Riservata", type="primary", use_container_width=True):
        st.session_state.autenticato = False
        st.rerun()
        
    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    st.sidebar.header("🚚 Carico Bottiglie (Arrivo Fornitori)")
    operatore_in = st.sidebar.text_input("Chi registra il carico?", placeholder="es. Mario / Titolare", key="op_in")

    elenco_carico_tendina = [f"{codice} - {info['nome']}" for codice, info in inventario.items()]
    elenco_carico_tendina.insert(0, "➕ NUOVO VINO (Inserisci a mano...)")

    prodotto_carico_scelto = st.sidebar.selectbox("Seleziona vino da aggiungere:", elenco_carico_tendina)

    if producto_carico_scelto == "➕ NUOVO VINO (Inserisci a mano...)":
        nuovo_codice = st.sidebar.text_input("Codice Bottiglia / Codice a Barre:", placeholder="es. 204")
        nuovo_nome = st.sidebar.text_input("Nome Vino / Cantina / Annata:", placeholder="es. Amarone della Valpolicella")
        soglia_allerta = st.sidebar.number_input("Scorta minima di allerta:", min_value=1, value=3)
    else:
        codice_esistente = prodotto_carico_scelto.split(" - ")
        st.sidebar.info(f"Stai caricando: **{inventario[codice_esistente]['nome']}**")

    quantita_carico = st.sidebar.number_input("Bottiglie da aggiungere:", min_value=1, value=6)

    if st.sidebar.button("Registra ed Entra in Cantina"):
        if prodotto_carico_scelto == "➕ NUOVO VINO (Inserisci a mano...)":
            nuovo_codice = nuovo_codice.strip()
            if not nuovo_codice or not nuovo_nome:
                st.sidebar.error("Inserisci sia il codice che il nome del vino!")
            else:
                if nuovo_codice in inventario:
                    st.sidebar.error("Questo codice esiste già nella cantina!")
                else:
                    inventario[nuovo_codice] = {"nome": nuovo_nome, "scorta": quantita_carico, "soglia_minima": soglia_allerta}
                    salva_vini(inventario)
                    aggiungi_evento("CARICO (➕)", nuovo_codice, nuovo_nome, quantita_carico, operatore_in if operatore_in else "Titolare", "Nuova etichetta inserita in cantina")
                    st.sidebar.success(f"Vino creato: {nuovo_nome}!")
                    st.rerun()
        else:
            codice_esistente = prodotto_carico_scelto.split(" - ")
            inventario[codice_esistente]["scorta"] += quantita_carico
            salva_vini(inventario)
            aggiungi_evento("CARICO (➕)", codice_esistente, inventario[codice_esistente]['nome'], quantita_carico, operatore_in if operatore_in else "Titolare", "Rifornimento cantina")
            st.sidebar.success(f"Aggiunte {quantita_carico} bottiglie.")
            st.rerun()

    st.sidebar.markdown("<hr>", unsafe_allow_html=True)
    st.sidebar.header("🗑️ Elimina Vino dal Catalogo")
    elenco_elimina = [f"{codice} - {info['nome']}" for codice, info in inventario.items()]
    if elenco_elimina:
        prodotto_da_eliminare = st.sidebar.selectbox("Seleziona vino da cancellare:", elenco_elimina, key="el_sel")
        if st.sidebar.button("🗑️ Elimina Definitivamente", type="primary"):
            cod_el = prodotto_da_eliminare.split(" - ")
            nome_el = inventario[cod_el]["nome"]
            del inventario[cod_el]
            salva_vini(inventario)
            aggiungi_evento("ELIMINATO (❌)", cod_el, nome_el, 0, "Titolare", "Rimosso completamente dalla carta dei vini")
            st.sidebar.success(f"Rimosso {nome_el} dalla cantina!")
            st.rerun()

if not st.session_state.autenticato:
    st.sidebar.info("🔒 Inserisci la password del titolare per sbloccare le funzioni di carico dei fornitori ed eliminazione vini.")


# PANNELLO CENTRALE: SCARICO RAPIDO
st.header("🛒 Scarico Rapido (Uscita bottiglie per i tavoli / bar)")
elenco_prodotti_tendina = [f"{codice} - {info['nome']}" for codice, info in inventario.items()]

col_personale, col_scelta, col_quantita = st.columns(3)

with col_personale:
    nome_cuoco = st.text_input("👨‍🍳 Nome Sommelier / Cuoco:", placeholder="Chi preleva")
    nome_cameriere = st.text_input("🤵 Nome Cameriere (Servering):", placeholder="Chi porta al tavolo")
with col_scelta:
    if elenco_prodotti_tendina:
        prodotto_selezionato = st.selectbox("Seleziona il vino dal menu a tendina:", elenco_prodotti_tendina)
    else:
        st.write("Nessun vino presente in cantina.")
    codice_manuale = st.text_input("Oppure digita il codice a mano:", key="manual_code_input", placeholder="Es. 201")
with col_quantita:
    quantita_prelievo = st.number_input("Bottiglie da prelevare:", min_value=1, value=1, key="qta")
    motivo_out = st.text_input("Note / Tavolo (opzionale):", placeholder="es. Tavolo 4, Bottiglia difettosa/tappo")

if st.button("🔄 Confirmed / Conferma Scarico Bottiglia", use_container_width=True):
    codice_prelievo = None
    
    if codice_manuale.strip():
        codice_prelievo = codice_manuale.strip()
    elif elenco_prodotti_tendina:
        codice_prelievo = prodotto_selezionato.split(" - ")
        
    if codice_prelievo and codice_prelievo in inventario:
        if inventario[codice_prelievo]["scorta"] >= quantita_prelievo:
            inventario[codice_prelievo]["scorta"] -= quantita_prelievo
            salva_vini(inventario)
            
            firme = []
            if nome_cuoco.strip(): firme.append(f"Sommelier: {nome_cuoco.strip()}")
            if nome_cameriere.strip(): firme.append(f"Servering: {nome_cameriere.strip()}")
            chi_ha_prelevato = " & ".join(firme) if firme else "Non specificato"
            
            aggiungi_evento("SCARICO (➖)", codice_prelievo, inventario[codice_prelievo]["nome"], quantita_prelievo, chi_ha_prelevato, motivo_out)
            st.success(f"Prelevate {quantita_prelievo} bottiglie di {inventario[codice_prelievo]['nome']}!")
            st.rerun()
        else:
            st.error(f"Scorte insufficienti! Ci sono solo {inventario[codice_prelievo]['scorta']} bottiglie in cantina.")
    else:
        st.error("Codice vino non trovato nel database o cantina vuota!")

# INVENTARIO IN TEMPO REALE
st.header("📊 Bottiglie Attuali in Cantina")
for codice, info in list(inventario.items()):
    col_info, col_azioni = st.columns(2)
    scorta_attuale = info["scorta"]
    soglia = info["soglia_minima"]
    
    with col_info:
        if scorta_attuale <= soglia:
            st.markdown(f"🚨 [<span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{codice}</span>] **{info['nome']}** | In Cantina: <span style='color: #F72585; font-weight: bold;'>{scorta_attuale} bt</span> (Sotto la soglia minima!)", unsafe_allow_html=True)
        else:
            st.markdown(f"📦 [<span style='color: #FFD166; font-size: 24px; font-weight: bold;'>{codice}</span>] **{info['nome']}** | In Cantina: **{scorta_attuale} bt**", unsafe_allow_html=True)
            
    with col_azioni:
        if st.button("Elimina rapido (1 bt)", key=f"del_{codice}"):
            if inventario[codice]["scorta"] > 0:
                inventario[codice]["scorta"] -= 1
                salva_vini(inventario)
                aggiungi_evento("CANCELLAZIONE (🗑️)", codice, inventario[codice]["nome"], 1, "Titolare", "Bottiglia rimossa manualmente")
                st.rerun()
    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #333;'>", unsafe_allow_html=True)

# REGISTRO STORICO
st.header("📜 Registro Ultimi Movimenti Cantina (Tracciabilità)")
lista_attivita = carica_log()

