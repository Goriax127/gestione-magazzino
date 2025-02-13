import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        # URL del database Railway
        DATABASE_URL = "postgresql://postgres:pPzplFUUKBqzjkDNhpmEKXzlMvFpjkZm@autorack.proxy.rlwy.net:11988/railway"
        self.conn = psycopg2.connect(DATABASE_URL)
        self.conn.autocommit = True

    def insert_movimento(self, codice, descrizione, quantita, tipo_movimento):
        """Inserisce un nuovo movimento"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO movimentazioni (codice_materia_prima, descrizione, quantita, tipo_movimento)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (codice, descrizione, quantita, tipo_movimento))
            return cur.fetchone()[0]

    def get_movimenti_da_confermare(self):
        """Recupera tutti i movimenti da confermare"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM movimentazioni 
                WHERE stato = 'da_confermare'
                ORDER BY data_creazione DESC
            """)
            return cur.fetchall()

    def conferma_movimento(self, movimento_id):
        """Conferma un movimento e aggiorna l'inventario"""
        with self.conn.cursor() as cur:
            # Recupera i dettagli del movimento
            cur.execute("""
                SELECT * FROM movimentazioni 
                WHERE id = %s AND stato = 'da_confermare'
            """, (movimento_id,))
            movimento = cur.fetchone()
            
            if not movimento:
                raise ValueError("Movimento non trovato o già confermato")

            codice = movimento[1]  # codice_materia_prima
            quantita = movimento[3]  # quantita
            tipo_movimento = movimento[4]  # tipo_movimento
            
            # Verifica se la materia prima esiste
            cur.execute("""
                SELECT quantita_disponibile 
                FROM materie_prime 
                WHERE codice_materia_prima = %s
            """, (codice,))
            result = cur.fetchone()
            
            if result:
                # Aggiorna quantità esistente
                quantita_precedente = result[0]
                nuova_quantita = (quantita_precedente + quantita) if tipo_movimento == 'carico' else (quantita_precedente - quantita)
                
                cur.execute("""
                    UPDATE materie_prime 
                    SET quantita_disponibile = %s,
                        ultimo_aggiornamento = CURRENT_TIMESTAMP
                    WHERE codice_materia_prima = %s
                """, (nuova_quantita, codice))
                
                # Log dell'operazione
                cur.execute("""
                    INSERT INTO log_operazioni 
                    (codice_materia_prima, tipo_operazione, quantita_precedente, 
                     quantita_modificata, quantita_risultante)
                    VALUES (%s, %s, %s, %s, %s)
                """, (codice, tipo_movimento, quantita_precedente, quantita, nuova_quantita))
                
                is_new_item = False
            else:
                # Inserisce nuova materia prima
                cur.execute("""
                    INSERT INTO materie_prime 
                    (codice_materia_prima, descrizione, quantita_disponibile)
                    VALUES (%s, %s, %s)
                """, (codice, movimento[2], quantita if tipo_movimento == 'carico' else -quantita))
                
                # Log della nuova materia prima
                cur.execute("""
                    INSERT INTO log_operazioni 
                    (codice_materia_prima, tipo_operazione, quantita_precedente, 
                     quantita_modificata, quantita_risultante)
                    VALUES (%s, 'nuovo_articolo', 0, %s, %s)
                """, (codice, quantita, quantita if tipo_movimento == 'carico' else -quantita))
                
                is_new_item = True
            
            # Aggiorna stato movimento
            cur.execute("""
                UPDATE movimentazioni 
                SET stato = 'confermato',
                    data_conferma = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (movimento_id,))
            
            return is_new_item

    def get_inventario(self):
        """Recupera l'inventario completo"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM materie_prime 
                ORDER BY codice_materia_prima
            """)
            return cur.fetchall()

    def get_log_operazioni(self, limit=100):
        """Recupera gli ultimi log delle operazioni"""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM log_operazioni 
                ORDER BY data_operazione DESC 
                LIMIT %s
            """, (limit,))
            return cur.fetchall()

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close() 