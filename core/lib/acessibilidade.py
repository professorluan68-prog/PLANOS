"""
Gerador de estratégias de acessibilidade por tipo de recurso.

Em vez de gerar frases genéricas por disciplina, analisa o tipo de
atividade/recurso presente no conteúdo e seleciona estratégias
específicas de um catálogo organizado.
"""

import re
from core.lib.classificador import normalizar_texto, contem_termos, detectar_recursos
from core.lib.progressao import _indice_hash


# ── Catálogo de estratégias por tipo de recurso/atividade ──────────────────

CATALOGO_ESTRATEGIAS = {
    "leitura_texto": [
        "Realizar leitura mediada com pausas para retomada de vocabulário, comandos, trechos importantes e relações de sentido necessárias à atividade.",
        "Disponibilizar roteiro, esquema ou banco de ideias para apoiar a organização das respostas.",
        "Permitir leitura em dupla com estudante-tutor para apoiar ritmos diferentes de compreensão.",
        "Destacar palavras-chave e trechos centrais no quadro ou projetor antes da leitura individual.",
        "Oferecer perguntas orientadoras por escrito para guiar a leitura e a localização de informações.",
    ],
    "analise_imagem": [
        "Descrever oralmente os elementos da imagem, destacando informações centrais para estudantes com dificuldade de leitura visual.",
        "Ampliar imagens no quadro ou projetor, apontando elementos que devem ser observados.",
        "Oferecer roteiro escrito de observação da imagem com perguntas orientadoras.",
        "Permitir registro por desenho, esquema ou anotação oral das observações.",
    ],
    "analise_grafico": [
        "Ler coletivamente os eixos, legendas e títulos do gráfico ou tabela antes da análise individual.",
        "Disponibilizar versão simplificada ou ampliada dos dados para apoiar a leitura.",
        "Organizar as informações em lista ou tópicos no quadro para facilitar a comparação.",
        "Oferecer questões de leitura guiada para orientar a interpretação dos dados.",
    ],
    "calculo_resolucao": [
        "Disponibilizar resolução comentada e exemplos graduados para favorecer a compreensão dos procedimentos.",
        "Organizar a atividade em etapas curtas com retomadas coletivas e comparação de estratégias.",
        "Oferecer mediação individual durante os registros, permitindo diferentes formas de resolução e conferência.",
        "Disponibilizar material de apoio (tabuada, fórmulas, calculadora) conforme a necessidade.",
        "Apresentar exemplos resolvidos como referência antes da resolução autônoma.",
    ],
    "producao_textual": [
        "Disponibilizar banco de palavras, expressões e modelos de início de parágrafo para apoiar a escrita.",
        "Permitir produção oral com transcrição assistida ou registro por tópicos.",
        "Oferecer checklist de revisão com critérios visuais claros e linguagem acessível.",
        "Organizar a produção em etapas (planejamento, rascunho, revisão) com mediação em cada fase.",
    ],
    "experimentacao": [
        "Garantir acessibilidade física dos materiais e instrumentos para todos os estudantes.",
        "Descrever etapas do experimento em cartões visuais sequenciais com imagens de apoio.",
        "Oferecer registro por desenho, esquema ou explicação oral para estudantes com dificuldade de escrita.",
        "Organizar grupos cooperativos com funções definidas para favorecer a participação de todos.",
    ],
    "debate_oral": [
        "Oferecer perguntas orientadoras por escrito antes da participação oral.",
        "Permitir participação por registro escrito ou sinalização para quem tem dificuldade de fala.",
        "Organizar turnos de fala com mediação para garantir escuta e respeito a todos os participantes.",
        "Disponibilizar tempo para preparação individual antes de socializar posições.",
    ],
    "escuta_audio": [
        "Disponibilizar transcrição ou resumo escrito do conteúdo de áudio ou vídeo.",
        "Permitir repetição do áudio e pausas para anotação e verificação da compreensão.",
        "Oferecer perguntas orientadoras antes da escuta para direcionar a atenção.",
        "Organizar discussão em duplas após a escuta para trocar percepções e complementar informações.",
    ],
}

