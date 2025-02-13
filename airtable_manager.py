import os
from pyairtable import Table
from dotenv import load_dotenv

class AirtableManager:
    def __init__(self):
        load_dotenv()
        
        api_key = os.getenv("AIRTABLE_API_KEY")
        base_id = os.getenv("AIRTABLE_BASE_ID")
        table_name = os.getenv("AIRTABLE_TABLE_NAME")
        
        if not all([api_key, base_id, table_name]):
            raise ValueError("Credenziali Airtable mancanti nel file .env")
            
        self.table = Table(api_key, base_id, table_name)
    
    def insert_record(self, data, tipo_movimento):
        """
        Inserisce un nuovo record in Airtable.
        
        Args:
            data (dict): Dati estratti dal documento
            tipo_movimento (str): 'carico' o 'scarico'
            
        Returns:
            dict: Record creato in Airtable
        """
        try:
            record = {
                "Tipo_Movimento": tipo_movimento,
                "Codice_Materia_Prima": data.get("codice_materia_prima", ""),
                "Descrizione": data.get("descrizione", ""),
                "Quantita": float(data.get("quantita", 0)) if data.get("quantita") else 0,
                "Riferimento_Cliente": data.get("riferimento_cliente", ""),
                "Stato": "Da_Confermare"
            }
            
            created_record = self.table.create(record)
            return created_record
            
        except Exception as e:
            raise Exception(f"Errore durante l'inserimento in Airtable: {str(e)}")
    
    def update_record_status(self, record_id, nuovo_stato):
        """
        Aggiorna lo stato di un record.
        
        Args:
            record_id (str): ID del record da aggiornare
            nuovo_stato (str): Nuovo stato del record
        """
        try:
            self.table.update(record_id, {"Stato": nuovo_stato})
        except Exception as e:
            raise Exception(f"Errore durante l'aggiornamento dello stato: {str(e)}") 