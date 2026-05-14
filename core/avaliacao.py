import re
import unicodedata


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", texto).strip().lower()


def _base_textual(*partes: str) -> str:
    return _normalizar(" ".join(parte or "" for parte in partes))


def _contem(base: str, termos: list[str]) -> bool:
    return any(termo in base for termo in termos)


def _perfil_resolvido(perfil: str, disciplina: str) -> str:
    if perfil:
        return perfil

    disciplina_norm = _normalizar(disciplina)
    mapa = {
        "orientacao_estudos": ["orientacao de estudos", "orienestudos"],
        "leitura_redacao": ["leitura e redacao", "redacao", "leitura"],
        "lingua_portuguesa_em": ["lingua portuguesa"],
        "ciencias_ef": ["ciencias"],
        "biologia": ["biologia"],
        "quimica": ["quimica"],
        "fisica": ["fisica"],
        "historia": ["historia"],
        "geografia": ["geografia"],
        "ingles": ["ingles", "lingua inglesa"],
        "arte": ["arte"],
        "projeto_de_vida": ["projeto de vida"],
        "educacao_financeira": ["educacao financeira"],
        "matematica": ["matematica"],
        "tecnologia_inovacao": ["tecnologia", "inovacao"],
        "sociologia": ["sociologia"],
        "lideranca_oratoria": ["lideranca", "oratoria"],
    }
    for nome, termos in mapa.items():
        if _contem(disciplina_norm, termos):
            return nome
    return "geral"


