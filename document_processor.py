import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from dotenv import load_dotenv
import re

class DocumentProcessor:
    def __init__(self):
        load_dotenv()
        
        endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
        key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
        
        if not endpoint or not key:
            raise ValueError("Azure Form Recognizer credentials not found in .env file")
            
        self.document_analysis_client = DocumentAnalysisClient(
            endpoint=endpoint, 
            credential=AzureKeyCredential(key)
        )

    def _is_valid_code(self, text):
        """Verifica se il testo è un codice valido (non vuoto e non inizia con RIF)"""
        if not text:
            return False
        text = text.strip().upper()
        return text and not text.startswith('RIF')

    def _is_valid_quantity(self, text):
        """Verifica se il testo è una quantità valida"""
        if not text:
            return False
        # Rimuovi spazi e sostituisci la virgola con il punto
        text = text.strip().replace(',', '.')
        # Verifica se è un numero
        try:
            float(text)
            return True
        except ValueError:
            return False

    def _find_table_columns(self, table):
        """
        Trova gli indici delle colonne basandosi sulle intestazioni.
        """
        col_indices = {"codice": -1, "descrizione": -1, "quantita": -1}
        
        # Cerca nelle prime righe della tabella per trovare le intestazioni
        for row in range(min(3, table.row_count)):  # Controlla solo le prime 3 righe
            for col in range(table.column_count):
                cell_content = table.cells[row * table.column_count + col].content.upper()
                if "COD" in cell_content:
                    col_indices["codice"] = col
                elif "DESC" in cell_content:
                    col_indices["descrizione"] = col
                elif any(q in cell_content for q in ["QUAN", "QTA", "Q.TA"]):
                    col_indices["quantita"] = col
        
        # Se abbiamo trovato tutte le colonne
        if -1 not in col_indices.values():
            return col_indices
        return None

    def _extract_table_data(self, table):
        """
        Estrae i dati da tutte le righe valide della tabella.
        """
        col_indices = self._find_table_columns(table)
        if not col_indices:
            return None
            
        extracted_items = []
        
        # Esamina tutte le righe della tabella
        for row in range(table.row_count):
            # Estrai i valori delle celle per questa riga
            codice = table.cells[row * table.column_count + col_indices["codice"]].content.strip()
            descrizione = table.cells[row * table.column_count + col_indices["descrizione"]].content.strip()
            quantita = table.cells[row * table.column_count + col_indices["quantita"]].content.strip()
            
            # Verifica se la riga è valida (ha un codice valido e una quantità)
            if self._is_valid_code(codice) and self._is_valid_quantity(quantita):
                item_data = {
                    "codice_materia_prima": codice,
                    "descrizione": descrizione,
                    "quantita": quantita.replace(',', '.'),
                    "riferimento_cliente": ""
                }
                extracted_items.append(item_data)
        
        return extracted_items if extracted_items else None

    async def process_document(self, document_path):
        """
        Processa un documento cercando specificamente una tabella con la struttura attesa.
        
        Args:
            document_path (str): Percorso del file del documento
            
        Returns:
            list: Lista di dizionari con i dati estratti per ogni riga valida
        """
        try:
            with open(document_path, "rb") as f:
                poller = self.document_analysis_client.begin_analyze_document(
                    "prebuilt-document", document=f
                )
            result = poller.result()
            
            # Cerca la tabella con la struttura corretta
            for table in result.tables:
                extracted_items = self._extract_table_data(table)
                if extracted_items:
                    return extracted_items
            
            raise Exception("Nessuna riga valida trovata con la struttura attesa (Codice, Descrizione, Quantità)")
            
        except Exception as e:
            raise Exception(f"Errore durante l'elaborazione del documento: {str(e)}") 