# ── Estratégias genéricas por perfil (fallback) ────────────────────────────

_FALLBACK_POR_PERFIL = {
    "matematica": [
        "Utilizar resolução comentada, apoio visual e exemplos graduados para favorecer a compreensão do problema, dos procedimentos e das relações matemáticas envolvidas.",
        "Organizar a atividade em etapas curtas, com retomadas coletivas, comparação de estratégias e destaque para dados, operações e representações essenciais.",
        "Oferecer mediação individual durante os registros e cálculos, permitindo diferentes formas de resolução, conferência e explicação das respostas.",
    ],
    "lingua_portuguesa_ef": [
        "Oferecer leitura mediada com pausas para retomada de vocabulário, comandos, trechos importantes e relações de sentido necessárias à atividade.",
        "Disponibilizar roteiro, esquema, banco de ideias ou critérios de análise e produção para apoiar a organização das respostas e textos.",
        "Realizar mediações individuais, retomadas coletivas e flexibilização do registro conforme as necessidades observadas na turma.",
    ],
    "lingua_portuguesa_em": [
        "Oferecer leitura mediada com pausas para retomada de vocabulário, comandos, trechos importantes e relações de sentido necessárias à atividade.",
        "Disponibilizar roteiro, esquema, banco de ideias ou critérios de análise e produção para apoiar a organização das respostas e textos.",
        "Realizar mediações individuais, retomadas coletivas e flexibilização do registro conforme as necessidades observadas na turma.",
    ],
    "leitura_redacao": [
        "Oferecer leitura mediada com pausas para retomada de vocabulário, comandos, trechos importantes e relações de sentido necessárias à atividade.",
        "Disponibilizar roteiro, esquema, banco de ideias ou critérios de análise e produção para apoiar a organização das respostas e textos.",
        "Realizar mediações individuais, retomadas coletivas e flexibilização do registro conforme as necessidades observadas na turma.",
    ],
    "orientacao_estudos": [
        "Modelar estratégias de estudo com exemplos concretos, registros guiados e demonstração de como organizar tempo, materiais e etapas da tarefa.",
        "Retomar os procedimentos com linguagem clara, perguntas orientadoras e apoio visual para favorecer a compreensão do que fazer em cada momento.",
        "Oferecer acompanhamento individualizado e diferentes formas de registro para apoiar estudantes com dificuldades de organização e monitoramento da aprendizagem.",
    ],
    "ciencias_ef": [
        "Utilizar imagens, esquemas, tabelas, demonstrações e exemplos do cotidiano para tornar mais acessíveis os conceitos científicos trabalhados.",
        "Organizar registros guiados com palavras-chave, relações de causa e consequência, etapas do fenômeno e sínteses construídas coletivamente.",
        "Oferecer mediação individual e correção dialogada, permitindo respostas por tópicos, desenhos, setas, explicação oral ou frases curtas quando necessário.",
    ],
    "biologia": [
        "Utilizar imagens, esquemas, tabelas, demonstrações e exemplos do cotidiano para tornar mais acessíveis os conceitos científicos trabalhados.",
        "Organizar registros guiados com palavras-chave, relações de causa e consequência, etapas do fenômeno e sínteses construídas coletivamente.",
        "Oferecer mediação individual e correção dialogada, permitindo respostas por tópicos, desenhos, setas, explicação oral ou frases curtas quando necessário.",
    ],
    "quimica": [
        "Utilizar imagens, esquemas, tabelas, demonstrações e exemplos do cotidiano para tornar mais acessíveis os conceitos científicos trabalhados.",
        "Organizar registros guiados com palavras-chave, relações de causa e consequência, etapas do fenômeno e sínteses construídas coletivamente.",
        "Oferecer mediação individual e correção dialogada, permitindo respostas por tópicos, desenhos, setas, explicação oral ou frases curtas quando necessário.",
    ],
    "fisica": [
        "Utilizar imagens, esquemas, tabelas, demonstrações e exemplos do cotidiano para tornar mais acessíveis os conceitos científicos trabalhados.",
        "Organizar registros guiados com palavras-chave, relações de causa e consequência, etapas do fenômeno e sínteses construídas coletivamente.",
        "Oferecer mediação individual e correção dialogada, permitindo respostas por tópicos, desenhos, setas, explicação oral ou frases curtas quando necessário.",
    ],
    "historia": [
        "Utilizar fontes, imagens, mapas, linhas do tempo e esquemas para apoiar a compreensão dos processos históricos e do vocabulário específico.",
        "Retomar relações de tempo, causa, consequência, permanência e mudança com registros guiados e sínteses no quadro.",
        "Oferecer mediação individual e diferentes formas de resposta, como tópicos, setas, frases curtas, explicação oral ou apoio coletivo na leitura das fontes.",
    ],
    "geografia": [
        "Utilizar mapas, imagens, gráficos, tabelas e exemplos próximos da realidade dos estudantes para favorecer a leitura das diferentes linguagens geográficas.",
        "Organizar registros guiados com palavras-chave, legendas, comparações e relações entre sociedade, natureza e território.",
        "Oferecer mediação individual e retomadas coletivas durante a interpretação das informações e a elaboração das respostas.",
    ],
    "ingles": [
        "Apresentar vocabulário com apoio visual, modelos de frases, leitura guiada e repetições curtas para favorecer a compreensão e a participação.",
        "Organizar as atividades em etapas pequenas, com exemplos de resposta, banco de palavras e checagens frequentes de entendimento.",
        "Permitir respostas por associação, seleção, fala curta, escrita orientada ou produção em dupla, conforme a necessidade dos estudantes.",
    ],
    "arte": [
        "Utilizar imagens, sons, vídeos curtos, demonstrações e exemplos culturais variados para ampliar o acesso aos repertórios mobilizados na aula.",
        "Organizar registros guiados com palavras-chave, comparações e sínteses coletivas para apoiar a leitura e a apreciação das produções artísticas.",
        "Permitir diferentes formas de participação e expressão, como fala, escrita, desenho, criação em dupla ou registro individual orientado.",
    ],
    "projeto_de_vida": [
        "Promover ambiente acolhedor, com combinados de escuta e respeito, para que os estudantes participem sem exposição excessiva de vivências pessoais.",
        "Utilizar perguntas orientadoras, exemplos concretos e registros visuais para apoiar a reflexão e a elaboração das respostas.",
        "Permitir diferentes formas de participação, como fala, escrita, desenho, registro individual ou produção em dupla, respeitando ritmos e necessidades.",
    ],
    "lideranca_oratoria": [
        "Promover ambiente acolhedor, com combinados de escuta e respeito, para que os estudantes participem sem exposição excessiva de vivências pessoais.",
        "Utilizar perguntas orientadoras, exemplos concretos e registros visuais para apoiar a reflexão e a elaboração das respostas.",
        "Permitir diferentes formas de participação, como fala, escrita, desenho, registro individual ou produção em dupla, respeitando ritmos e necessidades.",
    ],
    "educacao_financeira": [
        "Utilizar situações concretas do cotidiano, como compras, orçamento, metas e escolhas de consumo, para favorecer a compreensão do tema.",
        "Organizar cálculos, dados e informações em tabelas, listas, esquemas ou passo a passo no quadro para apoiar leitura e tomada de decisão.",
        "Oferecer mediação individual e correção dialogada, retomando vocabulário financeiro, critérios de escolha e estratégias de resolução conforme as dificuldades observadas.",
    ],
    "tecnologia_inovacao": [
        "Apresentar o conteúdo com exemplos concretos, linguagem clara e apoio visual para favorecer a compreensão dos conceitos e problemas discutidos.",
        "Organizar registros guiados, perguntas orientadoras e sínteses parciais para apoiar a participação e a construção das respostas.",
        "Oferecer acompanhamento individual, retomadas coletivas e flexibilização das formas de registro conforme as necessidades da turma.",
    ],
    "sociologia": [
        "Apresentar o conteúdo com exemplos concretos, linguagem clara e apoio visual para favorecer a compreensão dos conceitos e problemas discutidos.",
        "Organizar registros guiados, perguntas orientadoras e sínteses parciais para apoiar a participação e a construção das respostas.",
        "Oferecer acompanhamento individual, retomadas coletivas e flexibilização das formas de registro conforme as necessidades da turma.",
    ],
}

