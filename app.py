import streamlit as st
import os
import tempfile
import asyncio
from document_processor import DocumentProcessor
from airtable_manager import AirtableManager

# Configurazione della pagina
st.set_page_config(
    page_title="Gestione Documenti",
    layout="wide",
    initial_sidebar_state="collapsed"  # Nascondi la sidebar su mobile
)

# Stile CSS personalizzato per mobile
st.markdown("""
    <style>
    /* Stile per i pulsanti radio */
    .stRadio > label {
        font-size: 1.2rem !important;
        padding: 1rem !important;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    /* Stile per i pulsanti */
    .stButton > button {
        width: 100%;
        padding: 1rem 0.5rem;
        font-size: 1.1rem;
        margin: 0.5rem 0;
    }
    
    /* Stile per il titolo */
    h1 {
        font-size: 1.8rem !important;
        text-align: center;
        padding: 1rem 0;
    }
    
    /* Stile per i sottotitoli */
    h2, h3 {
        font-size: 1.4rem !important;
        padding: 0.8rem 0;
    }
    
    /* Stile per la tabella */
    .dataframe {
        font-size: 0.9rem !important;
    }
    
    /* Stile per i messaggi informativi */
    .stAlert {
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

async def process_document_async(doc_processor, file_path):
    """Wrapper asincrono per il processing del documento"""
    return await doc_processor.process_document(file_path)

def main():
    st.title("📦 Gestione Magazzino")
    
    # Inizializza i manager
    doc_processor = DocumentProcessor()
    airtable_mgr = AirtableManager()
    
    # STEP 1: Selezione del tipo di movimento
    st.header("📋 Step 1: Seleziona Tipo Movimento")
    tipo_movimento = st.radio(
        "",  # Label vuota per un look più pulito
        options=["carico", "scarico"],
        format_func=lambda x: "📥 CARICO" if x == "carico" else "📤 SCARICO",
        horizontal=True  # Disposizione orizzontale per i radio button
    )
    
    # Mostra un box colorato con il tipo di movimento selezionato
    movimento_color = "#a8e6cf" if tipo_movimento == "carico" else "#ffb3b3"
    st.markdown(f"""
        <div style="background-color: {movimento_color}; padding: 1rem; border-radius: 10px; text-align: center; margin: 1rem 0;">
            <h3 style="margin: 0; color: #1e1e1e;">Movimento selezionato: {tipo_movimento.upper()}</h3>
        </div>
    """, unsafe_allow_html=True)
    
    # STEP 2: Caricamento documento
    st.header("📸 Step 2: Carica Documento")
    st.info("📱 Puoi scattare una foto del documento o caricare un file esistente")
    
    uploaded_file = st.file_uploader(
        "",  # Label vuota per un look più pulito
        type=["pdf", "png", "jpg", "jpeg"],
        help="Supporta PDF e immagini (PNG, JPG)"
    )
    
    # Area principale
    if uploaded_file is not None:
        try:
            # Mostra preview del file caricato se è un'immagine
            if uploaded_file.type.startswith('image/'):
                st.image(uploaded_file, caption="Anteprima documento", use_column_width=True)
            
            # Salva temporaneamente il file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # Processa il documento
            with st.spinner("🔍 Analisi del documento in corso..."):
                extracted_items = asyncio.run(process_document_async(doc_processor, tmp_path))
            
            if extracted_items:
                # STEP 3: Verifica dati
                st.header("✅ Step 3: Verifica i Dati")
                st.success(f"Trovati {len(extracted_items)} elementi nel documento")
                
                # Mostra i dati in una tabella scrollabile orizzontalmente
                st.markdown("""
                    <div style="overflow-x: auto;">
                """, unsafe_allow_html=True)
                
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
                
                # STEP 4: Conferma
                st.header("🚀 Step 4: Conferma Operazione")
                if st.button("✅ CONFERMA E SALVA", use_container_width=True):
                    with st.spinner("💾 Salvataggio in corso..."):
                        records = []
                        for item in extracted_items:
                            record = airtable_mgr.insert_record(item, tipo_movimento)
                            records.append(record)
                    st.success(f"✅ Salvati con successo {len(records)} elementi!")
                    
                    # Mostra i dettagli in un expander
                    with st.expander("📋 Dettagli operazione"):
                        for i, record in enumerate(records, 1):
                            st.write(f"Record {i}:", record)
            
            # Pulisci il file temporaneo
            os.unlink(tmp_path)
            
        except Exception as e:
            st.error(f"❌ Si è verificato un errore: {str(e)}")
    
    else:
        # Mostra un messaggio guida quando non c'è ancora un file
        st.info("👆 Tocca il pulsante sopra per caricare un documento o scattare una foto")

if __name__ == "__main__":
    main() 