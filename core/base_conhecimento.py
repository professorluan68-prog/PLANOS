from typing import Dict, Any

PADROES_DISCIPLINARES: Dict[str, Dict[str, Any]] = {
    "lingua_portuguesa": {
        "tom": "dialogico e reflexivo",
        "verbos_comando": ["discutam", "reflitam", "compartilhem", "analisem", "identifiquem"],
        "tecnicas_esperadas": ["VIREM E CONVERSEM", "TODO MUNDO ESCREVE", "COM SUAS PALAVRAS", "HORA DA LEITURA", "UM PASSO DE CADA VEZ"],
        "tempos": {
            "para_comecar": "5 minutos",
            "foco": "variável",
            "pause": "2 minutos",
            "pratica": "15 minutos",
            "encerramento": "5 minutos"
        },
        "instrucoes_especificas": "Foco em gêneros textuais, análise de textos autênticos e produção. A correção deve ser mediada promovendo reflexão sobre as escolhas linguísticas."
    },
    "ciencias": {
        "tom": "cientifico-didatico",
        "verbos_comando": ["observem", "analisem", "identifiquem", "formulem hipóteses", "relacionem"],
        "tecnicas_esperadas": ["VIREM E CONVERSEM", "TODO MUNDO ESCREVE", "HORA DA LEITURA", "COM SUAS PALAVRAS", "DE OLHO NO MODELO"],
        "tempos": {
            "para_comecar": "5 minutos",
            "foco": "variável",
            "pause": "2 minutos",
            "pratica": "10 a 15 minutos",
            "encerramento": "5 minutos"
        },
        "instrucoes_especificas": "A aula deve ir do concreto ao abstrato. Sempre inicie com contextualização (dados reais) e problematização. Uso de infográficos e imagens é essencial."
    },
    "historia": {
        "tom": "analitico e contextualizado",
        "verbos_comando": ["analisem", "comparem", "contextualizem", "relacionem", "identifiquem"],
        "tecnicas_esperadas": ["VIREM E CONVERSEM", "HORA DA LEITURA", "TODO MUNDO ESCREVE", "DE OLHO NO MODELO", "COM SUAS PALAVRAS"],
        "tempos": {
            "para_comecar": "5 a 7 minutos",
            "foco": "variável",
            "pause": "1 a 2 minutos",
            "pratica": "10 a 30 minutos",
            "encerramento": "5 minutos"
        },
        "instrucoes_especificas": "Forte ênfase na análise de fontes primárias e secundárias. Conexões constantes entre passado e presente. Respeitar sequência cronológica."
    },
    "ingles": {
        "tom": "comunicativo e prático",
        "verbos_comando": ["listen", "repeat", "read", "write", "practice", "roleplay"],
        "tecnicas_esperadas": ["LISTEN AND REPEAT", "WRITE AND SHARE", "SAY IT IN ENGLISH", "VIREM E CONVERSEM"],
        "tempos": {
            "para_comecar": "5 minutos",
            "foco": "variável",
            "pause": "2 minutos",
            "pratica": "15 a 20 minutos",
            "encerramento": "5 minutos"
        },
        "instrucoes_especificas": "Aulas estruturadas de forma bilíngue (instruções em português, prática em inglês). Foco no desenvolvimento de habilidades integradas e repetição funcional."
    },
    "matematica": {
        "tom": "investigativo e logico",
        "verbos_comando": ["calculem", "demonstrem", "resolvam", "modelarem", "verifiquem"],
        "tecnicas_esperadas": ["TODO MUNDO ESCREVE", "VIREM E CONVERSEM", "COM SUAS PALAVRAS", "DE OLHO NO MODELO"],
        "tempos": {
            "para_comecar": "5 minutos",
            "foco": "variável",
            "pause": "3 minutos",
            "pratica": "20 minutos",
            "encerramento": "5 minutos"
        },
        "instrucoes_especificas": "Sempre formalizar o conceito após a exploração inicial. A prática deve contar com verificação de resultados e validação de estratégias de resolução."
    },
    "projeto_de_vida": {
        "tom": "acolhedor e reflexivo",
        "verbos_comando": ["reflitam", "compartilhem", "planejem", "autoavaliem", "escutem"],
        "tecnicas_esperadas": ["RODA DE CONVERSA", "TODO MUNDO ESCREVE", "COM SUAS PALAVRAS", "VIREM E CONVERSEM"],
        "tempos": {
            "para_comecar": "8 minutos",
            "foco": "variável",
            "pause": "2 minutos",
            "pratica": "15 minutos",
            "encerramento": "10 minutos"
        },
        "instrucoes_especificas": "A socialização é sempre voluntária e mediada. Sem respostas 'certas' ou 'erradas' para sentimentos. Validação de perspectivas individuais."
    },
    "geral": {
        "tom": "didatico e mediador",
        "verbos_comando": ["observem", "discutam", "registrem", "leiam"],
        "tecnicas_esperadas": ["VIREM E CONVERSEM", "TODO MUNDO ESCREVE", "COM SUAS PALAVRAS", "HORA DA LEITURA"],
        "tempos": {
            "para_comecar": "5 minutos",
            "foco": "variável",
            "pause": "2 minutos",
            "pratica": "15 minutos",
            "encerramento": "5 minutos"
        },
        "instrucoes_especificas": "Manter a intencionalidade pedagógica clara. Garantir que a mediação do professor esteja explícita em todas as etapas."
    }
}

TECNICAS_UNIVERSAIS = [
    "VIREM E CONVERSEM",
    "TODO MUNDO ESCREVE",
    "COM SUAS PALAVRAS",
    "DE OLHO NO MODELO",
    "HORA DA LEITURA",
    "UM PASSO DE CADA VEZ",
    "CIRCULAR PELA SALA",
    "VERIFICAR A COMPREENSÃO",
    "BILHETE DE SAÍDA",
]

ESTRUTURA_BASE_ETAPAS = {
    "introducao": ["Para começar", "Relembre"],
    "desenvolvimento": ["Foco no conteúdo"],
    "aplicacao": ["Na prática"],
    "sistematizacao": ["Sistematização"],
    "conclusao": ["Encerramento"],
}