def gerar_acompanhamento_dinamico(
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
    disciplina: str = "",
    perfil: str = "",
    tipo: str = "",
) -> list[str]:
    base = _base_textual(tema, aprendizagem, desenvolvimento, disciplina, tipo)
    perfil = _perfil_resolvido(perfil, disciplina)

    if perfil == "matematica":
        if tipo == "verificacao":
            return [
                "Observar se os estudantes retomam procedimentos, propriedades e relacoes matematicas ja trabalhadas, corrigindo estrategias quando necessario.",
                "Verificar se os estudantes justificam os caminhos escolhidos, comparam resultados e identificam onde precisam rever o raciocinio.",
                "Acompanhar se os registros mostram autonomia progressiva na resolucao, conferencia e validacao das respostas.",
            ]
        if tipo in {"modelagem", "funcoes", "algebra", "geometria", "estatistica_probabilidade", "combinatoria"}:
            return [
                f"Verificar se os estudantes identificam os elementos matematicos centrais de {tema} e representam as relacoes envolvidas de modo coerente.",
                "Observar se os estudantes utilizam estrategias, registros, calculos e justificativas compativeis com a situacao-problema proposta.",
                "Acompanhar se os estudantes interpretam os resultados, comparam caminhos de resolucao e validam as conclusoes construidas ao longo da aula.",
            ]
        return [
            f"Observar se os estudantes mobilizam conhecimentos previos e constroem estrategias adequadas para resolver as situacoes relacionadas a {tema}.",
            "Verificar se os estudantes explicitam procedimentos, organizam os registros e conseguem explicar como chegaram as respostas.",
            "Acompanhar se os estudantes revisam, testam e validam os resultados com progressiva autonomia durante as etapas da aula.",
        ]

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        if _contem(base, ["revisao", "reescrita", "rascunho", "producao textual", "planejamento do texto"]):
            return [
                "Observar como os estudantes planejam, revisam e ajustam a producao textual, considerando genero, finalidade comunicativa e organizacao das ideias.",
                "Verificar se os estudantes incorporam as orientacoes discutidas na aula para qualificar clareza, coerencia e adequacao linguistica.",
                "Acompanhar os registros produzidos, considerando avancos entre rascunho, revisao e versao final, bem como a autonomia no uso dos criterios trabalhados.",
            ]
        if tipo == "argumentacao" or _contem(base, ["debate", "tese", "argumento", "opinia", "ponto de vista"]):
            return [
                "Observar a participacao dos estudantes nas discussoes, considerando a escuta, a formulacao de posicionamentos e o uso de argumentos consistentes.",
                "Verificar se os estudantes identificam tese, argumentos e recursos persuasivos nos textos e interacoes analisados.",
                "Acompanhar se os registros e respostas evidenciam clareza de posicionamento, justificativa e respeito as diferentes perspectivas.",
            ]
        return [
            f"Observar se os estudantes compreendem as ideias centrais de {tema} e reconhecem os elementos textuais ou linguisticos em foco.",
            "Verificar a participacao nas leituras, analises, discussoes e registros, considerando interpretacao, argumentacao e ampliacao de repertorio.",
            "Acompanhar se os estudantes aplicam as estrategias de leitura, analise da linguagem ou producao de sentidos com autonomia crescente.",
        ]

    if perfil == "orientacao_estudos":
        return [
            "Observar se os estudantes utilizam as estrategias de organizacao, leitura, retomada e planejamento propostas durante a aula.",
            "Verificar se os estudantes conseguem identificar dificuldades, selecionar procedimentos de estudo e explicar como podem aplica-los em outras situacoes.",
            "Acompanhar os registros produzidos, considerando autonomia, constancia e capacidade de monitorar o proprio processo de aprendizagem.",
        ]

    if perfil in {"ciencias_ef", "biologia", "quimica", "fisica"}:
        if perfil == "biologia" and _contem(base, ["ecossistema", "biodiversidade", "cadeia alimentar", "teia alimentar", "clima"]):
            return [
                "Observar se os estudantes relacionam fenomenos biologicos e ambientais, utilizando conceitos cientificos para explicar causas, efeitos e interdependencias.",
                "Verificar se os estudantes interpretam dados, imagens, esquemas ou situacoes-problema com base nas evidencias discutidas na aula.",
                "Acompanhar se os registros mostram uso progressivo do vocabulario cientifico e capacidade de justificar posicoes e solucoes.",
            ]
        if perfil == "quimica" or _contem(base, ["reacao quimica", "mistura", "solucao", "lavoisier", "proust", "transformacao quimica"]):
            return [
                "Observar se os estudantes identificam evidencias, transformacoes e relacoes entre substancias, materiais ou processos quimicos em estudo.",
                "Verificar se os estudantes organizam informacoes, analisam representacoes e explicam resultados utilizando conceitos e linguagem adequados.",
                "Acompanhar se os estudantes conseguem aplicar os conhecimentos trabalhados para interpretar fenomenos, comparar situacoes e justificar conclusoes.",
            ]
        if perfil == "fisica" or _contem(base, ["ondas", "forca", "movimento", "energia", "circuito", "amplitude", "frequencia"]):
            return [
                "Observar se os estudantes identificam grandezas, variaveis e relacoes fisicas envolvidas nas situacoes analisadas na aula.",
                "Verificar se os estudantes interpretam esquemas, graficos, experimentos ou problemas, articulando conceitos e evidencias.",
                "Acompanhar se os estudantes explicam procedimentos, analisam resultados e utilizam os conceitos fisicos para justificar suas respostas.",
            ]
        return [
            f"Observar se os estudantes relacionam {tema} aos conceitos cientificos trabalhados e utilizam evidencias para sustentar suas respostas.",
            "Verificar a participacao nas investigacoes, discussoes, registros e socializacoes, considerando clareza de hipoteses e explicacoes.",
            "Acompanhar se os estudantes interpretam fenomenos, dados, experimentos ou representacoes com base nos conceitos desenvolvidos na aula.",
        ]

    if perfil == "historia":
        return [
            "Observar se os estudantes identificam sujeitos, contextos, permanencias, mudancas e relacoes temporais nas fontes e situacoes estudadas.",
            "Verificar se os estudantes utilizam evidencias historicas para interpretar acontecimentos, comparar perspectivas e sustentar explicacoes.",
            "Acompanhar os registros e respostas, considerando vocabulario historico, organizacao das ideias e progressiva autonomia de analise.",
        ]

    if perfil == "geografia":
        return [
            "Observar se os estudantes interpretam paisagens, mapas, graficos, tabelas e outras linguagens geograficas com atencao aos conceitos em foco.",
            "Verificar se os estudantes relacionam territorio, sociedade, natureza e escalas de analise nas situacoes discutidas ao longo da aula.",
            "Acompanhar os registros produzidos, considerando clareza na leitura de dados, argumentacao e aplicacao dos conceitos trabalhados.",
        ]

    if perfil == "ingles":
        return [
            "Observar se os estudantes compreendem vocabulario, estruturas e comandos em lingua inglesa nas atividades propostas.",
            "Verificar se os estudantes participam das praticas de leitura, escuta, oralidade e escrita com apoio progressivamente mais autonomo.",
            "Acompanhar se os registros e interacoes evidenciam uso contextualizado da lingua, ampliacao de repertorio e compreensao do tema estudado.",
        ]

    if perfil == "arte":
        return [
            "Observar se os estudantes participam das praticas de apreciacao, experimentacao, criacao e analise propostas durante a aula.",
            "Verificar se os estudantes reconhecem elementos, linguagens, procedimentos e intencionalidades presentes nas producoes artisticas estudadas.",
            "Acompanhar se os registros e producoes revelam ampliacao de repertorio, argumentacao sensivel e uso de referencias discutidas coletivamente.",
        ]

    if perfil in {"projeto_de_vida", "lideranca_oratoria"}:
        return [
            "Observar a participacao dos estudantes nas reflexoes e interacoes propostas, considerando escuta, respeito, cooperacao e elaboracao de ideias.",
            "Verificar se os estudantes relacionam o tema da aula a escolhas, atitudes, estrategias de convivencia e planejamento pessoal ou coletivo.",
            "Acompanhar os registros produzidos, valorizando argumentacao, consciencia critica e apropriacao dos conceitos sem exigir exposicao excessiva.",
        ]

    if perfil == "educacao_financeira":
        return [
            "Observar se os estudantes analisam situacoes de consumo, orcamento, planejamento e tomada de decisao com base em criterios claros.",
            "Verificar se os estudantes interpretam calculos, dados e cenarios financeiros, justificando escolhas e prioridades com coerencia.",
            "Acompanhar se os registros mostram compreensao progressiva das relacoes entre objetivos, recursos, limites e consequencias das decisoes.",
        ]

    if perfil in {"tecnologia_inovacao", "sociologia"}:
        return [
            f"Observar se os estudantes compreendem os conceitos centrais relacionados a {tema} e participam das atividades de analise, discussao e registro.",
            "Verificar se os estudantes articulam o tema estudado a situacoes do cotidiano, contextos sociais ou usos praticos do conhecimento.",
            "Acompanhar os registros produzidos, considerando clareza de ideias, argumentacao e autonomia crescente nas respostas.",
        ]

    return [
        f"Observar se os estudantes compreendem os conceitos centrais relacionados a {tema} durante as discussoes e atividades propostas.",
        "Verificar a participacao, os registros produzidos e a forma como os estudantes justificam suas respostas ao longo da aula.",
        "Acompanhar se os estudantes conseguem aplicar os conhecimentos trabalhados com autonomia progressiva nas atividades orientadas.",
    ]


