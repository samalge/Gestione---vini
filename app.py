import streamlit as st
import json
import os
import shutil
from datetime import datetime
import pandas as pd
import hmac

# ============================================================
# CONFIGURAZIONE
# ============================================================

st.set_page_config(
    page_title="Källarlager – Vin & Öl",
    page_icon="🍾",
    layout="wide"
)

st.title("🍾 Källarlager – Vin & Öl")

DB_FILE = "inventario_cantina.json"
BACKUP_FILE = "inventario_cantina_backup.json"

ADMIN_PASSWORD = "Samuelmark123#"

STANDARD_KATEGORIER = {
    "Röda viner": {},
    "Vita viner": {},
    "Mousserande / Spumante": {},
    "Hantverksöl": {}
}

LAGERGRÄNS = 6


# ============================================================
# DATABASHANTERING
# ============================================================

def skapa_standarddata():
    return {
        "produkter": {
            kategori: {}
            for kategori in STANDARD_KATEGORIER
        },
        "historik": []
    }


def konvertera_gammal_databas(gammal_data):
    """
    Gör både gamla och nya JSON-strukturer kompatibla
    med den aktuella databasen.
    """

    if not isinstance(gammal_data, dict):
        return skapa_standarddata()

    if "produkter" in gammal_data:
        produkter = gammal_data.get("produkter", {})
        historik = gammal_data.get("historik", [])

        if not isinstance(produkter, dict):
            produkter = {}

        if not isinstance(historik, list):
            historik = []

        for kategori in STANDARD_KATEGORIER:
            if not isinstance(produkter.get(kategori), dict):
                produkter[kategori] = {}

        return {
            "produkter": produkter,
            "historik": historik
        }

    # Vecchia struttura
    produkter = {}

    for kategori in STANDARD_KATEGORIER:
        contenuto = gammal_data.get(kategori, {})
        produkter[kategori] = contenuto if isinstance(contenuto, dict) else {}

    # Mantieni eventuali categorie extra
    for categoria, contenuto in gammal_data.items():
        if categoria not in produkter and isinstance(contenuto, dict):
            prodotti[categoria] = contenuto

    return {
        "produkter": prodotti,
        "historik": []
    }


def ladda_databas():
    if not os.path.exists(DB_FILE):
        return skapa_standarddata()

    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        return konvertera_gammal_databas(data)

    except Exception:
        return skapa_standarddata()


def spara_databas(data, skapa_backup=True):
    if skapa_backup and os.path.exists(DB_FILE):
        try:
            shutil.copy2(DB_FILE, BACKUP_FILE)
        except Exception:
            pass

    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def registrera_historik(
    data,
    kategori,
    produkt,
    typ,
    antal,
    före,
    efter
):
    nu = datetime.now()

    data["historik"].append({
        "datum": nu.strftime("%Y-%m-%d"),
        "tid": nu.strftime("%H:%M:%S"),
        "kategori": kategori,
        "produkt": produkt,
        "typ": typ,
        "antal": int(antal),
        "före": int(före),
        "efter": int(efter)
    })


def lagerstatus(antal):
    if antal == 0:
        return "❌ SLUT"

    if antal < LAGERGRÄNS:
        return "🚨 LÅGT LAGER"

    return "🟢 OK"


# ============================================================
# LÄS DATABASE
# ============================================================

data = ladda_databas()
produkter = data["produkter"]


# ============================================================
# ADMIN LOGIN
# ============================================================

if "cantina_admin_logged_in" not in st.session_state:
    st.session_state["cantina_admin_logged_in"] = False


st.sidebar.header("🔐 Administratör")

if not st.session_state["cantina_admin_logged_in"]:
    lösenord = st.sidebar.text_input(
        "Administratörslösenord",
        type="password"
    )

    if st.sidebar.button(
        "🔓 Lås upp redigering",
        use_container_width=True
    ):
        if hmac.compare_digest(lösenord, ADMIN_PASSWORD):
            st.session_state["cantina_admin_logged_in"] = True
            st.rerun()
        else:
            st.sidebar.error("❌ Fel lösenord.")

