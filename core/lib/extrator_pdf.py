"""
Extrator de conteúdo estruturado de PDFs.

Centraliza a lógica de extração de habilidades BNCC, conceitos,
atividades práticas e contexto de aula a partir do texto extraído.
"""

import re
import unicodedata


def _normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def _limpar_trecho(texto: str) -> str:
    texto = re.sub(r"\s+", " ", str(texto or "")).strip(" -:;•●")
    texto = re.sub(r"\.{2,}", ".", texto)
    return texto.strip()


_TRECHOS_DESCARTAVEIS = (
    "freepik", "seduc-sp", "produzido pela", "veja no livro",
    "de olho no pnld", "link para", "disponivel em", "disponível em", "slide",
)

_FINS_FRAGMENTADOS = {
    "a", "as", "o", "os", "um", "uma", "de", "da", "das", "do", "dos",
    "em", "e", "com", "para", "por",
}


def _trecho_descartavel(texto: str) -> bool:
    texto = _limpar_trecho(texto)
    if not texto:
        return True
    normalizado = _normalizar_texto(texto)
    if any(marcador in normalizado for marcador in _TRECHOS_DESCARTAVEIS):
        return True
    if any(seta in texto for seta in ["⬅", "←", "→"]):
        return True
    if texto.count("?") >= 2:
        return True
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto)
    if palavras and _normalizar_texto(palavras[-1]) in _FINS_FRAGMENTADOS:
        return True
    primeira = texto[:1]
    inicio = _normalizar_texto(texto)
    if primeira.islower() and not inicio.startswith(("a ", "o ", "as ", "os ", "um ", "uma ", "essa ", "esse ", "esta ", "este ")):
        return True
    return False


def _trecho_seguro(texto: str, fallback: str, limite: int = 220) -> str:
    texto = _limpar_trecho(texto)
    if _trecho_descartavel(texto):
        return fallback
    if len(texto) <= limite:
        return texto
    recorte = texto[:limite].rsplit(" ", 1)[0].strip()
    return recorte if not _trecho_descartavel(recorte) else fallback


# Padrões de habilidades BNCC / AE
_PADRAO_HABILIDADE = re.compile(
    r'((?:EM|EF)\d{2}[A-Z]{2}\d{2}[A-Z]?'
    r'|AE\d+\s*[-–]?\s*[^\n]{10,})',
    re.IGNORECASE
)
_PADRAO_HABILIDADE_TEXTO = re.compile(
    r'(?:habilidade|aprendizagem essencial|competência)[:\s]*([^\n]{20,})',
    re.IGNORECASE
)


