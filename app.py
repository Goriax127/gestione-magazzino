import streamlit as st
import os
import tempfile
import asyncio
from document_processor import DocumentProcessor
from db_manager import DatabaseManager
from datetime import datetime
import pandas as pd

# Configurazione della pagina
st.set_page_config(
    page_title="Gestione Magazzino",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Stile CSS personalizzato
st.markdown("""
    <style>
    .stRadio > label {
        font-size: 1.2rem !important;
        padding: 1rem !important;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .stButton > button {
        width: 100%;
        padding: 1rem 0.5rem;
        font-size: 1.1rem;
        margin: 0.5rem 0;
    }
    .big-button {
        font-size: 1.5rem !important;
        padding: 1.5rem !important;
    }
    h1 {
        font-size: 1.8rem !important;
        text-align: center;
        padding: 1rem 0;
    }
    h2, h3 {
        font-size: 1.4rem !important;
        padding: 0.8rem 0;
    }
    .dataframe {
        font-size: 0.9rem !important;
    }
    .success-box {
        padding: 1rem;
        background-color: #a8e6cf;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #ffb3b3;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

async def process_document_async(doc_processor, file_path):
    return await doc_processor.process_document(file_path)

def main():
    st.title("📦 Gestione Magazzino")
    
    # Inizializza i manager
    doc_processor = DocumentProcessor()
    db_manager = DatabaseManager()
    
    # Tab per le diverse funzionalità
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔄 Nuovo Movimento", 
        "✅ Movimenti da Confermare", 
        "📊 Inventario",
        "📝 Log Operazioni"
    ])
    
    # Tab 1: Nuovo Movimento
    with tab1:
        st.header("Nuovo Movimento")
        
        # Scelta tra caricamento documento o inserimento manuale
        input_method = st.radio(
            "Metodo di inserimento",
            ["📄 Carica Documento", "⌨️ Inserimento Manuale"],
            horizontal=True
        )
        
        if input_method == "📄 Carica Documento":
            # Selezione tipo movimento
            tipo_movimento = st.radio(
                "Tipo di Movimento",
                options=["carico", "scarico"],
                format_func=lambda x: "📥 CARICO" if x == "carico" else "📤 SCARICO",
                horizontal=True
            )
            
            # Box colorato per il tipo di movimento
            movimento_color = "#a8e6cf" if tipo_movimento == "carico" else "#ffb3b3"
            st.markdown(f"""
                <div style="background-color: {movimento_color}; padding: 1rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
                    <h3 style="margin: 0; color: #1e1e1e;">Movimento selezionato: {tipo_movimento.upper()}</h3>
                </div>
            """, unsafe_allow_html=True)
            
            # Caricamento documento
            uploaded_file = st.file_uploader(
                "Carica documento o scatta foto",
                type=["pdf", "png", "jpg", "jpeg"],
                help="Supporta PDF e immagini (PNG, JPG)"
            )
            
            if uploaded_file:
                try:
                    # Preview immagine
                    if uploaded_file.type.startswith('image/'):
                        st.image(uploaded_file, caption="Anteprima documento", use_column_width=True)
                    
                    # Processo documento
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    with st.spinner("🔍 Analisi del documento..."):
                        extracted_items = asyncio.run(process_document_async(doc_processor, tmp_path))
                    
                    if extracted_items:
                        st.success(f"Trovati {len(extracted_items)} elementi nel documento")
                        
                        # Mostra dati estratti
                        st.markdown("""<div style="overflow-x: auto;">""", unsafe_allow_html=True)
                        items_for_display = []
                        for i, item in enumerate(extracted_items, 1):
                            items_for_display.append({
                                "N°": i,
                                "Codice": item["codice_materia_prima"],
                                "Descrizione": item["descrizione"],
                                "Quantità": item["quantita"]
                            })
                        st.table(items_for_display)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Pulsante salva
                        if st.button("💾 SALVA MOVIMENTO", use_container_width=True):
                            with st.spinner("Salvataggio in corso..."):
                                for item in extracted_items:
                                    db_manager.insert_movimento(
                                        item["codice_materia_prima"],
                                        item["descrizione"],
                                        float(item["quantita"].replace(',', '.')),
                                        tipo_movimento
                                    )
                            st.success("✅ Movimento salvato con successo!")
                    
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    st.error(f"❌ Errore: {str(e)}")
        
        else:  # Inserimento Manuale
            st.subheader("Inserimento Movimento Manuale")
            
            # Form per inserimento manuale
            with st.form("movimento_manuale"):
                tipo_movimento = st.radio(
                    "Tipo di Movimento",
                    options=["carico", "scarico"],
                    format_func=lambda x: "📥 CARICO" if x == "carico" else "📤 SCARICO",
                    horizontal=True
                )
                
                codice = st.text_input("Codice Materia Prima")
                descrizione = st.text_input("Descrizione")
                quantita = st.number_input("Quantità", min_value=0.01, step=0.01)
                
                submitted = st.form_submit_button("💾 SALVA MOVIMENTO")
                
                if submitted:
                    try:
                        db_manager.insert_movimento(
                            codice,
                            descrizione,
                            float(quantita),
                            tipo_movimento
                        )
                        st.success("✅ Movimento inserito con successo!")
                    except Exception as e:
                        st.error(f"❌ Errore durante l'inserimento: {str(e)}")
    
    # Tab 2: Movimenti da Confermare
    with tab2:
        st.header("Movimenti da Confermare")
        
        # Recupera movimenti da confermare
        movimenti = db_manager.get_movimenti_da_confermare()
        
        if movimenti:
            for mov in movimenti:
                with st.container():
                    col1, col2, col3 = st.columns([2,1,1])
                    
                    with col1:
                        st.write(f"**Codice:** {mov['codice_materia_prima']}")
                        st.write(f"**Descrizione:** {mov['descrizione']}")
                        st.write(f"**Quantità:** {mov['quantita']}")
                        
                    with col2:
                        movimento_color = "#a8e6cf" if mov['tipo_movimento'] == 'carico' else "#ffb3b3"
                        st.markdown(f"""
                            <div style="background-color: {movimento_color}; padding: 0.5rem; border-radius: 5px; text-align: center;">
                                {mov['tipo_movimento'].upper()}
                            </div>
                        """, unsafe_allow_html=True)
                        
                    with col3:
                        if st.button("✅ Conferma", key=f"conf_{mov['id']}", use_container_width=True):
                            try:
                                is_new = db_manager.conferma_movimento(mov['id'])
                                if is_new:
                                    st.success("✨ Nuovo articolo aggiunto all'inventario!")
                                else:
                                    st.success("✅ Movimento confermato!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Errore: {str(e)}")
                    
                    st.markdown("---")
        else:
            st.info("👍 Nessun movimento da confermare")
    
    # Tab 3: Inventario
    with tab3:
        st.header("Inventario Attuale")
        
        # Aggiungi nuovo articolo
        with st.expander("➕ Aggiungi Nuovo Articolo"):
            with st.form("nuovo_articolo"):
                codice = st.text_input("Codice Materia Prima")
                descrizione = st.text_input("Descrizione")
                quantita = st.number_input("Quantità Iniziale", min_value=0.0, step=0.01)
                
                if st.form_submit_button("Aggiungi"):
                    try:
                        # Inserisci come movimento di carico
                        movimento_id = db_manager.insert_movimento(codice, descrizione, quantita, "carico")
                        # Conferma subito il movimento
                        db_manager.conferma_movimento(movimento_id)
                        st.success("✅ Articolo aggiunto con successo!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Errore: {str(e)}")
        
        # Visualizza inventario
        inventario = db_manager.get_inventario()
        if inventario:
            # Converti in DataFrame per una migliore visualizzazione
            df = pd.DataFrame(inventario)
            df['ultimo_aggiornamento'] = pd.to_datetime(df['ultimo_aggiornamento']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Aggiungi pulsanti di modifica per ogni riga
            for idx, row in df.iterrows():
                with st.expander(f"📦 {row['codice_materia_prima']} - {row['descrizione']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Quantità attuale:** {row['quantita_disponibile']}")
                        st.write(f"**Ultimo aggiornamento:** {row['ultimo_aggiornamento']}")
                    
                    with col2:
                        # Form per modificare la quantità
                        with st.form(f"modifica_{row['codice_materia_prima']}"):
                            nuova_quantita = st.number_input(
                                "Nuova quantità",
                                value=float(row['quantita_disponibile']),
                                step=0.01
                            )
                            
                            if st.form_submit_button("📝 Aggiorna"):
                                try:
                                    # Calcola la differenza
                                    diff = nuova_quantita - float(row['quantita_disponibile'])
                                    if diff != 0:
                                        # Inserisci come movimento
                                        movimento_id = db_manager.insert_movimento(
                                            row['codice_materia_prima'],
                                            row['descrizione'],
                                            abs(diff),
                                            "carico" if diff > 0 else "scarico"
                                        )
                                        # Conferma subito il movimento
                                        db_manager.conferma_movimento(movimento_id)
                                        st.success("✅ Quantità aggiornata!")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Errore: {str(e)}")
        else:
            st.info("Nessun articolo in inventario")
    
    # Tab 4: Log Operazioni
    with tab4:
        st.header("Log Operazioni")
        
        log_operazioni = db_manager.get_log_operazioni()
        if log_operazioni:
            for log in log_operazioni:
                with st.container():
                    # Formatta la data
                    data = log['data_operazione'].strftime("%Y-%m-%d %H:%M")
                    
                    if log['tipo_operazione'] == 'nuovo_articolo':
                        st.markdown(f"""
                            <div class="success-box">
                                ✨ Nuovo articolo: {log['codice_materia_prima']}<br>
                                📅 {data}<br>
                                Quantità iniziale: {log['quantita_risultante']}
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div class="{'success-box' if log['tipo_operazione'] == 'carico' else 'warning-box'}">
                                {'📥' if log['tipo_operazione'] == 'carico' else '📤'} {log['codice_materia_prima']}<br>
                                📅 {data}<br>
                                Quantità precedente: {log['quantita_precedente']} →
                                Modifica: {'+' if log['tipo_operazione'] == 'carico' else '-'}{abs(log['quantita_modificata'])} →
                                Risultato: {log['quantita_risultante']}
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("---")
        else:
            st.info("Nessuna operazione registrata")

if __name__ == "__main__":
    main() 