else:
    st.sidebar.success("🔓 Redigeringsläge aktivt")

    if st.sidebar.button(
        "🔒 Lås och logga ut",
        use_container_width=True
    ):
        st.session_state["cantina_admin_logged_in"] = False
        st.rerun()


# ============================================================
# SIDOPANEL – STATISTIK
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("📊 Lageröversikt")

alla_produkter = []

for kategori, lista in produkter.items():
    if not isinstance(lista, dict):
        continue

    for produkt, antal in lista.items():
        try:
            antal = int(antal)
        except (ValueError, TypeError):
            antal = 0

        alla_produkter.append({
            "kategori": kategori,
            "produkt": str(produkt),
            "antal": antal
        })


antal_produkter = len(alla_produkter)

totalt_antal = sum(
    x["antal"]
    for x in alla_produkter
)

antal_slut = sum(
    1
    for x in alla_produkter
    if x["antal"] == 0
)

antal_lågt = sum(
    1
    for x in alla_produkter
    if 0 < x["antal"] < LAGERGRÄNS
)


st.sidebar.metric("🍾 Produkter", antal_produkter)
st.sidebar.metric("📦 Totalt antal enheter", totalt_antal)
st.sidebar.metric("❌ Slut", antal_slut)
st.sidebar.metric("🚨 Lågt lager", antal_lågt)


# ============================================================
# RESET DATABASE
# ============================================================

if st.session_state["cantina_admin_logged_in"]:
    st.sidebar.markdown("---")

    with st.sidebar.expander("⚠️ Systemverktyg"):
        st.warning("Detta raderar hela lagret.")

        bekräfta = st.checkbox(
            "Jag bekräftar återställningen."
        )

        if st.button(
            "🗑️ ÅTERSTÄLL HELA LAGRET",
            use_container_width=True
        ):
            if not bekräfta:
                st.error("❌ Bekräfta först.")
            else:
                if os.path.exists(DB_FILE):
                    try:
                        shutil.copy2(DB_FILE, BACKUP_FILE)
                    except Exception:
                        pass

                ny_data = skapa_standarddata()
                spara_databas(
                    ny_data,
                    skapa_backup=False
                )

                st.success("✅ Lagret har återställts.")
                st.rerun()


# ============================================================
# AKTUELLT LAGER
# ============================================================

st.header("📋 Aktuellt lager")

if not alla_produkter:
    st.info("Det finns inga produkter registrerade ännu.")

