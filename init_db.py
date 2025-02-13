import psycopg2

def init_database():
    """Inizializza il database con le tabelle necessarie"""
    
    # Connessione al database usando l'URL completo
    conn = psycopg2.connect("postgresql://postgres:pPzplFUUKBqzjkDNhpmEKXzlMvFpjkZm@autorack.proxy.rlwy.net:11988/railway")
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Tabella Movimentazioni
            cur.execute("""
                CREATE TABLE IF NOT EXISTS movimentazioni (
                    id SERIAL PRIMARY KEY,
                    codice_materia_prima VARCHAR(50),
                    descrizione TEXT,
                    quantita DECIMAL(10,2),
                    tipo_movimento VARCHAR(10),
                    stato VARCHAR(20) DEFAULT 'da_confermare',
                    data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_conferma TIMESTAMP
                )
            """)
            
            # Tabella Materie Prime (inventario)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS materie_prime (
                    codice_materia_prima VARCHAR(50) PRIMARY KEY,
                    descrizione TEXT,
                    quantita_disponibile DECIMAL(10,2),
                    ultimo_aggiornamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabella Log Operazioni
            cur.execute("""
                CREATE TABLE IF NOT EXISTS log_operazioni (
                    id SERIAL PRIMARY KEY,
                    codice_materia_prima VARCHAR(50),
                    tipo_operazione VARCHAR(50),
                    quantita_precedente DECIMAL(10,2),
                    quantita_modificata DECIMAL(10,2),
                    quantita_risultante DECIMAL(10,2),
                    data_operazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operatore VARCHAR(50)
                )
            """)
            
            print("Database inizializzato con successo!")
            
    except Exception as e:
        print(f"Errore durante l'inizializzazione del database: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_database() 