_ACESSIBILIDADE_FINANCEIRA_POR_TIPO = {
    "orcamento_planejamento": [
        "Organizar receitas, despesas, metas e saldo em tabela simples ou esquema no quadro, com exemplos graduados antes da atividade individual.",
        "Oferecer roteiro com etapas do planejamento financeiro: identificar recursos, listar gastos, definir prioridades e revisar escolhas.",
        "Apoiar individualmente estudantes com dificuldade em leitura de dados, cálculos ou organização das respostas.",
    ],
    "consumo_consciente": [
        "Apresentar critérios visuais para comparar alternativas de consumo, como necessidade, desejo, preço, durabilidade e consequência da escolha.",
        "Utilizar exemplos neutros e cotidianos, evitando exposição ou julgamento dos hábitos financeiros pessoais e familiares.",
        "Permitir registros por tópicos, esquemas ou explicação oral para apoiar a justificativa das decisões.",
    ],
    "investimento_poupanca": [
        "Representar metas, prazos e valores acumulados em quadro, tabela ou linha do tempo para facilitar a compreensão.",
        "Retomar o vocabulário financeiro essencial, como poupança, reserva, rendimento, meta e imprevisto, antes dos cálculos.",
        "Oferecer exemplos passo a passo e mediação individual durante a interpretação dos cenários.",
    ],
    "credito_endividamento": [
        "Disponibilizar resolução comentada para comparação entre valor à vista, parcelas, juros e custo total.",
        "Destacar no quadro os dados do problema e as perguntas que orientam a decisão responsável sobre crédito.",
        "Permitir calculadora, tabelas de apoio ou registro por etapas para estudantes com dificuldade nos cálculos.",
    ],
    "empreendedorismo": [
        "Organizar o projeto em etapas curtas: ideia, público, recursos, custos, preço, viabilidade e revisão.",
        "Utilizar quadro ou ficha de planejamento para apoiar a organização das decisões do grupo.",
        "Permitir diferentes formas de participação, como fala, desenho, tópicos, cálculo com apoio ou registro em dupla.",
    ],
    "cidadania_financeira": [
        "Utilizar exemplos de comprovantes, garantias, direitos e cuidados de segurança com linguagem acessível.",
        "Registrar no quadro palavras-chave e procedimentos de proteção para orientar a análise das situações.",
        "Realizar leitura mediada dos enunciados e apoiar estudantes com dificuldade na interpretação dos direitos e responsabilidades.",
    ],
    "instituicoes_financeiras": [
        "Explicar funções de instituições financeiras com exemplos concretos e vocabulário acessível, como banco, conta, cartão e segurança.",
        "Organizar comparações em lista ou quadro para diferenciar formas de guardar, movimentar e proteger o dinheiro.",
        "Oferecer apoio individual durante a leitura e a organização das respostas sobre serviços financeiros.",
    ],
}


