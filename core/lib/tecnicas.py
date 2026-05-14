"""
Catálogo e seletor de técnicas pedagógicas (Lemov e outras).

Organiza as técnicas por momento da aula e tipo de atividade,
permitindo seleção variada e sem repetição entre aulas.
"""

import hashlib


# ── Catálogo completo de técnicas por momento da aula ───────────────────────

TECNICAS_POR_MOMENTO = {
    "abertura": {
        "discussao": [
            "Virem e conversem",
            "Roda de conversa breve",
            "Troca rápida em duplas",
            "Chuva de ideias coletiva",
        ],
        "retomada": [
            "Relembre",
            "Quiz oral de retomada",
            "Pergunta-desafio no quadro",
            "Retomada com palavra-chave",
        ],
        "contextualizacao": [
            "Situação-problema do cotidiano",
            "Imagem provocadora",
            "Pergunta geradora",
            "Caso real para análise",
        ],
    },
    "desenvolvimento": {
        "leitura": [
            "Hora da leitura",
            "Leitura compartilhada",
            "Leitura guiada com pausas",
            "Leitura silenciosa com destaque",
        ],
        "registro": [
            "Todo mundo escreve",
            "Mapa mental colaborativo",
            "Esquema no caderno",
            "Registro com palavras-chave",
            "Resumo guiado por tópicos",
        ],
        "modelagem": [
            "De olho no modelo",
            "Um passo de cada vez",
            "Resolução comentada no quadro",
            "Exemplo passo a passo",
        ],
        "investigacao": [
            "Formulem hipóteses",
            "Registrem observações",
            "Comparem resultados",
            "Testem previsões",
        ],
    },
    "verificacao": {
        "formativa": [
            "Pause e responda",
            "Bilhete de saída",
            "Polegar (concordo/discordo)",
            "Responda no papel",
            "Quadro de dúvidas",
        ],
        "mediada": [
            "Circular pela sala",
            "Verificar a compreensão",
            "Correção coletiva dialogada",
            "Socialização de respostas",
            "Troca de cadernos entre duplas",
        ],
    },
    "encerramento": {
        "sintese": [
            "Com suas palavras",
            "Resumo coletivo no quadro",
            "Palavra-chave da aula",
            "Três aprendizagens da aula",
            "Frase-síntese individual",
        ],
        "autoavaliacao": [
            "Bilhete de saída",
            "Termômetro da aprendizagem",
            "O que aprendi / O que ainda preciso rever",
            "Autoavaliação breve oral",
        ],
    },
}

# ── Técnicas por perfil disciplinar ─────────────────────────────────────────

TECNICAS_POR_PERFIL = {
    "lingua_portuguesa_ef": {
        "discussao": "Virem e conversem",
        "registro": "Todo mundo escreve",
        "sintese": "Com suas palavras",
        "verificacao": "Pause e responda",
    },
    "lingua_portuguesa_em": {
        "discussao": "Debate orientado",
        "registro": "Todo mundo escreve",
        "sintese": "Com suas palavras",
        "verificacao": "Pause e responda",
    },
    "leitura_redacao": {
        "discussao": "Virem e conversem",
        "registro": "Todo mundo escreve",
        "sintese": "Com suas palavras",
        "verificacao": "Pause e responda",
    },
    "orientacao_estudos": {
        "discussao": "Discussão em duplas sobre estratégias de estudo",
        "registro": "Registro de estratégia no caderno",
        "sintese": "Autoavaliação breve",
        "verificacao": "Bilhete de saída",
    },
    "ciencias_ef": {
        "discussao": "Formulem hipóteses",
        "registro": "Registrem observações",
        "sintese": "Com suas palavras",
        "verificacao": "Pause e responda",
    },
    "biologia": {
        "discussao": "Formulem hipóteses",
        "registro": "Registrem observações",
        "sintese": "Com suas palavras",
        "verificacao": "Verificar a compreensão",
    },
    "quimica": {
        "discussao": "Formulem hipóteses",
        "registro": "Registrem procedimentos e resultados",
        "sintese": "Com suas palavras",
        "verificacao": "Verificar a compreensão",
    },
    "fisica": {
        "discussao": "Observem e levantem hipóteses",
        "registro": "Registrem medidas e relações",
        "sintese": "Com suas palavras",
        "verificacao": "Pause e responda",
    },
    "historia": {
        "discussao": "Analisem as fontes",
        "registro": "Registrem a cronologia",
        "sintese": "Com suas palavras",
        "verificacao": "Verificar a compreensão",
    },
    "geografia": {
        "discussao": "Observem o mapa/imagem",
        "registro": "Registrem as relações espaciais",
        "sintese": "Com suas palavras",
        "verificacao": "Verificar a compreensão",
    },
    "ingles": {
        "discussao": "Listen and repeat",
        "registro": "Write and share",
        "sintese": "Say it in English",
        "verificacao": "Pause e responda",
    },
    "arte": {
        "discussao": "Virem e conversem",
        "registro": "Registro no diário de bordo",
        "sintese": "Apreciação compartilhada",
        "verificacao": "Socialização de respostas",
    },
    "projeto_de_vida": {
        "discussao": "Roda de conversa acolhedora",
        "registro": "Registro pessoal sem exposição obrigatória",
        "sintese": "Compromisso para a semana",
        "verificacao": "Autoavaliação breve",
    },
    "educacao_financeira": {
        "discussao": "análise orientada de caso",
        "registro": "registro de cálculos, critérios e decisões",
        "sintese": "planejamento de aplicação",
        "verificacao": "Verificar a compreensão",
    },
    "matematica": {
        "discussao": "Virem e conversem",
        "registro": "Todo mundo escreve",
        "sintese": "Com suas palavras",
        "verificacao": "Pause e responda",
    },
    "tecnologia_inovacao": {
        "discussao": "Pensem em soluções",
        "registro": "Registrem o protótipo ou algoritmo",
        "sintese": "Apresentem a solução",
        "verificacao": "Verificar a compreensão",
    },
    "sociologia": {
        "discussao": "Debatam o fenômeno social",
        "registro": "Registrem argumentos e evidências",
        "sintese": "Com suas palavras",
        "verificacao": "Socialização de respostas",
    },
    "lideranca_oratoria": {
        "discussao": "Pratiquem em duplas ou grupos",
        "registro": "Registrem feedbacks e avanços",
        "sintese": "Autoavaliação breve",
        "verificacao": "Socialização de respostas",
    },
}


