"""
Motor unificado de geração de metodologia (sem IA).

Substitui a geração fraca do inteligencia_local.py (5 etapas fixas)
pelo motor sofisticado que já existia no lote.py (etapas variáveis por perfil),
integrando as novas bibliotecas de técnicas e progressão.
"""

from core.lib.classificador import perfil_disciplina, detectar_tipo_aula, normalizar_texto, contem_termos
from core.lib.tecnicas import SeletorTecnicas
from core.lib.progressao import ajustar_texto_por_posicao
from core.lib.extrator_pdf import ExtratorPDF


_seletor_tecnicas = SeletorTecnicas()
_extrator = ExtratorPDF()


class ValidadorQualidade:
    """Remove etapas vazias e formata corretamente os blocos de texto."""

    def refinar(self, metodologia: list[dict]) -> list[dict]:
        validada = []
        for etapa in metodologia:
            if etapa.get("texto") and len(etapa["texto"].strip()) > 10:
                texto = etapa["texto"].strip()
                if not texto.endswith('.'):
                    texto += '.'
                etapa["texto"] = texto
                validada.append(etapa)
        return validada


def _etapas_por_perfil(perfil: str, tipo: str) -> list[tuple[str, str]]:
    """Define as etapas metodológicas adequadas ao perfil e tipo de aula."""

    if perfil == "matematica":
        if tipo == "verificacao":
            return [
                ("Relembre", "para_comecar"),
                ("Na prática", "pratica"),
                ("Encerramento", "encerramento"),
            ]
        return [
            ("Para começar", "para_comecar"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
            ("Na prática", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil == "lingua_portuguesa_em":
        return [
            ("Para começar", "para_comecar"),
            ("Contextualização", "contextualizacao"),
            ("Leitura analítica", "leitura_analitica"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
            ("Na prática", "pratica"),
            ("Encerramento", "encerramento"),
        ]

    if perfil in {"leitura_redacao"} and tipo == "producao":
        return [
            ("Para começar", "para_comecar"),
            ("Leitura e construção do conteúdo", "leitura"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
            ("Na prática", "pratica"),
            ("Revisão e reescrita", "encerramento"),
        ]

    if perfil == "educacao_financeira":
        etapas = [
            ("Para começar", "para_comecar"),
            ("Análise de caso", "analise_caso"),
            ("Foco no conteúdo", "foco"),
            ("Pause e responda", "pause"),
        ]
        if tipo in {"credito_endividamento", "investimento_poupanca"}:
            etapas.append(("Cálculos financeiros", "calculos"))
            etapas.append(("Na prática", "pratica"))
        elif tipo == "orcamento_planejamento":
            etapas.append(("Planejamento orçamentário", "planejamento"))
        elif tipo == "empreendedorismo":
            etapas.append(("Projeto empreendedor", "projeto"))
        else:
            etapas.append(("Na prática", "pratica"))
        etapas.append(("Encerramento", "encerramento"))
        return etapas

    # Padrão geral
    return [
        ("Para começar", "para_comecar"),
        ("Leitura e construção do conteúdo", "leitura"),
        ("Foco no conteúdo", "foco"),
        ("Pause e responda", "pause"),
        ("Na prática", "pratica"),
        ("Encerramento", "encerramento"),
    ]


def _frases_por_contexto(
    perfil: str, tipo: str, tema: str, conceito: str,
    turma: str, tecnicas: dict, texto_base: str = ""
) -> dict[str, str]:
    """Gera frases contextualizadas para cada etapa da metodologia."""

    t_disc = tecnicas.get("abertura", "Virem e conversem")
    t_reg = tecnicas.get("registro", "Todo mundo escreve")
    t_sint = tecnicas.get("sintese", "Com suas palavras")
    t_verif = tecnicas.get("verificacao", "Pause e responda")

    base = {
        "para_comecar": (
            f"Retomar conhecimentos prévios da turma sobre {tema}. Propor {t_disc} "
            "para levantar hipóteses, exemplos e dúvidas iniciais."
        ),
        "leitura": (
            "Realizar leitura guiada dos textos, imagens, comandos e/ou exemplos do material, fazendo pausas "
            "para destacar informações relevantes. Organizar no quadro as ideias principais e as palavras-chave "
            "que orientam a atividade."
        ),
        "contextualizacao": (
            f"Contextualizar {tema} a partir de situações do cotidiano, repertórios culturais ou exemplos do "
            "material, ajudando a turma a compreender por que esse conteúdo é relevante e como ele circula "
            "socialmente."
        ),
        "leitura_analitica": (
            "Conduzir leitura analítica do texto, imagem, dado ou situação apresentada, destacando escolhas de "
            "linguagem, organização das ideias, pistas visuais e informações que sustentam a compreensão."
        ),
        "foco": (
            f"Analisar {conceito}, relacionando o conteúdo ao objetivo da aula. Explicar os pontos centrais de "
            "forma dialogada e verificar se a turma compreende as relações entre conceito, exemplo e atividade."
        ),
        "pratica": (
            f"Orientar a resolução das atividades propostas, usando {t_reg} para garantir registro "
            "individual. Circular pela sala, mediar dúvidas e solicitar justificativas para as respostas."
        ),
        "pause": (
            f"Socializar algumas respostas e realizar correção dialogada com {t_verif}, retomando trechos do "
            "material, registros dos estudantes e dúvidas comuns antes de avançar."
        ),
        "encerramento": (
            f"Finalizar com {t_sint}, retomando os aprendizados sobre {tema} e registrando uma síntese "
            "curta no quadro ou no caderno."
        ),
    }

    # Ajustes por perfil
    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        if tipo == "producao":
            base["leitura"] = (
                "Apresentar a proposta de produção e realizar leitura guiada dos comandos, destacando finalidade, "
                "interlocutor, gênero textual e critérios de qualidade. Organizar no quadro um roteiro de planejamento."
            )
            base["foco"] = (
                f"Analisar as características do gênero relacionado a {tema}, observando estrutura, linguagem, "
                "organização das ideias e marcas que orientam a escrita."
            )
            base["pratica"] = (
                f"Orientar o planejamento, a escrita do rascunho e a revisão, solicitando {t_reg}. Solicitar que os estudantes confiram "
                "se o texto atende à finalidade, ao público e aos critérios combinados."
            )
        elif tipo == "argumentacao":
            base["foco"] = (
                f"Analisar tese, opinião, argumentos e estratégias persuasivas presentes em {conceito}. Destacar "
                "como escolhas de linguagem e exemplos ajudam a sustentar o ponto de vista."
            )
        else:
            base["foco"] = (
                f"Analisar {conceito}, destacando gênero, finalidade, público-alvo, recursos de linguagem e pistas "
                "textuais ou visuais que ajudam na compreensão."
            )

    elif perfil in {"orientacao_estudos"}:
        base["foco"] = (
            f"Trabalhar {conceito} como oportunidade para ensinar uma estratégia de estudo: localizar informações, "
            "interpretar comandos, justificar respostas e revisar registros."
        )
        base["pratica"] = (
            f"Orientar a resolução das atividades explicitando o passo a passo de estudo, usando {t_reg}: ler o comando, marcar "
            "palavras-chave, buscar evidências, responder e revisar a resposta."
        )
        base["encerramento"] = (
            f"Finalizar com autoavaliação breve sobre qual estratégia ajudou mais a compreender {tema} e como ela "
            "pode ser usada em outras disciplinas."
        )

    elif perfil in {"ciencias_ef", "biologia", "quimica", "fisica"}:
        base["para_comecar"] = (
            f"Contextualizar {tema} com uma situação-problema, imagem, dado ou exemplo do cotidiano. Propor "
            f"{t_disc} para que os estudantes antecipem explicações e levantem evidências."
        )
        base["foco"] = (
            f"Explicar {conceito} de forma progressiva, relacionando fenômeno, causa, consequência e exemplos. "
            "Usar esquemas no quadro para diferenciar observação, hipótese e conceito científico."
        )
        base["pratica"] = (
            f"Orientar leitura de texto, imagem, modelo ou atividade investigativa, solicitando {t_reg}. "
            "Retomar as evidências usadas pelos estudantes para justificar as respostas."
        )

    elif perfil == "historia":
        base["foco"] = (
            f"Apresentar o contexto histórico de {conceito}, situando sujeitos, tempo, espaço e conflitos envolvidos. "
            "Relacionar as ideias iniciais da turma com os conceitos históricos em estudo."
        )
        base["pratica"] = (
            f"Orientar a análise de fontes, imagens, mapas, linhas do tempo ou textos do material, usando {t_reg}. Solicitar registro "
            "das evidências encontradas e mediação para diferenciar fato, interpretação e contexto."
        )

    elif perfil == "geografia":
        base["foco"] = (
            f"Analisar {conceito} considerando paisagem, território, escala, localização e relações entre sociedade "
            "e natureza. Usar mapa, imagem, tabela ou gráfico como apoio para a explicação."
        )
        base["pratica"] = (
            f"Orientar leitura de mapas, imagens, gráficos ou situações-problema, solicitando {t_reg} para que os estudantes "
            "identifiquem elementos espaciais e expliquem relações de causa e consequência."
        )

    elif perfil == "ingles":
        base["para_comecar"] = (
            f"Retomar vocabulário conhecido relacionado a {tema} com repetição oral breve e exemplos no quadro. "
            "Estimular que os estudantes tentem pronunciar e reconhecer palavras antes da sistematização."
        )
        base["leitura"] = (
            "Apresentar o texto, diálogo, imagem ou situação comunicativa, alternando leitura em voz alta, escuta "
            "e repetição. Destacar vocabulário-chave e estruturas em inglês com apoio em exemplos."
        )
        base["foco"] = (
            f"Explorar o uso comunicativo de {conceito}, mostrando quando e como empregar as expressões estudadas. "
            "Registrar no quadro exemplos curtos em inglês e seus sentidos em contexto."
        )
        base["pratica"] = (
            f"Organizar prática oral e escrita em pares, com {t_reg} (repetição, preenchimento, pequenas respostas ou diálogos). "
            "Acompanhar pronúncia, compreensão e uso funcional das expressões."
        )

    elif perfil == "arte":
        base["foco"] = (
            f"Apresentar referências artísticas relacionadas a {conceito}, orientando apreciação de elementos visuais, "
            "sonoros, corporais ou culturais. Valorizar percepções diferentes sem reduzir a aula a explicação teórica."
        )
        base["pratica"] = (
            f"Propor experimentação, criação ou apreciação orientada, com {t_reg} no diário de bordo. Acompanhar "
            "processos criativos, escolhas dos estudantes e socialização das produções ou percepções."
        )

    elif perfil in {"projeto_de_vida", "lideranca_oratoria"}:
        base["para_comecar"] = (
            f"Abrir a aula com uma situação acolhedora relacionada a {tema}, sem exigir exposição pessoal. Propor "
            "troca em duplas ou roda de conversa breve, respeitando diferentes ritmos de participação."
        )
        base["foco"] = (
            f"Construir o conceito de {conceito} por meio de exemplos escolares e cotidianos, ajudando a turma a "
            "relacionar sentir, pensar e agir de forma respeitosa."
        )
        base["pratica"] = (
            "Orientar atividade reflexiva com registro individual, escolha pessoal ou planejamento simples. Garantir "
            "que a socialização seja opcional ou mediada, evitando exposição de experiências íntimas."
        )
        base["encerramento"] = (
            f"Encerrar com um compromisso simples ou observação para a semana, relacionado a {tema}, reforçando "
            "autonomia, respeito e cuidado nas relações."
        )

    elif perfil == "educacao_financeira":
        conceito_seguro = tema if normalizar_texto(conceito) in {"educacao financeira", "financeira"} else conceito
        situacoes = {
            "orcamento_planejamento": "uma situação de organização de renda, gastos e prioridades para cumprir uma meta simples",
            "consumo_consciente": "um dilema de consumo em que a turma precise comparar necessidade, desejo, preço, durabilidade e impacto da escolha",
            "investimento_poupanca": "uma situação de poupança ou reserva de emergência em que pequenos valores acumulados ajudam a lidar com imprevistos",
            "credito_endividamento": "uma compra parcelada ou oferta de crédito em que seja necessário comparar valor à vista, juros, parcelas e custo total",
            "empreendedorismo": "um pequeno projeto de venda, serviço ou solução para a comunidade escolar, analisando custos, preço e viabilidade",
            "cidadania_financeira": "uma situação de consumo que envolva direitos, responsabilidades, comprovantes, garantia ou uso seguro de serviços financeiros",
            "instituicoes_financeiras": "uma situação cotidiana sobre onde guardar, movimentar e proteger o dinheiro com segurança",
        }
        situacao = situacoes.get(tipo, f"uma situação financeira real relacionada a {tema}")
        base["para_comecar"] = (
            f"Apresentar {situacao}, sem exigir relatos pessoais nem julgamentos sobre hábitos financeiros familiares. "
            "Convidar os estudantes a levantar hipóteses sobre escolhas, riscos, prioridades e consequências antes da sistematização."
        )
        base["analise_caso"] = (
            f"Conduzir a análise do caso ligado a {tema}, identificando dados importantes, alternativas possíveis, "
            "critérios de decisão e consequências de curto e longo prazo. Registrar no quadro as perguntas que ajudam a decidir com responsabilidade."
        )
        base["foco"] = (
            f"Desenvolver {conceito_seguro} de forma contextualizada, relacionando o conceito a situações reais de consumo, "
            "planejamento, poupança, crédito ou organização de recursos. Explicar o vocabulário financeiro necessário e construir critérios claros para a tomada de decisão."
        )
        base["pause"] = (
            "Promover uma pausa para que a turma compare alternativas, justifique escolhas e avalie impactos financeiros, "
            "retomando dados do material e dúvidas comuns antes de seguir para a aplicação."
        )
        base["calculos"] = (
            "Orientar cálculos financeiros de forma guiada, destacando dados, operações, porcentagens, juros, parcelas, saldo ou custo total conforme o material. "
            "Relacionar cada resultado numérico a uma decisão possível, evitando que a atividade fique apenas mecânica."
        )
        base["planejamento"] = (
            "Orientar a elaboração ou análise de um planejamento financeiro simulado, organizando receita, despesas, prioridades, metas e saldo. "
            "Acompanhar os registros para que os estudantes expliquem os critérios usados nas escolhas."
        )
        base["simulacao"] = (
            "Organizar uma simulação financeira ou análise de alternativas, aplicando os critérios construídos na aula para escolher, comparar, planejar ou revisar uma decisão. "
            "Solicitar registro de cálculos, justificativas e possíveis consequências."
        )
        base["projeto"] = (
            "Orientar a organização de um projeto empreendedor simples, levantando recursos necessários, custos, preço, público, viabilidade e cuidados éticos. "
            "Solicitar que os estudantes justifiquem as decisões tomadas no planejamento."
        )
        base["pratica"] = (
            "Orientar a resolução das atividades do material com registro individual ou em dupla, acompanhando leitura de dados, comparação de alternativas e justificativa das decisões. "
            "Retomar vocabulário financeiro e critérios de escolha sempre que surgirem dúvidas."
        )

        if tipo == "orcamento_planejamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} como estratégia de organização financeira, relacionando receitas, despesas, gastos, prioridades e metas. "
                "Construir com a turma critérios para controlar recursos e ajustar escolhas conforme limites e objetivos."
            )
            base["pratica"] = base["planejamento"]
        elif tipo == "consumo_consciente":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} a partir de critérios de consumo consciente, diferenciando necessidade, desejo, prioridade, custo-benefício e impacto da escolha. "
                "Evitar tom moralista e conduzir a análise com base em argumentos, dados e consequências."
            )
        elif tipo == "investimento_poupanca":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando poupança, reserva, rendimento, constância e planejamento de metas. "
                "Mostrar como a organização dos recursos ajuda a lidar com imprevistos e objetivos de curto ou longo prazo."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "credito_endividamento":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} com foco no uso responsável do crédito, analisando juros, parcelas, custo total, riscos de endividamento e critérios para decidir. "
                "Comparar alternativas sem estimular consumo, priorizando avaliação crítica e planejamento."
            )
            base["pratica"] = base["simulacao"]
        elif tipo == "empreendedorismo":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} articulando oportunidade, necessidade, produto ou serviço, custos, preço, lucro e viabilidade. "
                "Relacionar a proposta a planejamento, responsabilidade e análise do contexto."
            )
            base["pratica"] = base["projeto"]
        elif tipo == "cidadania_financeira":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} relacionando direitos do consumidor, responsabilidades, segurança, comprovantes, garantias e autonomia nas decisões financeiras. "
                "Orientar a turma a identificar formas de proteção e uso consciente de serviços financeiros."
            )
        elif tipo == "instituicoes_financeiras":
            base["foco"] = (
                f"Desenvolver {conceito_seguro} explicando a função das instituições financeiras na guarda, movimentação, controle e proteção do dinheiro. "
                "Comparar exemplos como banco, conta digital, poupança e outros serviços, destacando segurança e planejamento."
            )

        base["encerramento"] = (
            f"Sintetizar os aprendizados financeiros relacionados a {tema}, retomando critérios de decisão, organização e responsabilidade. "
            "Propor um fechamento com planejamento de aplicação no cotidiano, sem solicitar exposição de informações financeiras pessoais."
        )

    elif perfil == "matematica":
        base["para_comecar"] = (
            f"Apresentar situação-problema envolvendo {tema} e propor {t_disc} para que os estudantes mobilizem "
            "conhecimentos prévios, levantem hipóteses e identifiquem o que precisa ser descoberto na situação."
        )
        base["foco"] = (
            f"Explorar {conceito} com exemplos guiados, destacando dados, relações, procedimentos e critérios para "
            "verificar se o resultado encontrado faz sentido na situação estudada."
        )
        base["pratica"] = (
            f"Orientar {t_reg} com problemas e registros relacionados a {tema}, acompanhando a interpretação "
            "dos enunciados, a organização dos cálculos e a validação das soluções construídas pela turma."
        )
        base["encerramento"] = (
            f"Encerrar com {t_sint}, sistematizando as estratégias construídas pela turma para compreender e "
            f"resolver situações relacionadas a {tema} e registrar uma síntese coletiva do que foi aprendido na aula."
        )

    elif perfil == "tecnologia_inovacao":
        base["para_comecar"] = (
            f"Apresentar um problema real relacionado a {tema}, incentivando observação do contexto e levantamento "
            "de necessidades antes da construção de soluções."
        )
        base["pratica"] = (
            f"Orientar criação, programação, prototipagem ou teste de solução, exigindo {t_reg}, e acompanhando escolhas técnicas, "
            "iterações e registros do processo."
        )

    elif perfil == "sociologia":
        base["para_comecar"] = (
            f"Apresentar um fenômeno social ligado a {tema} por meio de situação, imagem, dado ou relato, "
            "provocando estranhamento e questionamentos iniciais."
        )
        base["foco"] = (
            f"Analisar {conceito} sociologicamente, articulando teoria, conceitos e exemplos da realidade social "
            "para superar leituras baseadas apenas no senso comum."
        )

    return base


