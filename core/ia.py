import os
import json
import traceback
from pydantic import BaseModel, Field

# Fallback para as dependências
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from config import IA_TIMEOUT_SEGUNDOS

class EtapaMetodologia(BaseModel):
    titulo: str = Field(description="Título da etapa, ex: 'Para começar', 'Foco no conteúdo', 'Na prática'")
    texto: str = Field(description="Texto descritivo com a ação do professor e os recursos utilizados.")

class PlanoAulaIA(BaseModel):
    tema: str = Field(description="O título principal ou tema da aula (ex: 'AULA 1 - Anuncie aqui! – Parte 1').")
    aprendizagem: str = Field(description="A aprendizagem essencial e/ou código da BNCC exato encontrado no slide.")
    metodologia: list[EtapaMetodologia] = Field(description="As etapas de desenvolvimento da aula.")

def processar_plano_ia(texto_pdf: str, disciplina: str, turma: str, provedor: str, modelo: str) -> dict:
    prompt = f"""Você é um especialista em planejamento pedagógico. Extraia as informações do slide abaixo.
DISCIPLINA: {disciplina}
TURMA: {turma}

REGRAS:
1. Extraia o TEMA exato da aula.
2. Identifique o código da BNCC (ex: EM13LP44A) e a descrição da 'Aprendizagem Essencial' se houver.
3. Elabore a metodologia dividindo em etapas claras (ex: Relembre, Foco no Conteúdo, Na Prática, Encerramento), detalhando o que o professor fará.
4. Varie os inícios das frases entre as etapas e entre aulas diferentes. Evite repetir sempre fórmulas como "Retomar a importância", "Promover discussão" ou "Orientar a resolução", mantendo linguagem natural, objetiva e pedagógica.
Devolva APENAS JSON válido seguindo a estrutura solicitada.

CONTEÚDO DO SLIDE:
{texto_pdf[:6000]}
"""

    if provedor.lower() == "openai":
        if not OpenAI or not os.getenv("OPENAI_API_KEY"):
            raise Exception("Chave OPENAI_API_KEY não configurada ou biblioteca ausente.")
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.beta.chat.completions.parse(
            model=modelo or "gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format=PlanoAulaIA,
            timeout=IA_TIMEOUT_SEGUNDOS
        )
        data = json.loads(response.choices[0].message.content)
        return {
            "tema": data["tema"],
            "aprendizagem": data["aprendizagem"],
            "metodologia": [{"titulo": m["titulo"], "texto": m["texto"]} for m in data["metodologia"]]
        }

    elif provedor.lower() == "gemini":
        if not genai or not os.getenv("GEMINI_API_KEY"):
            raise Exception("Chave GEMINI_API_KEY não configurada ou biblioteca ausente.")
        
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt_json = prompt + "\nRESPONDA EXATAMENTE NO SEGUINTE FORMATO JSON: {\"tema\": \"...\", \"aprendizagem\": \"...\", \"metodologia\": [{\"titulo\": \"...\", \"texto\": \"...\"}]}"
        
        response = client.models.generate_content(
            model=modelo or "gemini-2.5-flash",
            contents=prompt_json,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        data = json.loads(text.strip())
        return {
            "tema": data.get("tema", ""),
            "aprendizagem": data.get("aprendizagem", ""),
            "metodologia": data.get("metodologia", [])
        }
    
    raise Exception(f"Provedor {provedor} desconhecido.")