def _indice_hash(partes: list[str], total: int) -> int:
    """Gera índice determinístico baseado em hash para variação controlada."""
    if total <= 1:
        return 0
    chave = "|".join(str(p or "") for p in partes)
    digest = hashlib.blake2b(chave.encode("utf-8", errors="ignore"), digest_size=2).hexdigest()
    return int(digest, 16) % total


class SeletorTecnicas:
    """Seleciona técnicas pedagógicas adequadas com variação controlada."""

    def obter_tecnica_perfil(self, perfil: str, funcao: str) -> str:
        """Retorna a técnica padrão de um perfil para uma função pedagógica."""
        padrao = TECNICAS_POR_PERFIL.get(perfil, TECNICAS_POR_PERFIL.get("lingua_portuguesa_ef", {}))
        return padrao.get(funcao, "")

    def selecionar_tecnica(
        self,
        momento: str,
        tipo_atividade: str,
        seed_parts: list[str] | None = None,
    ) -> str:
        """
        Seleciona uma técnica do catálogo com variação determinística.

        Args:
            momento: 'abertura', 'desenvolvimento', 'verificacao', 'encerramento'
            tipo_atividade: subtipo dentro do momento (ex: 'discussao', 'registro')
            seed_parts: partes para gerar variação (disciplina, turma, tema, etc.)
        """
        opcoes_momento = TECNICAS_POR_MOMENTO.get(momento, {})
        opcoes = opcoes_momento.get(tipo_atividade, [])
        if not opcoes:
            return ""
        idx = _indice_hash(seed_parts or [], len(opcoes))
        return opcoes[idx]

    def selecionar_para_aula(
        self,
        perfil: str,
        tipo_aula: str,
        tema: str,
        indice_aula: int = 0,
    ) -> dict[str, str]:
        """
        Seleciona um conjunto completo de técnicas para uma aula,
        priorizando as do perfil mas variando com base no índice.
        """
        seed = [perfil, tipo_aula, tema, str(indice_aula)]
        padrao = TECNICAS_POR_PERFIL.get(perfil, TECNICAS_POR_PERFIL.get("lingua_portuguesa_ef", {}))

        tecnica_abertura = padrao.get("discussao", "")
        tecnica_registro = padrao.get("registro", "")
        tecnica_sintese = padrao.get("sintese", "")
        tecnica_verificacao = padrao.get("verificacao", "")

        # Variação: a cada 3 aulas, troca a técnica de abertura
        if indice_aula % 3 == 1:
            alternativa = self.selecionar_tecnica("abertura", "retomada", seed)
            if alternativa:
                tecnica_abertura = alternativa
        elif indice_aula % 3 == 2:
            alternativa = self.selecionar_tecnica("abertura", "contextualizacao", seed)
            if alternativa:
                tecnica_abertura = alternativa

        # Variação: alterna técnica de verificação
        if indice_aula % 2 == 1:
            alternativa = self.selecionar_tecnica("verificacao", "mediada", seed)
            if alternativa:
                tecnica_verificacao = alternativa

        # Variação: alterna técnica de encerramento
        if indice_aula % 4 == 3:
            alternativa = self.selecionar_tecnica("encerramento", "autoavaliacao", seed)
            if alternativa:
                tecnica_sintese = alternativa

        return {
            "abertura": tecnica_abertura,
            "registro": tecnica_registro,
            "sintese": tecnica_sintese,
            "verificacao": tecnica_verificacao,
        }