class ExtratorPDF:
    """Extrai conteúdo estruturado de texto de PDF."""

    # Filtros para linhas de conceito/prática
    _FILTROS = [
        "todo mundo escreve", "virem e conversem", "com suas palavras",
        "hora da leitura", "de olho no modelo", "link para vídeo",
        "um passo de cada vez", "slide", "aula", "veja no livro",
        "freepik", "produzido pela", "seduc-sp", "de olho no pnld",
    ]

    def extrair(self, texto: str, tema: str) -> dict:
        """
        Extrai informações estruturadas do texto do PDF.

        Retorna dict com:
            - conceito_extraido: conceito principal identificado
            - atividade_extraida: atividade prática encontrada
            - habilidade: habilidade BNCC/AE, se presente
            - contexto_aula: pergunta ou situação de abertura
            - palavras_chave: termos relevantes
            - etapas_detectadas: seções do material (para começar, etc.)
            - recursos_detectados: tipos de recursos (leitura, cálculo, etc.)
        """
        linhas = [linha.strip() for linha in texto.split('\n') if linha.strip()]

        conceito = tema
        atividade_pratica = ""
        habilidade = ""
        contexto_aula = ""
        palavras_chave = []
        etapas_detectadas = []

        # 1. Extrair habilidade/BNCC
        habilidade = self._extrair_habilidade(linhas)

        # 2. Extrair conceito
        conceito = self._extrair_conceito(linhas, tema)

        # 3. Extrair atividade prática
        atividade_pratica = self._extrair_pratica(linhas, tema)

        # 4. Extrair contexto/abertura
        contexto_aula = self._extrair_contexto(linhas)

        # 5. Palavras-chave
        palavras_chave = self._extrair_palavras_chave(linhas)

        # 6. Etapas detectadas no material
        etapas_detectadas = self._detectar_etapas(linhas)

        # 7. Recursos detectados
        from core.lib.classificador import detectar_recursos
        recursos = detectar_recursos(texto, tema)

        return {
            "conceito_extraido": _trecho_seguro(conceito, tema, 220),
            "atividade_extraida": _trecho_seguro(
                atividade_pratica,
                f"atividades propostas no material, articuladas ao tema {tema}",
                220,
            ),
            "habilidade": habilidade,
            "contexto_aula": _trecho_seguro(contexto_aula, "", 160),
            "palavras_chave": palavras_chave,
            "etapas_detectadas": etapas_detectadas,
            "recursos_detectados": recursos,
            "linhas": linhas,
        }

    def _linha_valida(self, linha: str) -> bool:
        ll = linha.lower()
        return len(linha) > 10 and not any(
            ll.startswith(f) or ll == f or f in ll for f in self._FILTROS
        )

    def _extrair_habilidade(self, linhas: list[str]) -> str:
        for linha in linhas:
            m = _PADRAO_HABILIDADE.search(linha)
            if m:
                return linha.strip()
        for linha in linhas:
            m = _PADRAO_HABILIDADE_TEXTO.search(linha)
            if m:
                return m.group(1).strip()
        return ""

    def _extrair_conceito(self, linhas: list[str], tema: str) -> str:
        marcadores = [
            "o que é", "definição", "conceito", "é o uso de", "é uma estratégia",
            "consiste em", "refere-se a", "trata-se de", "podemos definir",
        ]
        for i, linha in enumerate(linhas):
            linha_lower = linha.lower()
            if any(m in linha_lower for m in marcadores):
                bloco = []
                if self._linha_valida(linha):
                    bloco.append(linha)
                for j in range(i + 1, min(i + 4, len(linhas))):
                    if self._linha_valida(linhas[j]):
                        bloco.append(linhas[j])
                if bloco:
                    return " ".join(bloco)[:300]
                break
        return tema

    def _extrair_pratica(self, linhas: list[str], tema: str) -> str:
        marcadores = [
            "atividade", "exercício", "na prática", "veja no livro",
            "assistam", "leiam o texto", "analise", "compare",
            "identifique", "reescreva", "produz",
        ]
        for i, linha in enumerate(linhas):
            linha_lower = linha.lower()
            if any(m in linha_lower for m in marcadores) and len(linha) > 15:
                bloco = []
                if self._linha_valida(linha):
                    bloco.append(linha)
                for j in range(i + 1, min(i + 5, len(linhas))):
                    if self._linha_valida(linhas[j]):
                        bloco.append(linhas[j])
                if bloco:
                    return " ".join(bloco)[:300]
                break
        return "atividades propostas no material"

    def _extrair_contexto(self, linhas: list[str]) -> str:
        marcadores = [
            "você já", "pense em", "imagine", "o que as pessoas",
            "qual é a importância", "como você", "nas últimas aulas",
        ]
        for linha in linhas:
            linha_lower = linha.lower()
            if any(m in linha_lower for m in marcadores) and len(linha) > 20:
                return _trecho_seguro(linha, "", 160)
        return ""

    def _extrair_palavras_chave(self, linhas: list[str]) -> list[str]:
        palavras_chave = []
        for linha in linhas:
            if 5 < len(linha) < 60 and not linha.startswith("AULA") and not linha.startswith("Slide"):
                palavras_chave.append(linha)
            if len(palavras_chave) >= 5:
                break
        return palavras_chave

    def _detectar_etapas(self, linhas: list[str]) -> list[str]:
        """Detecta quais seções metodológicas existem no material."""
        etapas_conhecidas = {
            "para comecar", "relembre", "exploracao", "foco no conteudo",
            "formalizacao", "pause e responda", "na pratica",
            "encerramento", "sistematizacao", "contextualizacao",
            "leitura analitica", "leitura e construcao do conteudo",
        }
        encontradas = []
        for linha in linhas:
            normalizada = _normalizar_texto(linha)
            if normalizada in etapas_conhecidas:
                encontradas.append(normalizada)
        return encontradas