def gerar_acessibilidade_dinamica(
    tema: str,
    aprendizagem: str,
    desenvolvimento: str,
    disciplina: str = "",
    perfil: str = "",
    tipo: str = "",
) -> list[str]:
    base = _base_textual(tema, aprendizagem, desenvolvimento, disciplina, tipo)
    perfil = _perfil_resolvido(perfil, disciplina)

    if perfil == "matematica":
        return [
            "Utilizar resolucao comentada, apoio visual e exemplos graduados para favorecer a compreensao do problema, dos procedimentos e das relacoes matematicas envolvidas.",
            "Organizar a atividade em etapas curtas, com retomadas coletivas, comparacao de estrategias e destaque para dados, operacoes e representacoes essenciais.",
            "Oferecer mediacao individual durante os registros e calculos, permitindo diferentes formas de resolucao, conferencia e explicacao das respostas.",
        ]

    if perfil in {"lingua_portuguesa_ef", "lingua_portuguesa_em", "leitura_redacao"}:
        return [
            "Oferecer leitura mediada com pausas para retomada de vocabulario, comandos, trechos importantes e relacoes de sentido necessarias a atividade.",
            "Disponibilizar roteiro, esquema, banco de ideias ou criterios de analise e producao para apoiar a organizacao das respostas e textos.",
            "Realizar mediacoes individuais, retomadas coletivas e flexibilizacao do registro conforme as necessidades observadas na turma.",
        ]

    if perfil == "orientacao_estudos":
        return [
            "Modelar estrategias de estudo com exemplos concretos, registros guiados e demonstracao de como organizar tempo, materiais e etapas da tarefa.",
            "Retomar os procedimentos com linguagem clara, perguntas orientadoras e apoio visual para favorecer a compreensao do que fazer em cada momento.",
            "Oferecer acompanhamento individualizado e diferentes formas de registro para apoiar estudantes com dificuldades de organizacao e monitoramento da aprendizagem.",
        ]

    if perfil in {"ciencias_ef", "biologia", "quimica", "fisica"}:
        return [
            "Utilizar imagens, esquemas, tabelas, demonstracoes e exemplos do cotidiano para tornar mais acessiveis os conceitos cientificos trabalhados.",
            "Organizar registros guiados com palavras-chave, relacoes de causa e consequencia, etapas do fenomeno e sinteses construidas coletivamente.",
            "Oferecer mediacao individual e correcao dialogada, permitindo respostas por topicos, desenhos, setas, explicacao oral ou frases curtas quando necessario.",
        ]

    if perfil == "historia":
        return [
            "Utilizar fontes, imagens, mapas, linhas do tempo e esquemas para apoiar a compreensao dos processos historicos e do vocabulario especifico.",
            "Retomar relacoes de tempo, causa, consequencia, permanencia e mudanca com registros guiados e sinteses no quadro.",
            "Oferecer mediacao individual e diferentes formas de resposta, como topicos, setas, frases curtas, explicacao oral ou apoio coletivo na leitura das fontes.",
        ]

    if perfil == "geografia":
        return [
            "Utilizar mapas, imagens, graficos, tabelas e exemplos proximos da realidade dos estudantes para favorecer a leitura das diferentes linguagens geograficas.",
            "Organizar registros guiados com palavras-chave, legendas, comparacoes e relacoes entre sociedade, natureza e territorio.",
            "Oferecer mediacao individual e retomadas coletivas durante a interpretacao das informacoes e a elaboracao das respostas.",
        ]

    if perfil == "ingles":
        return [
            "Apresentar vocabulario com apoio visual, modelos de frases, leitura guiada e repeticoes curtas para favorecer a compreensao e a participacao.",
            "Organizar as atividades em etapas pequenas, com exemplos de resposta, banco de palavras e checagens frequentes de entendimento.",
            "Permitir respostas por associacao, selecao, fala curta, escrita orientada ou producao em dupla, conforme a necessidade dos estudantes.",
        ]

    if perfil == "arte":
        return [
            "Utilizar imagens, sons, videos curtos, demonstracoes e exemplos culturais variados para ampliar o acesso aos repertorios mobilizados na aula.",
            "Organizar registros guiados com palavras-chave, comparacoes e sinteses coletivas para apoiar a leitura e a apreciacao das producoes artisticas.",
            "Permitir diferentes formas de participacao e expressao, como fala, escrita, desenho, criacao em dupla ou registro individual orientado.",
        ]

    if perfil in {"projeto_de_vida", "lideranca_oratoria"}:
        return [
            "Promover ambiente acolhedor, com combinados de escuta e respeito, para que os estudantes participem sem exposicao excessiva de vivencias pessoais.",
            "Utilizar perguntas orientadoras, exemplos concretos e registros visuais para apoiar a reflexao e a elaboracao das respostas.",
            "Permitir diferentes formas de participacao, como fala, escrita, desenho, registro individual ou producao em dupla, respeitando ritmos e necessidades.",
        ]

    if perfil == "educacao_financeira":
        return [
            "Utilizar situacoes concretas do cotidiano, como compras, orcamento, metas e escolhas de consumo, para favorecer a compreensao do tema.",
            "Organizar calculos, dados e informacoes em tabelas, listas, esquemas ou passo a passo no quadro para apoiar leitura e tomada de decisao.",
            "Oferecer mediacao individual e correcao dialogada, retomando vocabulario financeiro, criterios de escolha e estrategias de resolucao conforme as dificuldades observadas.",
        ]

    if perfil in {"tecnologia_inovacao", "sociologia"}:
        return [
            "Apresentar o conteudo com exemplos concretos, linguagem clara e apoio visual para favorecer a compreensao dos conceitos e problemas discutidos.",
            "Organizar registros guiados, perguntas orientadoras e sinteses parciais para apoiar a participacao e a construcao das respostas.",
            "Oferecer acompanhamento individual, retomadas coletivas e flexibilizacao das formas de registro conforme as necessidades da turma.",
        ]

    if _contem(base, ["imagem", "grafico", "mapa", "tabela", "esquema", "anuncio"]):
        primeiro_item = "Utilizar recursos visuais, exemplos concretos e mediacao oral para favorecer a compreensao do conteudo e das atividades propostas."
    else:
        primeiro_item = "Apresentar o conteudo com linguagem clara, exemplos comentados e retomadas frequentes dos pontos essenciais."

    if _contem(base, ["leitura", "texto", "fonte", "noticia", "conto", "documento"]):
        segundo_item = "Realizar leitura guiada com pausas para explicar vocabulario, informacoes centrais e comandos necessarios a participacao na aula."
    else:
        segundo_item = "Explicar as atividades passo a passo, com apoio visual e perguntas orientadoras para apoiar diferentes ritmos de aprendizagem."

    return [
        primeiro_item,
        segundo_item,
        "Oferecer mediacao individual, tempo ampliado quando necessario e diferentes formas de registro para apoiar a participacao de todos os estudantes.",
    ]
