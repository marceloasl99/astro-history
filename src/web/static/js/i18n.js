/**
 * AstroHistory - Internationalization (i18n) Engine: Portuguese (PT) & English (EN)
 */
(function() {
    const translations = {
        en: {
            // Navigation
            "Explorar": "Explore",
            "Analisar": "Analyze",
            "Pessoal": "Personal",
            "Sobre": "About",
            "Dashboard": "Dashboard",
            "Catálogo (1.342)": "Catalog (1,342)",
            "Catálogo": "Catalog",
            "🌐 Países": "🌐 Countries",
            "Países": "Countries",
            "🔮 Linha do Tempo & Análogos": "🔮 Timeline & Analogues",
            "Linha do Tempo": "Timeline",
            "Simulador": "Simulator",
            "Correlações": "Correlations",
            "📈 Previsão": "📈 Forecast",
            "Previsão": "Forecast",
            "Previsão Probabilística": "Probabilistic Forecast",
            "Previsão Probabilística (2026–2060)": "Probabilistic Forecast (2026–2060)",
            "Abrir Previsão →": "Open Forecast →",
            "📅 Cenários": "📅 Scenarios",
            "Cenários": "Scenarios",
            "Cenários & Picos de Energia (2026–2060)": "Scenarios & Energy Peaks (2026–2060)",
            "Cenários Prospectivos & Picos de Energia Cósmica (2026–2060)": "Prospective Scenarios & Cosmic Energy Peaks (2026–2060)",
            "⚡ Picos de Energia (2026–2060)": "⚡ Energy Peaks (2026–2060)",
            "Picos de Energia": "Energy Peaks",
            "📅 Série Anual & Portais Sazonais (2027–2060)": "📅 Annual Series & Seasonal Portals (2027–2060)",
            "Série Anual & Portais Sazonais": "Annual Series & Seasonal Portals",
            "Total de Picos": "Total Peaks",
            "Conflitos Bélicos": "Military Conflicts",
            "Crises de Poder": "Power & Regime Crises",
            "Quebras Financeiras": "Financial Crashes",
            "Comoção & 🚀 Tec": "Upheaval & 🚀 Tech",
            "Todos os Cenários": "All Scenarios",
            "Guerra & Conflito Militar": "War & Military Conflict",
            "Quebra Econômica & Crise Financeira": "Economic Crash & Financial Crisis",
            "Crise Institucional & Ruptura de Poder": "Institutional Crisis & Regime Shift",
            "Comoção Social & Movimentos Coletivos": "Social Upheaval & Mass Movements",
            "Salto Tecnológico & Fronteira Espacial": "Tech Leap & Space Frontier",
            "Todos os Âmbitos": "All Scopes",
            "Mundial": "Worldwide",
            "Global / Mundial": "Global / Worldwide",
            "Assinatura Astrológica Exata:": "Exact Astrological Signature:",
            "Precedente Histórico Isomórfico:": "Isomorphic Historical Precedent:",
            "Tendência do Cenário:": "Scenario Tendency:",
            "Pico de Energia:": "Energy Peak:",
            "🔬 Metodologia": "🔬 Methodology",
            "Metodologia": "Methodology",
            "Pesquisa Científica & Astrologia Moderna": "Scientific Research & Modern Astrology",
            "Astrologia Mundana Computacional": "Computational Mundane Astrology",
            "1800–2100 Ativo": "1800–2100 Active",
            "1.342 Fatos": "1,342 Events",

            // Navigation Mega-Menu Submenu Items & Descriptions
            "Mapa Natal": "Natal Chart",
            "Carta natal e pessoas salvas": "Natal chart and saved profiles",
            "Pessoas Cadastradas": "Saved Profiles",
            "Mapas salvos em cookies/localStorage": "Charts saved locally in cookies/storage",
            "Trânsitos da Vida": "Life Transits",
            "Datas exatas do nascimento aos 100 anos": "Exact transit dates from birth to age 100",
            "Progressões": "Progressions",
            "Progressões secundárias e Lua progredida": "Secondary progressions & progressed Moon",
            "Previsão Pessoal": "Personal Forecast",
            "Ciclos e acontecimentos 2026–2050": "Planetary cycles and events 2026–2050",
            "Dados & Fontes": "Data & Sources",
            "Licenças, cobertura e versões": "Licenses, coverage and versions",
            "Glossário": "Glossary",
            "Termos de astrologia e estatística": "Astrological and statistical terms",
            "Sobre o projeto": "About the Project",
            "Equipe, citação e changelog": "Team, citation and changelog",
            "Visão geral, achados e gráfico 1800–2100": "Overview, findings and 1800–2100 chart",
            "Eventos históricos auditados": "Audited historical events",
            "Mapas soberanos e trânsitos nacionais": "Sovereign charts and national transits",
            "Teste qualquer data": "Test any historical or future date",
            "Hub de correlações": "Modern astrology correlations hub",
            "Skill walk-forward 2026–2060": "Walk-forward skill & predictions 2026–2060",
            "Picos de energia e dossiês": "Energy peaks and prospective dossiers",
            "Modelos nulos N1–N3 e hindcast": "N1–N3 null models & walk-forward hindcast",

            // Theme & Language Controls
            "Tema": "Theme",
            "Tema:": "Theme:",
            "Idioma": "Language",
            "Idioma:": "Language:",
            "Claro": "Light",
            "Escuro": "Dark",
            "Preto": "Black",
            "Tema Claro": "Light Theme",
            "Tema Escuro": "Dark Theme",
            "Tema Preto": "Black OLED Theme",
            "Tema Claro (Light Mode)": "Light Theme (Light Mode)",
            "Tema Escuro (Cosmic Navy)": "Dark Theme (Cosmic Navy)",
            "Tema Preto (OLED Pitch Black)": "Black Theme (OLED Pitch Black)",
            "Português (Brasil)": "Portuguese (Brazil)",
            "English (United States)": "English (United States)",

            // Top Banner
            "CIÊNCIA & DADOS": "SCIENCE & DATA",
            "Plataforma de pesquisa computacional e literacia estatística. Correlações geométricas não implicam determinismo causal.": "Computational research platform and data literacy. Geometric correlations do not imply causal determinism.",
            "Metodologia N1–N3": "N1–N3 Methodology",
            "Ver Metodologia & Testes Nulos": "View Methodology & Null Tests",
            "AVISO METODOLÓGICO:": "METHODOLOGICAL NOTICE:",
            "Ferramenta de pesquisa exploratória e literacia de dados. Correlações geométricas não implicam causalidade mecânica nem previsão determinística. Projeções não devem orientar decisões financeiras, políticas ou de segurança.": "Exploratory research and data literacy tool. Geometric correlations do not imply mechanical causality or deterministic prediction. Projections must not guide financial, political, or security decisions.",

            // 6 Canonical Categories
            "Guerra & Conflito": "War & Conflict",
            "Guerras & Conflitos": "Wars & Conflicts",
            "Revolução & Conflito Interno": "Revolution & Internal Conflict",
            "Revoluções & Conflitos Internos": "Revolutions & Internal Conflicts",
            "Desastre & Saúde Pública": "Disaster & Public Health",
            "Desastres & Saúde Pública": "Disasters & Public Health",
            "Crise Financeira & Econômica": "Financial & Economic Crisis",
            "Crises Financeiras & Econômicas": "Financial & Economic Crises",
            "Ciência & Tecnologia": "Science & Technology",
            "Política, Tratados & Cultura": "Politics, Treaties & Culture",
            "Todas": "All",
            "Todas as 6 Categorias": "All 6 Categories",
            "Todas as Categorias": "All Categories",
            "Amostra validada": "Validated sample",
            "✓ Amostra validada": "✓ Validated sample",
            "✓ Amostra validada (N=59)": "✓ Validated sample (N=59)",

            // Alert levels & percentiles
            "Alerta": "Alert",
            "Alerta Crítico": "Critical Alert",
            "Alerta Alto": "High Alert",
            "Alerta Moderado": "Moderate Alert",
            "Crítico": "Critical",
            "Alto": "High",
            "Moderado": "Moderate",
            "Basal": "Baseline",
            "Percentil Superior": "Upper Percentile",
            "Percentil Moderado": "Moderate Percentile",
            "Percentil Basal": "Baseline Percentile",

            // Timeline & Table headers
            "Ano": "Year",
            "Tipo": "Type",
            "Tensão Cósmica (0–1000)": "Cosmic Tension (0–1000)",
            "Tensão Cósmica": "Cosmic Tension",
            "Gatilho Cósmico Central": "Central Cosmic Trigger",
            "Sub-Índices": "Sub-Indices",
            "Fato Histórico / Precedente": "Historical Event / Precedent",
            "Síntese Analítica & Cenários": "Analytical Synthesis & Scenarios",
            "Projeção": "Projection",
            "Fato Real": "Recorded Event",
            "Histórico": "Historical",
            "Média Anual:": "Annual Average:",
            "Média Anual": "Annual Average",
            "Média Diária:": "Daily Average:",
            "Bélico:": "Conflict:",
            "Crise:": "Crisis:",
            "Ciência:": "Science:",
            "Aspectos:": "Aspects:",
            "Estrelas ativas:": "Active stars:",

            // Periods & Eras
            "Época:": "Era:",
            "Todos (1800–2100)": "All (1800–2100)",
            "Século XIX (1800–1899)": "19th Century (1800–1899)",
            "Século XX (1900–1999)": "20th Century (1900–1999)",
            "Contemporâneo (2000–2025)": "Contemporary (2000–2025)",
            "Futuro (2026–2100)": "Future (2026–2100)",

            // Cosmic History Search
            "Cosmic History Search & Métricas Internacionais": "Cosmic History Search & International Metrics",
            "Data Alvo": "Target Date",
            "Filtrar Categoria": "Filter Category",
            "Janela Cronológica": "Chronological Window",
            "Qualquer época (inclusive mesmo ano)": "Any era (including same year)",
            "Trans-histórico (mínimo ±1 ano de distância)": "Trans-historical (minimum ±1 year apart)",
            "Eras distintas (mínimo ±5 anos)": "Distinct eras (minimum ±5 years)",
            "✨ Buscar Análogos Cósmicos": "✨ Search Cosmic Analogues",
            "Buscar Análogos Cósmicos": "Search Cosmic Analogues",
            "⏳ Calculando...": "⏳ Calculating...",
            "Fatos Históricos Ocorridos sob Céus Mais Semelhantes": "Historical Events Under Most Similar Skies",
            "Precedentes Históricos Ocorridos sob Céus Semelhantes (Base 1.342 Fatos)": "Historical Precedents Under Similar Skies (1,342 Events Base)",
            "Precedentes Históricos Mais Próximos na Base (1.342 Fatos)": "Closest Historical Precedents in Database (1,342 Events)",
            "Índice Cíclico de André Barbault (CI-4 vs CI-5)": "André Barbault Cyclic Index (CI-4 vs CI-5)",
            "Métrica Sum of Cosines (Renay Oshop)": "Sum of Cosines Metric (Renay Oshop)",
            "5 Planetas Lentos": "5 Outer Planets",
            "Variância Circular:": "Circular Variance:",
            "Derivada anual:": "Annual derivative:",
            "Ver Mapa Astral & Análogos →": "View Astral Chart & Analogues →",
            "Ver Mapa Natal →": "View Natal Chart →",
            "Ver Mapa & Análogos →": "View Chart & Analogues →",
            "Ver Mapa &rarr;": "View Chart &rarr;",
            "Ver Mapa": "View Chart",
            "Ver Mapa Astral &rarr;": "View Astral Chart &rarr;",
            "Ver Todos os 1.342 Fatos &rarr;": "View All 1,342 Events &rarr;",
            "Ver &rarr;": "View &rarr;",
            "similar": "similar",

            // Dashboard
            "Monitor de Cálculos Astrológicos Históricos": "Historical Astrological Calculations Monitor",
            "Novos Módulos de Astrologia Mundana Computacional": "New Computational Mundane Astrology Modules",
            "Astrologia dos Países": "National Mundane Astrology",
            "Expansão do AstroHistory • Benchmark Internacional": "AstroHistory Expansion • International Benchmark",
            "Eventos Históricos": "Historical Events",
            "Tensão Cósmica Média": "Mean Cosmic Tension",
            "Categorias Geopolíticas": "Geopolitical Categories",
            "Motor de Efemérides": "Ephemeris Engine",
            "100% com análise de consequências": "100% with historical consequence analysis",
            "Quadraturas e Oposições ponderadas": "Weighted Squares and Oppositions",
            "Guerras, Crises, Revoluções, Ciência": "Wars, Crises, Revolutions, Science",
            "Gráfico de Tensão Cósmica & Rupturas Históricas (1800–2100)": "Cosmic Tension & Historical Ruptures Chart (1800–2100)",
            "Distribuição dos 1.342 Fatos pelas 6 Categorias Canônicas": "Distribution of 1,342 Events Across 6 Canonical Categories",
            "Posição do Sol nos 1.342 Grandes Eventos Históricos": "Sun Sign Distribution in 1,342 Major Historical Events",
            "Marcos Históricos Paradigmáticos & Mapas Natais": "Paradigmatic Historical Milestones & Natal Charts",
            "Eventos de grande relevância selecionados com suas respectivas coordenadas e cartas celestes.": "High-relevance historical events with geographical coordinates and astronomical charts.",
            "Passado:": "Past:",
            "Futuro:": "Future:",
            "de média": "average",
            "Abrir Tabela Analítica & Simulador Completo &rarr;": "Open Analytical Table & Full Simulator &rarr;",
            "Explorar Países": "Explore Countries",
            "Pesquisar Análogos": "Search Analogues",
            "Ver Linha do Tempo": "View Timeline",
            "Ver Metodologia": "View Methodology",

            // Countries Hub & Detail
            "Mapas Natais dos Países & Trânsitos Histórico-Futuros": "National Foundation Charts & Past-Future Transits",
            "Astrologia Mundana & Geopolítica Histórica": "Mundane Astrology & Historical Geopolitics",
            "Voltar ao Catálogo de Países": "Back to Countries Catalog",
            "Todos os Países": "All Countries",
            "América do Sul": "South America",
            "América do Norte": "North America",
            "Europa": "Europe",
            "Ásia": "Asia",
            "África": "Africa",
            "Oceania": "Oceania",
            "Buscar por país, código ou data...": "Search by country, code or date...",
            "Exibindo": "Displaying",
            "de": "of",
            "nações": "nations",
            "Casas Placidus": "Placidus Houses",
            "Carta Solar (Sem Casas)": "Solar Chart (No Houses)",
            "Curva Geral / Total": "Overall / Total Curve",
            "Quebra Econômica": "Economic Crash",
            "Crise Institucional": "Institutional Crisis",
            "Comoção Social": "Social Upheaval",
            "Comparar Todas": "Compare All",
            "Linha Completa (1800–2060)": "Full Timeline (1800–2060)",
            "Histórico (Passado)": "Historical (Past)",
            "Projeção Futura (2026–2060)": "Future Projection (2026–2060)",
            "Fato Real (Passado)": "Recorded Event (Past)",
            "Pico Projetado (Futuro)": "Projected Peak (Future)",

            // Simulator
            "Linha do Tempo Cosmológica & Simulador (1800–2100)": "Cosmological Timeline & Simulator (1800–2100)",
            "⚡ Recalcular Linha do Tempo (1800–2100)": "⚡ Recalculate Timeline (1800–2100)",
            "Maior Ruptura do Passado (1800-2025)": "Highest Past Rupture (1800-2025)",
            "Maior Pico Futuro (2026–2100)": "Highest Future Peak (2026–2100)",
            "Média do Passado (1800–2025)": "Past Mean (1800–2025)",
            "Média do Futuro (2026–2100)": "Future Mean (2026–2100)",
            "Todos os Anos (301)": "All Years (301)",
            "📜 Histórico (1800–2025)": "📜 Historical (1800–2025)",
            "🔮 Projeção Futura (2026–2100)": "🔮 Future Projection (2026–2100)",
            "🚨 Alerta Crítico (≥ 750)": "🚨 Critical Alert (≥ 750)",
            "⚠️ Alerta Alto (≥ 550)": "⚠️ High Alert (≥ 550)",
            "Buscar por ano, gatilho, fato histórico ou síntese...": "Search by year, trigger, historical event or synthesis...",

            // Event Detail
            "Voltar ao Catálogo dos 1.342 Fatos": "Back to 1,342 Events Catalog",
            "&larr; Voltar ao Catálogo dos 1.342 Fatos": "&larr; Back to 1,342 Events Catalog",
            "&larr; Anterior": "&larr; Previous",
            "Próximo &rarr;": "Next &rarr;",
            "Desdobramentos & Consequências Históricas": "Historical Developments & Consequences",
            "Verificação de Controle Nulo": "Null Control Verification",
            "Compare a geometria deste evento com datas aleatórias do grupo de controle que apresentaram tensão geométrica similar ou superior.": "Compare this event's geometry with control random dates exhibiting equal or higher geometric tension.",
            "🎲 Ver Controle Aleatório": "🎲 View Random Control",
            "Ver Controle Aleatório": "View Random Control",
            "Configurações em Maior Ênfase Cósmica no Momento do Fato": "Configurations with Highest Cosmic Emphasis at Event Moment",
            "Planeta em Ênfase": "Emphasized Planet",
            "Signo em Ênfase": "Emphasized Sign",
            "Aspecto em Ênfase": "Emphasized Aspect",
            "Estrela Fixa em Ênfase": "Emphasized Fixed Star",
            "Pesquisa Internacional & Astrologia Computacional": "International Research & Computational Astrology",
            "Métricas de Barbault, Oshop e Precedentes Cósmicos Análogos": "Barbault, Oshop Metrics and Analogous Cosmic Precedents",
            "Data do Fato:": "Event Date:",
            "Alinhamentos com as 30 Principais Estrelas Fixas (Orbe Estrito ≤ 0,3° / 18')": "Alignments with 30 Major Fixed Stars (Strict Orb ≤ 0.3° / 18')",
            "Contato(s) Detectado(s)": "Contact(s) Detected",
            "Mandala Astrológica de Alta Precisão (Swiss Ephemeris)": "High-Precision Astrological Mandala (Swiss Ephemeris)",

            // Correlations
            "Hub de Correlações da Astrologia Moderna": "Modern Astrology Correlations Hub",
            "Nível Médio de Tensão Cósmica por Categoria de Fato Histórico": "Mean Cosmic Tension by Historical Event Category",
            "Concentrações Significativas:": "Significant Concentrations:",
            "Grandes Ciclos Planetários Registrados no Dataset": "Major Planetary Cycles Recorded in Dataset",
            "Ciclo Saturno-Plutão": "Saturn-Pluto Cycle",
            "Ciclo Urano-Plutão": "Uranus-Pluto Cycle",
            "Investigação Internacional de Ciclos Globais (Barbault, Oshop & Tarnas)": "International Global Cycles Investigation (Barbault, Oshop & Tarnas)",

            // Methodology
            "Metodologia, Modelos Nulos & Validação Científica": "Methodology, Null Models & Scientific Validation",
            "Métodos Internacionais & Astrologia Computacional": "International Methods & Computational Astrology",
            "Catálogo Geral:": "General Catalog:",
            "Amostra Qualificada:": "Qualified Sample:",
            "Amostra Analítica Congelada:": "Frozen Analytical Sample:",
            "Hindcast Walk-Forward (Skill de Previsão)": "Walk-Forward Hindcast (Forecast Skill)",
            "Resultados Empíricos dos Testes de Hipótese (Amostra Pré-Registrada · N=59)": "Empirical Hypothesis Testing Results (Pre-Registered Sample · N=59)",

            // Footer
            "Plataforma Internacional de Pesquisa Computacional em Astrologia Mundana & Ephemerides Suíças.": "International Computational Research Platform in Mundane Astrology & Swiss Ephemerides.",
            "Modelos Nulos N1–N3": "N1–N3 Null Models",
            "Skill Walk-Forward": "Walk-Forward Skill",
            "Mapas Soberanos": "Sovereign Charts",
            "Swiss Ephemeris © Astrodienst AG • Licenciado sob GNU AGPL-3.0-or-later • 1.342 fatos históricos catalogados (1800–2100)": "Swiss Ephemeris © Astrodienst AG • Licensed under GNU AGPL-3.0-or-later • 1,342 historical events cataloged (1800–2100)"
        }
    };

    // State management
    let currentLang = localStorage.getItem('astro_lang') || 'pt';

    function setLanguage(lang) {
        if (lang !== 'pt' && lang !== 'en') lang = 'pt';
        currentLang = lang;
        localStorage.setItem('astro_lang', lang);
        document.cookie = `astro_lang=${lang};path=/;max-age=31536000;SameSite=Lax`;
        document.documentElement.setAttribute('lang', lang === 'en' ? 'en-US' : 'pt-BR');

        updateLanguageUIButtons();
        applyTranslationsToDOM();
    }

    function updateLanguageUIButtons() {
        document.querySelectorAll('.lang-btn').forEach(btn => {
            const lang = btn.getAttribute('data-lang');
            if (lang === currentLang) {
                btn.classList.add('bg-amber-400', 'text-slate-950', 'font-bold');
                btn.classList.remove('text-slate-300', 'hover:text-white', 'text-slate-400');
            } else {
                btn.classList.remove('bg-amber-400', 'text-slate-950', 'font-bold');
                btn.classList.add('text-slate-400', 'hover:text-white');
            }
        });
    }

    function applyTranslationsToDOM() {
        if (currentLang === 'pt') {
            // Se o usuário selecionou português, caso já estivesse traduzido para EN, recarrega o estado nativo
            if (sessionStorage.getItem('was_en_translated') === 'true') {
                sessionStorage.removeItem('was_en_translated');
                window.location.reload();
            }
            return;
        }

        sessionStorage.setItem('was_en_translated', 'true');
        const dict = translations.en;

        // 1. Tradução de nós de texto exatos
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            const trimmed = node.nodeValue.trim();
            if (dict[trimmed]) {
                node.nodeValue = node.nodeValue.replace(trimmed, dict[trimmed]);
            } else {
                // Checar substituições de categorias e alertas dentro de strings
                let val = node.nodeValue;
                let changed = false;
                for (const [ptKey, enVal] of Object.entries(dict)) {
                    if (ptKey.length > 5 && val.includes(ptKey)) {
                        val = val.replaceAll(ptKey, enVal);
                        changed = true;
                    }
                }
                if (changed) {
                    node.nodeValue = val;
                }
            }
        }

        // 2. Tradução de placeholders
        document.querySelectorAll('input[placeholder], textarea[placeholder]').forEach(el => {
            const ph = el.getAttribute('placeholder');
            if (dict[ph]) el.setAttribute('placeholder', dict[ph]);
        });

        // 3. Tradução de títulos (tooltips)
        document.querySelectorAll('[title]').forEach(el => {
            const t = el.getAttribute('title');
            if (dict[t]) el.setAttribute('title', dict[t]);
        });

        // 4. Tradução de botões e links específicos (somente nós folha para preservar ícones e spans internos)
        document.querySelectorAll('a, button, span, th, td').forEach(el => {
            if (el.children.length === 0) {
                const text = el.innerText ? el.innerText.trim() : '';
                if (dict[text]) {
                    el.innerText = dict[text];
                }
            }
        });
    }

    // Theme Management (Light is default)
    let currentTheme = localStorage.getItem('astro_theme') || 'light';

    function setTheme(theme) {
        if (!['light', 'dark', 'oled'].includes(theme)) theme = 'light';
        currentTheme = theme;
        localStorage.setItem('astro_theme', theme);
        document.cookie = `astro_theme=${theme};path=/;max-age=31536000;SameSite=Lax`;

        const docEl = document.documentElement;
        docEl.classList.remove('theme-light', 'theme-dark', 'theme-oled');
        docEl.classList.add('theme-' + theme);
        if (theme === 'light') {
            docEl.classList.remove('dark');
        } else {
            docEl.classList.add('dark');
        }

        updateThemeUIButtons(theme);
        syncChartThemes(theme);
        window.dispatchEvent(new CustomEvent('astro-theme-changed', { detail: { theme } }));
    }

    function syncChartThemes(theme) {
        const isLight = theme === 'light';
        const gridColor = isLight ? 'rgba(0, 0, 0, 0.08)' : 'rgba(255, 255, 255, 0.06)';
        const textColor = isLight ? '#475569' : '#94a3b8';

        if (typeof Chart !== 'undefined') {
            Chart.defaults.color = textColor;
            Chart.defaults.borderColor = gridColor;

            if (Chart.instances) {
                Object.values(Chart.instances).forEach(chart => {
                    try {
                        if (chart.options && chart.options.scales) {
                            Object.values(chart.options.scales).forEach(scale => {
                                if (scale.ticks) scale.ticks.color = textColor;
                                if (scale.grid) scale.grid.color = gridColor;
                            });
                        }
                        chart.update('none');
                    } catch(e) {}
                });
            }
        }
    }

    function updateThemeUIButtons(theme) {
        const active = theme || currentTheme;
        document.querySelectorAll('.theme-btn').forEach(btn => {
            const t = btn.getAttribute('data-theme');
            if (t === active) {
                btn.classList.add('bg-amber-400', 'text-slate-950', 'font-bold', 'shadow-sm');
                btn.classList.remove('text-slate-400', 'hover:text-white');
            } else {
                btn.classList.remove('bg-amber-400', 'text-slate-950', 'font-bold', 'shadow-sm');
                btn.classList.add('text-slate-400', 'hover:text-white');
            }
        });
    }

    // Inicialização ao carregar o DOM
    document.addEventListener('DOMContentLoaded', () => {
        updateThemeUIButtons(currentTheme);
        updateLanguageUIButtons();
        syncChartThemes(currentTheme);
        if (currentLang === 'en') {
            applyTranslationsToDOM();
        }
    });

    // Expor globalmente
    window.setLanguage = setLanguage;
    window.getCurrentLanguage = () => currentLang;
    window.setTheme = setTheme;
    window.getCurrentTheme = () => currentTheme;
})();
