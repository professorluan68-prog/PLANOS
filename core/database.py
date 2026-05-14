import sqlite3
import json
from pathlib import Path
import os

DB_PATH = Path(__file__).resolve().parent.parent / "sistema.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Tabela de Professores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS professores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Tabela de Turmas/Disciplinas por Professor
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS professor_turmas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_id INTEGER,
                disciplina TEXT,
                turma TEXT,
                dia_semana TEXT,
                horario TEXT,
                aulas_semana TEXT,
                FOREIGN KEY(professor_id) REFERENCES professores(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabela de Histórico de Planos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_planos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_nome TEXT,
                disciplina TEXT,
                turma TEXT,
                data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                arquivo_nome TEXT,
                arquivo_docx BLOB
            )
        ''')
        
        # Tabela de Configurações do Usuário
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
        ''')
        conn.commit()

def migrar_json_para_sqlite():
    json_path = Path(__file__).resolve().parent.parent / "professores.json"
    if not json_path.exists():
        return
        
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            dados = json.load(f)
            
        with get_connection() as conn:
            cursor = conn.cursor()
            for professor, info in dados.items():
                cursor.execute('INSERT OR IGNORE INTO professores (nome) VALUES (?)', (professor,))
                cursor.execute('SELECT id FROM professores WHERE nome = ?', (professor,))
                prof_id = cursor.fetchone()[0]
                
                disciplinas = info.get("disciplinas", [])
                for d in disciplinas:
                    # Check if already exists to avoid duplicates if migration runs multiple times
                    cursor.execute('''
                        SELECT id FROM professor_turmas 
                        WHERE professor_id = ? AND disciplina = ? AND turma = ?
                    ''', (prof_id, d.get("disciplina"), d.get("turma")))
                    
                    if not cursor.fetchone():
                        cursor.execute('''
                            INSERT INTO professor_turmas 
                            (professor_id, disciplina, turma, dia_semana, horario, aulas_semana)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            prof_id, 
                            d.get("disciplina"), 
                            d.get("turma"), 
                            d.get("dia_semana"), 
                            d.get("horario"), 
                            d.get("aulas_semana")
                        ))
            conn.commit()
            
        # Renomear o json para backup após migração com sucesso
        os.rename(json_path, json_path.with_suffix(".json.backup"))
    except Exception as e:
        print(f"Erro na migração do JSON: {e}")

# Funções de CRUD para app.py
def obter_professores_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.nome, t.disciplina, t.turma, t.dia_semana, t.horario, t.aulas_semana
            FROM professores p
            LEFT JOIN professor_turmas t ON p.id = t.professor_id
            ORDER BY
                p.nome,
                CASE
                    WHEN COALESCE(t.dia_semana, '') <> ''
                     AND COALESCE(t.horario, '') <> ''
                     AND COALESCE(t.aulas_semana, '') <> '' THEN 0
                    ELSE 1
                END,
                t.disciplina,
                t.turma
        ''')
        
        resultado = {}
        for row in cursor.fetchall():
            nome = row[0]
            if nome not in resultado:
                resultado[nome] = {"disciplinas": []}
            if row[1] and row[3] and row[4] and row[5]: # mostra no seletor apenas aulas com agenda utilizável
                resultado[nome]["disciplinas"].append({
                    "disciplina": row[1],
                    "turma": row[2],
                    "dia_semana": row[3],
                    "horario": row[4],
                    "aulas_semana": row[5]
                })
        return resultado

def salvar_professor_turma(nome, disciplina, turma, dia_semana, horario, aulas_semana):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO professores (nome) VALUES (?)', (nome,))
        cursor.execute('SELECT id FROM professores WHERE nome = ?', (nome,))
        prof_id = cursor.fetchone()[0]
        
        cursor.execute('''
            INSERT INTO professor_turmas (professor_id, disciplina, turma, dia_semana, horario, aulas_semana)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (prof_id, disciplina, turma, dia_semana, horario, aulas_semana))
        conn.commit()

def salvar_historico_plano(professor_nome, disciplina, turma, arquivo_nome, arquivo_docx_bytes):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO historico_planos (professor_nome, disciplina, turma, arquivo_nome, arquivo_docx)
            VALUES (?, ?, ?, ?, ?)
        ''', (professor_nome, disciplina, turma, arquivo_nome, arquivo_docx_bytes))
        conn.commit()

def listar_historico_planos():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, professor_nome, disciplina, turma, data_geracao, arquivo_nome
            FROM historico_planos
            ORDER BY data_geracao DESC
            LIMIT 50
        ''')
        return cursor.fetchall()
        
def obter_arquivo_historico(plano_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT arquivo_nome, arquivo_docx FROM historico_planos WHERE id = ?', (plano_id,))
        return cursor.fetchone()
