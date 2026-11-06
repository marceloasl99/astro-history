"""
Enriquecimento dos fatos históricos com Japão, Itália, Ucrânia, África do Sul, Chile, México, etc.
"""
import json

MORE_HISTORICAL_EVENTS = [
    # Japão (Fundação Soberana pós-guerra: 1952-04-28)
    {
        "event_id": "JPN_1964_TOKYO_OLYMPICS",
        "iso_code": "JPN",
        "title": "Jogos Olímpicos de Tóquio e Estreia do Trem-Bala (Shinkansen)",
        "category": "Reforma Política & Tratado",
        "date": "1964-10-10",
        "description": "Consagração internacional da reconstrução pós-guerra e do milagre econômico e tecnológico japonês.",
        "historical_source": "Comitê Olímpico Internacional / Japan National Archives",
        "severity_notes": "Símbolo máximo da reintegração pacífica e tecnológica do Japão ao mundo."
    },
    {
        "event_id": "JPN_1990_BUBBLE_BURST",
        "iso_code": "JPN",
        "title": "Estouro da Bolha Financeira e Imobiliária Japonesa",
        "category": "Crise Financeira & Econômica",
        "date": "1990-01-04",
        "description": "Início da queda abrupta do índice Nikkei e dos preços de imóveis em Tóquio, inaugurando a 'Década Perdida' e estagnação deflacionária.",
        "historical_source": "Bank of Japan / Ministry of Finance",
        "severity_notes": "Maior contração de valor de ativos imobiliários e corporativos do Japão moderno."
    },
    {
        "event_id": "JPN_2011_FUKUSHIMA",
        "iso_code": "JPN",
        "title": "Grande Terremoto de Tohoku, Tsunami e Desastre de Fukushima",
        "category": "Desastre & Saúde Pública",
        "date": "2011-03-11",
        "description": "Sismo de magnitude 9.1 seguido de tsunami devastador de até 40 metros que causou o colapso e fusão dos reatores da usina nuclear de Fukushima Daiichi.",
        "historical_source": "National Police Agency of Japan / IAEA",
        "severity_notes": "Mais de 18.000 mortos e pior desastre nuclear mundial desde Chernobyl."
    },

    # Itália (Fundação República: 1946-06-10)
    {
        "event_id": "ITA_1978_ALDO_MORO",
        "iso_code": "ITA",
        "title": "Sequestro e Assassinato de Aldo Moro pelas Brigadas Vermelhas",
        "category": "Revolução & Conflito Interno",
        "date": "1978-03-16",
        "description": "Terroristas das Brigadas Vermelhas emboscaram e sequestraram o ex-primeiro-ministro Aldo Moro em Roma, executando-o após 55 dias de cativeiro.",
        "historical_source": "Archivio di Stato di Roma / Commissione Moro",
        "severity_notes": "O clímax sangrento dos 'Anos de Chumbo' (Anni di Piombo) na Itália."
    },
    {
        "event_id": "ITA_1992_MANI_PULITE",
        "iso_code": "ITA",
        "title": "Início da Operação Mãos Limpas (Mani Pulite)",
        "category": "Reforma Política & Tratado",
        "date": "1992-02-17",
        "description": "A prisão do político Mario Chiesa pelo promotor Antonio Di Pietro deu início às investigações que desmantelaram o sistema partidário da Primeira República italiana.",
        "historical_source": "Procura della Repubblica di Milano / Corriere della Sera",
        "severity_notes": "Extinção dos tradicionais partidos Democracia Cristã e Socialista Italiano."
    },

    # Ucrânia (Fundação: 1991-08-24)
    {
        "event_id": "UKR_2004_ORANGE_REVOLUTION",
        "iso_code": "UKR",
        "title": "Eclosão da Revolução Laranja",
        "category": "Revolução & Golpe de Estado",
        "date": "2004-11-22",
        "description": "Protestos maciços na Praça da Independência (Maidan) em Kiev denunciando fraudes eleitorais em favor de Viktor Yanukovych, forçando nova eleição sob Viktor Yushchenko.",
        "historical_source": "Central Election Commission of Ukraine / OSCE",
        "severity_notes": "Primeira grande vitória civil democrática pós-soviética na Ucrânia."
    },
    {
        "event_id": "UKR_2014_EUROMAIDAN",
        "iso_code": "UKR",
        "title": "Revolução da Dignidade (Euromaidan) e Fuga de Yanukovych",
        "category": "Revolução & Golpe de Estado",
        "date": "2014-02-22",
        "description": "Após semanas de confrontos mortais em Kiev contra a tropa de choque Berkut, o presidente pró-Moscou Viktor Yanukovych foi destituído pelo parlamento.",
        "historical_source": "Verkhovna Rada of Ukraine / Anistia Internacional",
        "severity_notes": "Seguida imediatamente pela anexação russa da Crimeia e guerra no Donbas."
    },
    {
        "event_id": "UKR_2022_RUSSIAN_INVASION",
        "iso_code": "UKR",
        "title": "Resistência Nacional à Invasão em Larga Escala Russa",
        "category": "Guerra & Conflito",
        "date": "2022-02-24",
        "description": "A Ucrânia decretou lei marcial e mobilização geral após bombardeios russos em todo o país, resistindo à tentativa de tomada rápida de Kiev.",
        "historical_source": "UCDP Conflict Data / General Staff of the Armed Forces of Ukraine",
        "severity_notes": "Maior guerra convencional entre Estados na Europa desde 1945."
    },

    # África do Sul (Fundação Democrática: 1994-05-10)
    {
        "event_id": "ZAF_1996_CONSTITUTION",
        "iso_code": "ZAF",
        "title": "Promulgação da Constituição Democrática da África do Sul",
        "category": "Reforma Política & Tratado",
        "date": "1996-12-10",
        "description": "Nelson Mandela assinou em Sharpeville a Constituição pós-apartheid, consagrada como uma das mais progressistas do mundo em direitos humanos.",
        "historical_source": "Constitutional Court of South Africa / Government Gazette",
        "severity_notes": "Fundamento legal inabalável do Estado sul-africano livre e multirracial."
    },
    {
        "event_id": "ZAF_2010_WORLD_CUP",
        "iso_code": "ZAF",
        "title": "Abertura da Copa do Mundo FIFA na África do Sul",
        "category": "Reforma Política & Tratado",
        "date": "2010-06-11",
        "description": "Primeira Copa do Mundo sediada no continente africano, celebrando a afirmação global da África do Sul e a fraternidade esportiva internacional.",
        "historical_source": "FIFA / South African Government Information",
        "severity_notes": "Símbolo de prestígio global e modernização de infraestrutura nacional."
    },

    # Chile (Fundação: 1818-02-12)
    {
        "event_id": "CHL_1879_WAR_OF_PACIFIC",
        "iso_code": "CHL",
        "title": "Início da Guerra do Pacífico (Chile contra Peru e Bolívia)",
        "category": "Guerra & Conflito",
        "date": "1879-04-05",
        "description": "Declaração de guerra do Chile à Bolívia e ao Peru pela posse das ricas jazidas de salitre e cobre do deserto de Atacama.",
        "historical_source": "Correlates of War (COW War #52) / Exército de Chile",
        "severity_notes": "Vitória chilena com incorporação de Antofagasta e Tarapacá, e perda da saída para o mar da Bolívia."
    },
    {
        "event_id": "CHL_1973_PINOCHET_COUP",
        "iso_code": "CHL",
        "title": "Golpe Militar e Bombardeio do Palácio de La Moneda",
        "category": "Revolução & Golpe de Estado",
        "date": "1973-09-11",
        "description": "As Forças Armadas comandadas por Augusto Pinochet bombardearam a sede do governo, culminando na morte de Salvador Allende e ditadura de 17 anos.",
        "historical_source": "Comisión Valech / National Security Archive",
        "severity_notes": "Instauração de regime militar autoritário e implantação do modelo neoliberal dos Chicago Boys."
    },
    {
        "event_id": "CHL_1988_PLEBISCITE",
        "iso_code": "CHL",
        "title": "Vitória do 'NO' no Plebiscito e Fim da Ditadura de Pinochet",
        "category": "Reforma Política & Tratado",
        "date": "1988-10-05",
        "description": "Por 55,9% dos votos válidos, os chilenos rejeitaram a continuidade de Pinochet, abrindo caminho para a redemocratização sob Patricio Aylwin.",
        "historical_source": "Tribunal Calificador de Elecciones de Chile / Servel",
        "severity_notes": "Transição pacífica exemplar para a democracia na América Latina."
    },

    # México (Fundação: 1810-09-16)
    {
        "event_id": "MEX_1847_BATTLE_CHAPULTEPEC",
        "iso_code": "MEX",
        "title": "Batalha de Chapultepec e Ocupação da Cidade do México",
        "category": "Guerra & Conflito",
        "date": "1847-09-13",
        "description": "Forças norte-americanas tomaram o Castelo de Chapultepec defendido pelos cadetes militares (Niños Héroes), ocupando a capital mexicana.",
        "historical_source": "Correlates of War (COW War #47) / Secretaría de la Defensa Nacional (SEDENA)",
        "severity_notes": "Ponto culminante da guerra com a subsequente perda de mais de metade do território mexicano."
    },
    {
        "event_id": "MEX_1910_MEXICAN_REVOLUTION",
        "iso_code": "MEX",
        "title": "Eclosão da Revolução Mexicana (Plano de San Luis)",
        "category": "Revolução & Golpe de Estado",
        "date": "1910-11-20",
        "description": "Francisco I. Madero fez o chamado nacional à insurreição armada contra a ditadura de mais de três décadas de Porfirio Díaz.",
        "historical_source": "Instituto Nacional de Estudios Históricos de las Revoluciones de México (INEHRM)",
        "severity_notes": "Guerra civil de 10 anos que gerou a Constituição progressista de 1917 e o México moderno."
    },
    {
        "event_id": "MEX_1994_TEQUILA_CRISIS",
        "iso_code": "MEX",
        "title": "Crise do Peso Mexicano (Efeito Tequila)",
        "category": "Crise Financeira & Econômica",
        "date": "1994-12-20",
        "description": "Desvalorização forçada do peso pelo governo de Ernesto Zedillo após o levante zapatista e assassinatos políticos, gerando fuga maciça de capitais.",
        "historical_source": "Banco de México / Fundo Monetário Internacional (FMI)",
        "severity_notes": "Resgate financeiro emergencial internacional de mais de 50 bilhões de dólares liderado pelos EUA."
    }
]

def enrich():
    target_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "country_historical_events.json")
    with open(target_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    existing_ids = {e["event_id"] for e in existing}
    added = 0
    for e in MORE_HISTORICAL_EVENTS:
        if e["event_id"] not in existing_ids:
            existing.append(e)
            existing_ids.add(e["event_id"])
            added += 1
    existing.sort(key=lambda x: (x["iso_code"], x["date"]))
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    print(f"Adicionados {added} novos fatos históricos. Total consolidado: {len(existing)} eventos em {target_path}")

if __name__ == "__main__":
    enrich()