class MotorMetodologico:
    """Motor unificado de geração de metodologia sem IA."""

    def __init__(self):
        self.extrator = _extrator
        self.validador = ValidadorQualidade()
        self.seletor = _seletor_tecnicas

    def gerar(
        self,
        texto_pdf: str,
        disciplina: str,
        turma: str,
        tema: str,
        indice_aula: int = 0,
        total_aulas: int = 1,
    ) -> list[dict]:
        """
        Gera metodologia completa com etapas variáveis por perfil.

        Usa o motor sofisticado (equivalente ao _montar_etapas_metodologia
        do lote.py) em vez do motor fraco do inteligencia_local.py.
        """
        # 1. Classificar
        perfil = perfil_disciplina(disciplina)
        tipo = detectar_tipo_aula(texto_pdf, tema, disciplina)

        # 2. Extrair conceito
        extracao = self.extrator.extrair(texto_pdf, tema)
        conceito = extracao["conceito_extraido"]

        # 3. Selecionar técnicas com variação
        tecnicas = self.seletor.selecionar_para_aula(perfil, tipo, tema, indice_aula)

        # 4. Gerar frases contextualizadas
        frases = _frases_por_contexto(perfil, tipo, tema, conceito, turma, tecnicas, texto_pdf)

        # 5. Montar etapas
        etapas_config = _etapas_por_perfil(perfil, tipo)
        metodologia = []
        for titulo, chave in etapas_config:
            texto_etapa = frases.get(chave, "").strip()
            if texto_etapa:
                # Aplicar progressão entre aulas
                texto_etapa = ajustar_texto_por_posicao(
                    texto_etapa, indice_aula, total_aulas, tema
                )
                metodologia.append({"titulo": titulo, "texto": texto_etapa})

        # 6. Validar
        return self.validador.refinar(metodologia)

    def extrair_dados(self, texto_pdf: str, tema: str) -> dict:
        """Expõe a extração de dados para uso por outros módulos."""
        return self.extrator.extrair(texto_pdf, tema)