class GeradorAcessibilidade:
    """Gera estratégias de acessibilidade contextualizadas por tipo de recurso."""

    def gerar(
        self,
        perfil: str,
        tipo: str,
        tema: str,
        recursos_detectados: list[str] | None = None,
        indice_aula: int = 0,
        aprendizagem: str = "",
        desenvolvimento: str = "",
        disciplina: str = "",
    ) -> list[str]:
        """
        Gera 3 itens de acessibilidade contextualizados.

        Se recursos_detectados estiver disponível, seleciona estratégias
        específicas do catálogo. Caso contrário, usa fallback por perfil.
        """
        # Se não detectou recursos, tenta detectar pelo texto
        if not recursos_detectados and desenvolvimento:
            recursos_detectados = detectar_recursos(desenvolvimento, tema)

        if perfil == "educacao_financeira" and tipo in _ACESSIBILIDADE_FINANCEIRA_POR_TIPO:
            return list(_ACESSIBILIDADE_FINANCEIRA_POR_TIPO[tipo])

        # Estratégia: selecionar dos catálogos por recurso
        if recursos_detectados:
            itens = self._selecionar_por_recursos(recursos_detectados, indice_aula, tema)
            if len(itens) >= 3:
                return itens[:3]

        # Fallback: usar catálogo por perfil
        fallback = _FALLBACK_POR_PERFIL.get(perfil, [])
        if fallback:
            return list(fallback)

        # Fallback final genérico
        base_texto = normalizar_texto(f"{tema} {aprendizagem} {desenvolvimento}")
        if contem_termos(base_texto, ["imagem", "grafico", "mapa", "tabela", "esquema", "anuncio"]):
            primeiro = "Utilizar recursos visuais, exemplos concretos e mediação oral para favorecer a compreensão do conteúdo e das atividades propostas."
        else:
            primeiro = "Apresentar o conteúdo com linguagem clara, exemplos comentados e retomadas frequentes dos pontos essenciais."

        if contem_termos(base_texto, ["leitura", "texto", "fonte", "noticia", "conto", "documento"]):
            segundo = "Realizar leitura guiada com pausas para explicar vocabulário, informações centrais e comandos necessários à participação na aula."
        else:
            segundo = "Explicar as atividades passo a passo, com apoio visual e perguntas orientadoras para apoiar diferentes ritmos de aprendizagem."

        return [
            primeiro,
            segundo,
            "Oferecer mediação individual, tempo ampliado quando necessário e diferentes formas de registro para apoiar a participação de todos os estudantes.",
        ]

    def _selecionar_por_recursos(
        self, recursos: list[str], indice_aula: int, tema: str
    ) -> list[str]:
        """Seleciona estratégias do catálogo baseado nos recursos detectados."""
        itens_selecionados = []
        recursos_usados = set()

        for recurso in recursos:
            if recurso in recursos_usados:
                continue
            estrategias = CATALOGO_ESTRATEGIAS.get(recurso, [])
            if not estrategias:
                continue

            # Seleciona uma estratégia com variação pelo índice da aula
            idx = _indice_hash([recurso, tema, str(indice_aula)], len(estrategias))
            itens_selecionados.append(estrategias[idx])
            recursos_usados.add(recurso)

            if len(itens_selecionados) >= 3:
                break

        # Se não completou 3, adiciona estratégia genérica de mediação
        while len(itens_selecionados) < 3:
            genericas = [
                "Oferecer mediação individual durante as atividades, adequando explicações, tempo e forma de resposta conforme as necessidades da turma.",
                "Utilizar apoio visual, retomadas coletivas e registros orientados para favorecer a compreensão dos conceitos trabalhados.",
                "Organizar intervenções com exemplos comentados e acompanhamento próximo para apoiar estudantes com dificuldades de leitura, interpretação ou organização das tarefas.",
            ]
            idx_gen = len(itens_selecionados) % len(genericas)
            itens_selecionados.append(genericas[idx_gen])

        return itens_selecionados


# ── Instância global e função de conveniência ──────────────────────────────

_gerador = GeradorAcessibilidade()


def gerar_acessibilidade_aprimorada(
    tema: str,
    aprendizagem: str = "",
    desenvolvimento: str = "",
    disciplina: str = "",
    perfil: str = "",
    tipo: str = "",
    recursos_detectados: list[str] | None = None,
    indice_aula: int = 0,
) -> list[str]:
    """
    Gera acessibilidade aprimorada.
    Compatível com a assinatura de gerar_acessibilidade_dinamica() do avaliacao.py,
    mas com seleção por tipo de recurso e variação sequencial.
    """
    from core.lib.classificador import perfil_disciplina, detectar_tipo_aula

    if not perfil:
        perfil = perfil_disciplina(disciplina)
    if not tipo:
        tipo = detectar_tipo_aula(desenvolvimento, tema, disciplina)

    return _gerador.gerar(
        perfil=perfil,
        tipo=tipo,
        tema=tema,
        recursos_detectados=recursos_detectados,
        indice_aula=indice_aula,
        aprendizagem=aprendizagem,
        desenvolvimento=desenvolvimento,
        disciplina=disciplina,
    )