else:
    sökning = st.text_input(
        "🔎 Sök produkt eller producent",
        placeholder="t.ex. Chianti, Antinori, IPA..."
    ).strip().lower()

    filtrerade_produkter = [
        x
        for x in alla_produkter
        if (
            not sökning
            or sökning in x["produkt"].lower()
            or sökning in x["kategori"].lower()
        )
    ]

    if filtrerade_produkter:
        tabell = pd.DataFrame([
            {
                "Kategori": x["kategori"],
                "Produkt / Producent": x["produkt"],
                "Tillgängligt": f'{x["antal"]} st',
                "Status": lagerstatus(x["antal"])
            }
            for x in filtrerade_produkter
        ])

        st.dataframe(
            tabell,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("🔎 Ingen produkt hittades.")


# ============================================================
# ADMIN – PRODUKTHANTERING
# ============================================================

if st.session_state["cantina_admin_logged_in"]:
    st.markdown("---")
    st.header("🛠️ Produkthantering")

    tab_ny, tab_namn, tab_radera = st.tabs([
        "➕ Ny artikel",
        "✏️ Ändra namn",
        "🗑️ Radera produkt"
    ])

    # --------------------------------------------------------
    # NY ARTIKEL
    # --------------------------------------------------------

    with tab_ny:
        st.subheader("➕ Lägg till ny artikel")

        kategorier = list(produkter.keys())

        col1, col2 = st.columns(2)

        with col1:
            ny_kategori = st.selectbox(
                "Kategori",
                kategorier,
                key="ny_artikel_kategori"
            )

        with col2:
            initial_mängd = st.number_input(
                "Startlager",
                min_value=0,
                value=0,
                step=1,
                key="ny_artikel_mangd"
            )

        nytt_produkt_namn = st.text_input(
            "Produkt / Producent",
            placeholder="t.ex. Chianti Classico – Antinori",
            key="ny_artikel_namn"
        ).strip()

        st.caption(
            "Exempel: du kan skriva vinets namn, producenten "
            "eller båda tillsammans."
        )

        if st.button(
            "➕ LÄGG TILL ARTIKEL",
            type="primary",
            use_container_width=True
        ):
            if not nytt_produkt_namn:
                st.error("❌ Ange ett produktnamn.")

            else:
                aktuell_data = ladda_databas()

                aktuell_data["produkter"].setdefault(
                    ny_kategori,
                    {}
                )

                befintliga = aktuell_data[
                    "produkter"
                ][ny_kategori]

                if nytt_produkt_namn in befintliga:
                    st.error(
                        "❌ Produkten finns redan i denna kategori."
                    )

                else:
                    befintlig_mängd = int(initial_mängd)

                    befintliga[nytt_produkt_namn] = befintlig_mängd

                    registrera_historik(
                        aktuell_data,
                        ny_kategori,
                        nytt_produkt_namn,
                        "Ny produkt",
                        befintlig_mängd,
                        0,
                        befintlig_mängd
                    )

                    spara_databas(aktuell_data)

                    st.success(
                        f"✅ {nytt_produkt_namn} har lagts till "
                        f"med {befintlig_mängd} st."
                    )

                    st.rerun()

    # --------------------------------------------------------
    # ÄNDRA NAMN
    # --------------------------------------------------------

    with tab_namn:
        st.subheader("✏️ Ändra namn på produkt")

        if not alla_produkter:
            st.info("Det finns inga produkter att ändra.")

        else:
            produktlista_namn = [
                f'{x["kategori"]} – {x["produkt"]} '
                f'({x["antal"]} st)'
                for x in alla_produkter
            ]

            vald_namn = st.selectbox(
                "Välj produkt",
                produktlista_namn,
                key="andra_namn_produkt"
            )

            index_namn = produktlista_namn.index(vald_namn)
            info_namn = alla_produkter[index_namn]

            nytt_namn = st.text_input(
                "Nytt produktnamn",
                value=info_namn["produkt"],
                key="nytt_produktnamn"
            ).strip()

            if st.button(
                "💾 SPARA NYTT NAMN",
                type="primary",
                use_container_width=True
            ):
                if not nytt_namn:
                    st.error("❌ Namnet får inte vara tomt.")

                elif nytt_namn == info_namn["produkt"]:
                    st.info("ℹ️ Namnet är oförändrat.")

                else:
                    aktuell_data = ladda_databas()

                    kategori = info_namn["kategori"]
                    gammalt_namn = info_namn["produkt"]

                    kategori_data = aktuell_data[
                        "produkter"
                    ].setdefault(kategori, {})

                    if nytt_namn in kategori_data:
                        st.error(
                            "❌ Det nya namnet finns redan "
                            "i denna kategori."
                        )

                    elif gammalt_namn not in kategori_data:
                        st.error(
                            "❌ Produkten kunde inte hittas."
                        )

                    else:
                        mängd = kategori_data.pop(
                            gammalt_namn
                        )

                        kategori_data[nytt_namn] = mängd

                        # Uppdatera produktnamnet i historiken
                        for post in aktuell_data["historik"]:
                            if (
                                post.get("kategori") == kategori
                                and post.get("produkt") == gammalt_namn
                            ):
                                post["produkt"] = nytt_namn

                        spara_databas(aktuell_data)

                        st.success(
                            f"✅ Produktnamnet har ändrats från "
                            f"'{gammalt_namn}' till '{nytt_namn}'."
                        )

                        st.rerun()

    # --------------------------------------------------------
    # RADERA PRODUKT
    # --------------------------------------------------------

    with tab_radera:
        st.subheader("🗑️ Radera produkt")

        if not alla_produkter:
            st.info("Det finns inga produkter att radera.")

        else:
            produktlista_radera = [
                f'{x["kategori"]} – {x["produkt"]} '
                f'({x["antal"]} st)'
                for x in alla_produkter
            ]

            vald_radera = st.selectbox(
                "Välj produkt",
                produktlista_radera,
                key="radera_produkt"
            )

            index_radera = produktlista_radera.index(
                vald_radera
            )

            info_radera = alla_produkter[index_radera]

            st.warning(
                f"Du är på väg att radera "
                f"**{info_radera['produkt']}**."
            )

            bekräfta_radera = st.checkbox(
                "Jag bekräftar att produkten ska raderas.",
                key="bekrafta_radera"
            )

            if st.button(
                "🗑️ RADERA PRODUKT",
                use_container_width=True
            ):
                if not bekräfta_radera:
                    st.error("❌ Bekräfta raderingen först.")

                else:
                    aktuell_data = ladda_databas()

                    kategori = info_radera["kategori"]
                    produkt = info_radera["produkt"]

                    kategori_data = aktuell_data[
                        "produkter"
                    ].get(kategori, {})

                    if produkt in kategori_data:
                        del kategori_data[produkt]

                        spara_databas(aktuell_data)

                        st.success(
                            f"✅ {produkt} har raderats."
                        )

                        st.rerun()

                    else:
                        st.error(
                            "❌ Produkten kunde inte hittas."
                        )


# ============================================================
# ADMIN – LAGERÄNDRING
# ============================================================

if st.session_state["cantina_admin_logged_in"]:
    st.markdown("---")
    st.header("📦 Registrera lagerändring")

    kategorier = list(produkter.keys())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        kategori = st.selectbox(
            "1. Kategori",
            kategorier,
            key="lager_kategori"
        )

    befintliga_produkter = list(
        produkter.get(kategori, {}).keys()
    )

    produktalternativ = [
        "➕ NY PRODUKT"
    ] + befintliga_produkter

    with col2:
        valt_produkt = st.selectbox(
            "2. Produkt",
            produktalternativ,
            key="lager_produkt"
        )

    if valt_produkt == "➕ NY PRODUKT":
        produkt = st.text_input(
            "Produkt / Producent",
            placeholder="t.ex. Chianti Classico – Antinori",
            key="lager_ny_produkt"
        ).strip()
    else:
        produkt = valt_produkt

    with col3:
        typ = st.radio(
            "3. Operation",
            [
                "🟢 Inleverans (+)",
                "🔴 Uttag (-)"
            ],
            key="lager_operation"
        )

    with col4:
        antal = st.number_input(
            "4. Antal",
            min_value=1,
            value=6,
            step=1,
            key="lager_antal"
        )

    nuvarande = 0

    if produkt:
        nuvarande = int(
            produkter
            .get(kategori, {})
            .get(produkt, 0)
        )

        st.info(
            f"📦 **{produkt}** – "
            f"nuvarande lager: **{nuvarande} st**"
        )

    if st.button(
        "💾 REGISTRERA LAGERÄNDRING",
        type="primary",
        use_container_width=True
    ):
        if not produkt:
            st.error("⚠️ Ange ett produktnamn.")

        else:
            aktuell_data = ladda_databas()

            aktuell_data["produkter"].setdefault(
                kategori,
                {}
            )

            kategori_data = aktuell_data[
                "produkter"
            ][kategori]

            före = int(
                kategori_data.get(
                    produkt,
                    0
                )
            )

            # ------------------------------------------------
            # INLEVERANS
            # ------------------------------------------------

            if "Inleverans" in typ:
                efter = före + int(antal)
                historik_typ = "Inleverans"

            # ------------------------------------------------
            # UTTAG
            # ------------------------------------------------

            else:
                if int(antal) > före:
                    st.error(
                        f"❌ Otillräckligt lager. "
                        f"Det finns bara {före} st."
                    )
                    st.stop()

                efter = före - int(antal)
                historik_typ = "Uttag"

            kategori_data[produkt] = efter

            registrera_historik(
                aktuell_data,
                kategori,
                produkt,
                historik_typ,
                antal,
                före,
                efter
            )

            spara_databas(aktuell_data)

            st.success(
                f"✅ {produkt}: "
                f"{före} → {efter} st"
            )

            st.rerun()


# ============================================================
# ADMIN – KORRIGERA LAGER
# ============================================================

if st.session_state["cantina_admin_logged_in"]:
    st.markdown("---")
    st.header("✏️ Korrigera lagersaldo")

    if alla_produkter:
        produktlista_korrigering = [
            f'{x["kategori"]} – '
            f'{x["produkt"]} '
            f'({x["antal"]} st)'
            for x in alla_produkter
        ]

        vald_korrigering = st.selectbox(
            "Välj produkt",
            produktlista_korrigering,
            key="korrigera_produkt"
        )

        index_korrigering = produktlista_korrigering.index(
            vald_korrigering
        )

        info_korrigering = alla_produkter[
            index_korrigering
        ]

        ny_mängd = st.number_input(
            "Nytt faktiskt lagersaldo",
            min_value=0,
            value=int(info_korrigering["antal"]),
            step=1,
            key="ny_lagersaldo"
        )

        if st.button(
            "💾 SPARA KORRIGERING",
            use_container_width=True
        ):
            aktuell_data = ladda_databas()

            kategori = info_korrigering["kategori"]
            produkt = info_korrigering["produkt"]

            kategori_data = aktuell_data[
                "produkter"
            ].get(kategori, {})

            if produkt not in kategori_data:
                st.error(
                    "❌ Produkten kunde inte hittas."
                )

            else:
                före = int(kategori_data[produkt])
                efter = int(ny_mängd)

                if före != efter:
                    kategori_data[produkt] = efter

                    registrera_historik(
                        aktuell_data,
                        kategori,
                        produkt,
                        "Lagerkorrigering",
                        abs(efter - före),
                        före,
                        efter
                    )

                    spara_databas(aktuell_data)

                st.success(
                    "✅ Lagret har korrigerats."
                )

                st.rerun()


# ============================================================
# HISTORIK
# ============================================================

st.markdown("---")
st.header("📜 Lagerhistorik")

historik = data.get("historik", [])

if not historik:
    st.info("Ingen lagerhistorik finns ännu.")

else:
    historik = list(reversed(historik))

    filter_historik = st.text_input(
        "🔎 Sök i historiken",
        placeholder="Produkt, kategori eller operation..."
    ).strip().lower()

    if filter_historik:
        historik = [
            x
            for x in historik
            if filter_historik in str(x).lower()
        ]

    df_historik = pd.DataFrame([
        {
            "Datum": x.get("datum", ""),
            "Tid": x.get("tid", ""),
            "Kategori": x.get("kategori", ""),
            "Produkt": x.get("produkt", ""),
            "Operation": x.get("typ", ""),
            "Antal": x.get("antal", 0),
            "Före": x.get("före", 0),
            "Efter": x.get("efter", 0)
        }
        for x in historik
    ])

    st.dataframe(
        df_historik,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# BESTÄLLNINGSLISTA
# ============================================================

st.markdown("---")
st.header("🚨 Beställningslista")

beställningslista = [
    x
    for x in alla_produkter
    if x["antal"] < LAGERGRÄNS
]

if beställningslista:
    df_beställning = pd.DataFrame([
        {
            "Kategori": x["kategori"],
            "Produkt / Producent": x["produkt"],
            "Tillgängligt": f'{x["antal"]} st',
            "Status": lagerstatus(x["antal"])
        }
        for x in beställningslista
    ])

    st.dataframe(
        df_beställning,
        use_container_width=True,
        hide_index=True
    )

else:
    st.success("✅ Inga produkter behöver beställas.")
