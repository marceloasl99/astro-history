"""
Gerador da Versão Standalone Estática do AstroHistory para GitHub Pages e Servidores Estáticos.
Gera um único arquivo 'web/index.html' totalmente funcional, autônomo e auto-contido,
com todos os 3.406 fatos históricos, 107 países, 148 picos de energia 2026-2060,
linha do tempo 1800-2100, projeções anuais e previsões pré-calculadas.
"""

import json
import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "web")
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "index.html")

def build_standalone():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("1. Extraindo dados do SQLite e arquivos JSON...")

    # 1. Eventos Históricos (3.406) com cartas celestes calculadas
    conn = sqlite3.connect(os.path.join(BASE_DIR, "db", "history_astrology.db"))
    c = conn.cursor()
    c.execute("""
        SELECT id, title, category, date, time, city, country, consequence, 
               tension_index, sun_sign, moon_sign, ascendant_sign, chart_json 
        FROM events ORDER BY date ASC
    """)
    rows = c.fetchall()

    events_list = []
    for r in rows:
        chart = json.loads(r[12]) if r[12] else {}
        planets = chart.get("planets", [])
        aspects = chart.get("aspects", [])
        stars = chart.get("star_contacts", []) or chart.get("fixed_stars", [])

        events_list.append({
            "id": r[0],
            "title": r[1],
            "category": r[2],
            "date": r[3],
            "time": r[4] or "12:00",
            "city": r[5] or "",
            "country": r[6] or "",
            "consequence": r[7] or "",
            "tension": round(float(r[8] or 0), 1),
            "sun": r[9] or "Calculado",
            "moon": r[10] or "Calculado",
            "asc": r[11] or "Calculado",
            "planets": [
                {
                    "name": p["name"],
                    "sym": p["symbol"],
                    "sign": p["sign_name"],
                    "ssym": p["sign_symbol"],
                    "deg": p.get("short_formatted", p.get("formatted", ""))
                }
                for p in planets
            ] if planets else [],
            "aspects": [
                {
                    "p1": a.get("planet1_symbol", ""),
                    "p1_name": a.get("planet1_name", ""),
                    "p2": a.get("planet2_symbol", ""),
                    "p2_name": a.get("planet2_name", ""),
                    "asp": a.get("aspect_symbol", ""),
                    "name": a.get("aspect_name", ""),
                    "orb": round(float(a.get("orb", 0.0)), 1),
                    "nature": a.get("nature", "tenso")
                }
                for a in aspects[:8]
            ] if aspects else [],
            "stars": [
                {
                    "star": s.get("star_name", ""),
                    "planet": s.get("planet_name", ""),
                    "orb": round(float(s.get("orb", 0.0)), 2)
                }
                for s in stars[:4]
            ] if stars else []
        })

    # Estatísticas de categorias e signos solares
    categories_cnt = {}
    sun_signs_cnt = {}
    for ev in events_list:
        cat = ev["category"]
        categories_cnt[cat] = categories_cnt.get(cat, 0) + 1
        s = ev["sun"]
        if s:
            sun_signs_cnt[s] = sun_signs_cnt.get(s, 0) + 1

    categories_stats = [{"category": k, "cnt": v} for k, v in sorted(categories_cnt.items(), key=lambda x: -x[1])]
    sun_signs_stats = [{"sun_sign": k, "cnt": v} for k, v in sorted(sun_signs_cnt.items(), key=lambda x: -x[1])]

    # 2. Timeline 1800-2100
    with open(os.path.join(BASE_DIR, "data", "timeline_1800_2100.json"), "r", encoding="utf-8") as f:
        timeline_full = json.load(f)

    opt_timeline = []
    for y in timeline_full.get("timeline", []):
        opt_timeline.append({
            "year": y["year"],
            "is_hist": y.get("is_historical", False),
            "peak": y.get("peak_tension_1000", 0),
            "avg": y.get("avg_tension_1000") or y.get("annual_percentile_1000", 0),
            "conflict": y.get("conflict_risk_index_1000", 0),
            "tech": y.get("tech_innovation_index_1000", 0),
            "barbault": y.get("barbault_concentration_1000", 0),
            "alert": y.get("alert_level", "Moderado"),
            "trigger": y.get("cosmic_trigger", ""),
            "events": [e.get("title") for e in y.get("historical_events", [])[:3]],
            "top_event": y.get("top_matches", [{}])[0].get("title") if y.get("top_matches") else "",
            "top_year": y.get("top_matches", [{}])[0].get("year") if y.get("top_matches") else "",
            "scenarios": y.get("scenarios_and_possibilities", "")
        })

    # 3. Picos de Energia 2026-2060
    with open(os.path.join(BASE_DIR, "data", "energy_peaks_2026_2060.json"), "r", encoding="utf-8") as f:
        peaks_data = json.load(f)

    # 4. Países (107)
    with open(os.path.join(BASE_DIR, "data", "countries_database.json"), "r", encoding="utf-8") as f:
        countries_data = json.load(f)

    # 5. Projeções 2027-2060
    with open(os.path.join(BASE_DIR, "data", "projections_2027_2060.json"), "r", encoding="utf-8") as f:
        projections_data = json.load(f)

    # 6. Previsões 2026-2060
    with open(os.path.join(BASE_DIR, "data", "forecast_v3.json"), "r", encoding="utf-8") as f:
        forecast_data = json.load(f)

    bundle = {
        "stats": {
            "total_events": len(events_list),
            "time_span": "490 a.C. – 2100",
            "categories": categories_stats,
            "sun_signs_distribution": sun_signs_stats,
            "avg_past_tension": timeline_full.get("avg_past_tension", 492.6),
            "avg_future_tension": timeline_full.get("avg_future_tension", 529.0),
            "highest_past_rupture": timeline_full.get("highest_past_rupture", {"year": 1941, "tension": 995.0, "event": "Segunda Guerra Mundial / Pearl Harbor"}),
            "highest_future_year": timeline_full.get("highest_future_year", {"year": 2034, "tension": 996.0})
        },
        "events": events_list,
        "timeline": opt_timeline,
        "peaks": peaks_data,
        "countries": countries_data,
        "projections": projections_data,
        "forecast": forecast_data,
        "methodology": {
            "h1": {"z": -0.506, "p": 0.612, "q": 0.883, "result": "Hipótese Nula NÃO Rejeitada"},
            "tost": {"bounds": "±0.30 DP", "p": 0.041, "result": "Efeito Estatisticamente Equivalente a Zero"},
            "sample_n": 59,
            "catalog_total": 3406,
            "control_dates": 10000
        }
    }

    print(f"2. Dados consolidados: {len(events_list)} eventos, {len(opt_timeline)} anos de linha do tempo, {len(peaks_data['peaks'])} picos, {len(countries_data)} países.")
    bundle_json_str = json.dumps(bundle, ensure_ascii=False)
    print(f"Tamanho do bundle JSON em memória: {len(bundle_json_str.encode('utf-8')) / 1024:.1f} KB")

    print("3. Gerando HTML standalone unificado 'web/index.html'...")
    # Monta o HTML unificado
    html_content = generate_html_template(bundle_json_str)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"4. Sucesso! Arquivo estático standalone criado em: {OUTPUT_HTML} ({os.path.getsize(OUTPUT_HTML) / 1024:.1f} KB)")

def generate_html_template(bundle_json: str) -> str:
    # Retorna o HTML único completo com Tailwind, Chart.js, CSS e todo o Javascript reativo
    return f"""<!DOCTYPE html>
<html lang="pt-BR" class="theme-light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AstroHistory | Plataforma Standalone de Astrologia Mundana Computacional (v7.0.0)</title>

    <!-- FOUC Prevention & Initial Theme Restore -->
    <script>
        (function() {{
            try {{
                var theme = localStorage.getItem('astro_theme') || 'light';
                var doc = document.documentElement;
                doc.classList.remove('theme-light', 'theme-dark', 'theme-oled');
                doc.classList.add('theme-' + theme);
                if (theme === 'light') doc.classList.remove('dark'); else doc.classList.add('dark');
            }} catch(e) {{}}
        }})();
    </script>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
                        display: ['"Cinzel"', 'serif'],
                        mono: ['"JetBrains Mono"', 'monospace']
                    }}
                }}
            }}
        }}
    </script>

    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

    <style>
        /* Base Dark Background */
        body {{
            background-color: #060913;
            color: #f1f5f9;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .glass-panel {{
            background: rgba(11, 17, 32, 0.85);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
        }}
        /* Theme OLED (Pitch Black) */
        html.theme-oled body {{
            background-color: #000000 !important;
            background-image: none !important;
            color: #f8fafc !important;
        }}
        html.theme-oled .glass-panel {{
            background: #080808 !important;
            border-color: rgba(255, 255, 255, 0.12) !important;
            box-shadow: none !important;
        }}
        /* Theme Light */
        html.theme-light body {{
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }}
        html.theme-light .glass-panel {{
            background: rgba(255, 255, 255, 0.95) !important;
            border-color: #e2e8f0 !important;
            box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.06) !important;
            color: #0f172a !important;
        }}
        html.theme-light .text-white {{ color: #0f172a !important; }}
        html.theme-light .text-slate-300 {{ color: #334155 !important; }}
        html.theme-light .text-slate-400 {{ color: #64748b !important; }}
        html.theme-light .bg-slate-900 {{ background-color: #f1f5f9 !important; border-color: #cbd5e1 !important; }}
        html.theme-light .bg-slate-800 {{ background-color: #e2e8f0 !important; border-color: #cbd5e1 !important; }}
        html.theme-light input {{ background-color: #ffffff !important; color: #0f172a !important; border-color: #cbd5e1 !important; }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: rgba(0, 0, 0, 0.2); }}
        ::-webkit-scrollbar-thumb {{ background: rgba(255, 255, 255, 0.2); border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: rgba(255, 255, 255, 0.35); }}
    </style>
</head>
<body class="antialiased">

    <!-- Top Navigation Bar -->
    <header class="sticky top-0 z-50 glass-panel border-b border-slate-800/80">
        <div class="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
            <!-- Brand Logo -->
            <div class="flex items-center gap-3 shrink-0 cursor-pointer" onclick="switchMainTab('dashboard')">
                <span class="text-2xl">🪐</span>
                <div>
                    <span class="font-display font-black text-lg tracking-wider text-white">AstroHistory</span>
                    <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-400/20 text-amber-300 border border-amber-400/30 ml-1.5 font-bold">v5.0.0 Static</span>
                </div>
            </div>

            <!-- Navigation Links (Tabs) -->
            <nav class="hidden xl:flex items-center gap-1.5" id="nav-desktop">
                <button type="button" onclick="switchMainTab('dashboard')" data-tab="dashboard" class="nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 bg-amber-400 text-slate-950 shadow-sm">
                    <span>📊</span> <span data-i18n="Dashboard">Dashboard</span>
                </button>
                <button type="button" onclick="switchMainTab('catalog')" data-tab="catalog" class="nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition flex items-center gap-1.5">
                    <span>📚</span> <span data-i18n="Catálogo">Catálogo (3.406)</span>
                </button>
                <button type="button" onclick="switchMainTab('countries')" data-tab="countries" class="nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition flex items-center gap-1.5">
                    <span>🌐</span> <span data-i18n="Países">Países Soberanos</span>
                </button>
                <button type="button" onclick="switchMainTab('peaks')" data-tab="peaks" class="nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition flex items-center gap-1.5">
                    <span>⚡</span> <span data-i18n="Picos de Energia">Picos de Energia (148)</span>
                </button>
                <button type="button" onclick="switchMainTab('scenarios')" data-tab="scenarios" class="nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition flex items-center gap-1.5">
                    <span>📅</span> <span data-i18n="Cenários">Cenários 2027–2060</span>
                </button>
                <button type="button" onclick="switchMainTab('simulator')" data-tab="simulator" class="nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition flex items-center gap-1.5">
                    <span>🔮</span> <span data-i18n="Simulador">Linha do Tempo 1800–2100</span>
                </button>
                <button type="button" onclick="switchMainTab('forecast')" data-tab="forecast" class="nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition flex items-center gap-1.5">
                    <span>📈</span> <span data-i18n="Previsão">Previsão Probabilística</span>
                </button>
                <button type="button" onclick="switchMainTab('methodology')" data-tab="methodology" class="nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition flex items-center gap-1.5">
                    <span>🔬</span> <span data-i18n="Metodologia">Metodologia N1–N3</span>
                </button>
            </nav>

            <!-- Controls: Theme & Language -->
            <div class="flex items-center gap-2">
                <!-- Theme Toggle -->
                <div class="flex items-center bg-slate-900/90 p-0.5 rounded-xl border border-slate-800 shadow-inner">
                    <button type="button" onclick="setAppTheme('light')" data-theme="light" class="theme-btn w-7 h-7 rounded-lg text-xs flex items-center justify-center transition" title="Claro">☀️</button>
                    <button type="button" onclick="setAppTheme('dark')" data-theme="dark" class="theme-btn w-7 h-7 rounded-lg text-xs flex items-center justify-center transition" title="Escuro">🌙</button>
                    <button type="button" onclick="setAppTheme('oled')" data-theme="oled" class="theme-btn w-7 h-7 rounded-lg text-xs flex items-center justify-center transition bg-amber-400 text-slate-950 font-bold" title="Preto OLED">🖤</button>
                </div>

                <!-- Language Toggle -->
                <div class="flex items-center bg-slate-900/90 p-0.5 rounded-xl border border-slate-800 shadow-inner">
                    <button type="button" onclick="setAppLang('pt')" data-lang="pt" class="lang-btn px-2 py-1 rounded-lg text-[11px] font-mono font-bold bg-amber-400 text-slate-950 transition">PT</button>
                    <button type="button" onclick="setAppLang('en')" data-lang="en" class="lang-btn px-2 py-1 rounded-lg text-[11px] font-mono font-bold text-slate-400 hover:text-white transition">EN</button>
                </div>

                <!-- Mobile Hamburger -->
                <button type="button" onclick="toggleMobileNav()" class="xl:hidden p-2 rounded-xl bg-slate-800 text-slate-300 hover:text-white border border-slate-700">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
                </button>
            </div>
        </div>

        <!-- Mobile Menu Dropdown -->
        <div id="nav-mobile" class="hidden xl:hidden p-4 bg-slate-950 border-b border-slate-800 space-y-2">
            <button type="button" onclick="switchMainTab('dashboard'); toggleMobileNav();" class="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2"><span>📊</span> Dashboard</button>
            <button type="button" onclick="switchMainTab('catalog'); toggleMobileNav();" class="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2"><span>📚</span> Catálogo (3.406)</button>
            <button type="button" onclick="switchMainTab('countries'); toggleMobileNav();" class="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2"><span>🌐</span> Países Soberanos</button>
            <button type="button" onclick="switchMainTab('peaks'); toggleMobileNav();" class="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2"><span>⚡</span> Picos de Energia (148)</button>
            <button type="button" onclick="switchMainTab('scenarios'); toggleMobileNav();" class="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2"><span>📅</span> Cenários 2027–2060</button>
            <button type="button" onclick="switchMainTab('simulator'); toggleMobileNav();" class="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2"><span>🔮</span> Linha do Tempo</button>
            <button type="button" onclick="switchMainTab('forecast'); toggleMobileNav();" class="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2"><span>📈</span> Previsões</button>
            <button type="button" onclick="switchMainTab('methodology'); toggleMobileNav();" class="w-full text-left px-3 py-2 rounded-lg text-sm font-semibold text-slate-200 hover:bg-slate-800 flex items-center gap-2"><span>🔬</span> Metodologia</button>
        </div>
    </header>

    <!-- Main Workspace Container -->
    <main class="flex-grow w-full max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        <!-- ============================================================= -->
        <!-- TAB 1: DASHBOARD GERAL                                        -->
        <!-- ============================================================= -->
        <section id="tab-dashboard" class="tab-pane space-y-8">
            <!-- Hero Banner -->
            <div class="glass-panel p-6 sm:p-10 rounded-3xl relative overflow-hidden border border-slate-700/60 shadow-2xl">
                <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-8">
                    <div class="max-w-3xl space-y-4">
                        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-400/10 text-amber-300 border border-amber-400/30">
                            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                            <span>Standalone GitHub Pages • 3.406 Fatos Históricos • Swiss Ephemeris 2.10</span>
                        </div>
                        <h1 class="font-display text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
                            Astrologia Mundana Computacional
                        </h1>
                        <p class="text-slate-300 text-sm sm:text-base leading-relaxed">
                            Versão 100% autônoma e executável offline ou em servidores estáticos. Investigação empírica de 2.500 anos de história global sob ciclos astronômicos, efemérides suíças e modelos nulos N1–N3. Todos os dados e gráficos encontram-se pré-calculados.
                        </p>
                        <div class="flex flex-wrap items-center gap-3 pt-2">
                            <button type="button" onclick="switchMainTab('peaks')" class="px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs sm:text-sm transition flex items-center gap-2 shadow-lg shadow-amber-400/10">
                                <span>⚡</span> <span>Ver Picos de Energia (2026–2060)</span>
                            </button>
                            <button type="button" onclick="switchMainTab('catalog')" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs sm:text-sm border border-slate-700 transition flex items-center gap-2">
                                <span>📚</span> <span>Explorar 3.406 Fatos</span>
                            </button>
                            <button type="button" onclick="switchMainTab('countries')" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-sky-300 font-semibold text-xs sm:text-sm border border-slate-700 transition flex items-center gap-2">
                                <span>🌐</span> <span>Países Soberanos</span>
                            </button>
                            <button type="button" onclick="switchMainTab('methodology')" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-300 font-semibold text-xs sm:text-sm border border-slate-700 transition flex items-center gap-2">
                                <span>🔬</span> <span>Metodologia N1–N3</span>
                            </button>
                        </div>
                    </div>

                    <!-- Hero Quick Stats Card -->
                    <div class="lg:w-80 shrink-0 bg-slate-900/90 rounded-2xl p-5 border border-slate-700/80 shadow-xl space-y-4">
                        <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                            <span class="text-xs uppercase font-mono tracking-wider text-slate-400 font-bold">Base de Dados</span>
                            <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">100% Autônoma</span>
                        </div>
                        <div class="space-y-3">
                            <div>
                                <div class="flex justify-between text-xs mb-1">
                                    <span class="text-slate-400">Marcos Históricos:</span>
                                    <span class="font-bold text-white font-mono">3.406 eventos</span>
                                </div>
                                <div class="w-full bg-slate-800 rounded-full h-2">
                                    <div class="bg-amber-400 h-2 rounded-full w-full"></div>
                                </div>
                            </div>
                            <div>
                                <div class="flex justify-between text-xs mb-1">
                                    <span class="text-slate-400">Janela Temporal:</span>
                                    <span class="font-bold text-sky-300 font-mono">490 a.C. – 2100</span>
                                </div>
                                <div class="w-full bg-slate-800 rounded-full h-2">
                                    <div class="bg-sky-400 h-2 rounded-full w-full"></div>
                                </div>
                            </div>
                            <div>
                                <div class="flex justify-between text-xs mb-1">
                                    <span class="text-slate-400">Picos 2026–2060:</span>
                                    <span class="font-bold text-rose-300 font-mono">148 picos</span>
                                </div>
                                <div class="w-full bg-slate-800 rounded-full h-2">
                                    <div class="bg-rose-400 h-2 rounded-full w-full"></div>
                                </div>
                            </div>
                        </div>
                        <div class="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                            <span>Modo de Execução:</span>
                            <span class="font-mono text-emerald-400 font-bold">Zero Backend (Pure Client)</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Top KPIs -->
            <div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="glass-panel p-5 rounded-2xl border-l-4 border-amber-400">
                    <span class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Eventos Auditados</span>
                    <div class="text-3xl font-black text-white font-mono mt-1" id="dashTotalEvents">3.406</div>
                    <div class="text-xs text-amber-300/80 mt-1">100% com efemérides suíças</div>
                </div>
                <div class="glass-panel p-5 rounded-2xl border-l-4 border-sky-400">
                    <span class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Média Histórica (Passado)</span>
                    <div class="text-3xl font-black text-sky-300 font-mono mt-1">492.6 <span class="text-xs text-slate-500">/1000</span></div>
                    <div class="text-xs text-slate-400 mt-1">1800–2025 (226 anos)</div>
                </div>
                <div class="glass-panel p-5 rounded-2xl border-l-4 border-rose-400">
                    <span class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Maior Ruptura Histórica</span>
                    <div class="text-3xl font-black text-rose-300 font-mono mt-1">995.0 <span class="text-xs text-slate-500">(1941)</span></div>
                    <div class="text-xs text-slate-400 mt-1">II Guerra Mundial / Pearl Harbor</div>
                </div>
                <div class="glass-panel p-5 rounded-2xl border-l-4 border-purple-400">
                    <span class="text-xs uppercase tracking-wider text-slate-400 font-semibold">Picos de Energia 2026–60</span>
                    <div class="text-3xl font-black text-purple-300 font-mono mt-1">148 <span class="text-xs text-slate-500">picos</span></div>
                    <div class="text-xs text-slate-400 mt-1">81 Críticos • 67 Altos</div>
                </div>
            </div>

            <!-- Interactive Timeline Chart (1800-2100) -->
            <div class="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
                <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div>
                        <h2 class="text-xl font-bold text-white flex items-center gap-2">
                            <span>📈</span> Linha do Tempo Cosmológica (1800–2100)
                        </h2>
                        <p class="text-xs text-slate-400">Curva de tensão máxima anual, faixa de controle nulo N3 e índices temáticos.</p>
                    </div>

                    <!-- Range Selector -->
                    <div class="flex flex-wrap items-center gap-1.5 p-1 bg-slate-900 rounded-xl border border-slate-800">
                        <button type="button" onclick="setTimelineRange(1800, 2100, this)" class="chart-btn px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-400 text-slate-950 font-bold">1800–2100</button>
                        <button type="button" onclick="setTimelineRange(1900, 1950, this)" class="chart-btn px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-400 hover:text-white">1900–1950</button>
                        <button type="button" onclick="setTimelineRange(1950, 2000, this)" class="chart-btn px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-400 hover:text-white">1950–2000</button>
                        <button type="button" onclick="setTimelineRange(2000, 2025, this)" class="chart-btn px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-400 hover:text-white">2000–2025</button>
                        <button type="button" onclick="setTimelineRange(2026, 2060, this)" class="chart-btn px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-400 hover:text-white">2026–2060 (Futuro)</button>
                    </div>
                </div>

                <div class="h-80 sm:h-96 w-full">
                    <canvas id="timelineChartCanvas"></canvas>
                </div>
            </div>

            <!-- Charts Section: Categorias & Signos Solares -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="glass-panel p-6 rounded-2xl space-y-4">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span>📊</span> Distribuição dos 3.406 Fatos pelas 6 Categorias Canônicas
                    </h3>
                    <div class="h-64 flex items-center justify-center">
                        <canvas id="categoryDoughnutCanvas"></canvas>
                    </div>
                </div>

                <div class="glass-panel p-6 rounded-2xl space-y-4">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span>☀️</span> Posição do Sol nos 3.406 Grandes Eventos Históricos
                    </h3>
                    <div class="h-64 flex items-center justify-center">
                        <canvas id="sunSignBarCanvas"></canvas>
                    </div>
                </div>
            </div>

            <!-- Resumo Prospectivo dos Picos de Energia (2026–2060) -->
            <div class="glass-panel p-6 sm:p-8 rounded-3xl border border-slate-700/80 shadow-2xl space-y-6">
                <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                    <div>
                        <div class="flex items-center gap-2 mb-1.5">
                            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-400/20 text-amber-300 border border-amber-400/30">⚡ Horizonte 2026–2060</span>
                            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">148 Picos Filtrados</span>
                        </div>
                        <h3 class="font-display text-xl sm:text-2xl font-extrabold text-white">
                            Resumo Prospectivo: Picos de Energia Cósmica & Cenários por País (2026–2060)
                        </h3>
                        <p class="text-xs sm:text-sm text-slate-300 mt-1 max-w-4xl">
                            Síntese cronológica das maiores ativações mundiais e trânsitos nas cartas de fundação das potências soberanas.
                        </p>
                    </div>
                    <button type="button" onclick="switchMainTab('peaks')" class="px-4 py-2 rounded-xl bg-amber-400 text-slate-950 font-bold text-xs transition hover:bg-amber-300 flex items-center gap-1.5 shrink-0">
                        <span>Ver Todos os 148 Picos &rarr;</span>
                    </button>
                </div>

                <!-- Destaques dos Primeiros Picos da Era -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" id="homePeaksPreviewGrid">
                    <!-- Preenchido dinamicamente via JS -->
                </div>
            </div>
        </section>

        <!-- ============================================================= -->
        <!-- TAB 2: CATÁLOGO DE 3.406 FATOS HISTÓRICOS                     -->
        <!-- ============================================================= -->
        <section id="tab-catalog" class="tab-pane hidden space-y-6">
            <!-- Header -->
            <div class="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 class="font-display text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-2">
                            <span>📚</span> Catálogo dos 3.406 Fatos Históricos Mundiais
                        </h2>
                        <p class="text-xs sm:text-sm text-slate-300 mt-1">
                            Base auditada cobrindo de 490 a.C. até 2026 d.C. em 6 eixos canônicos com efemérides suíças completas.
                        </p>
                    </div>
                    <div class="w-full md:w-80 relative">
                        <input type="text" id="catalogSearchInput" placeholder="Buscar por título, país, ano ou consequência..."
                            class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-400 pl-10"
                            onkeyup="filterCatalogEvents()">
                        <span class="absolute left-3.5 top-3 text-slate-400 text-sm">🔍</span>
                    </div>
                </div>

                <!-- Category Pills -->
                <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800" id="catalogCategoryFilters">
                    <button type="button" onclick="setCatalogCategoryFilter('Todas')" class="cat-pill px-3 py-1 rounded-xl text-xs font-bold bg-amber-400 text-slate-950 transition" data-cat="Todas">Todas (3.406)</button>
                    <button type="button" onclick="setCatalogCategoryFilter('Guerra & Conflito')" class="cat-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cat="Guerra & Conflito">⚔️ Guerra & Conflito</button>
                    <button type="button" onclick="setCatalogCategoryFilter('Política, Revoluções & Poder')" class="cat-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cat="Política, Revoluções & Poder">🏛️ Política & Revolução</button>
                    <button type="button" onclick="setCatalogCategoryFilter('Ciência, Tecnologia & Exploração Espacial')" class="cat-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cat="Ciência, Tecnologia & Exploração Espacial">🚀 Ciência & Espaço</button>
                    <button type="button" onclick="setCatalogCategoryFilter('Economia, Crises Financeiras & Mercados')" class="cat-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cat="Economia, Crises Financeiras & Mercados">📉 Economia & Crises</button>
                    <button type="button" onclick="setCatalogCategoryFilter('Cultura, Religião & Filosofia')" class="cat-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cat="Cultura, Religião & Filosofia">📜 Cultura & Religião</button>
                    <button type="button" onclick="setCatalogCategoryFilter('Desastres Naturais, Pandemias & Clima')" class="cat-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cat="Desastres Naturais, Pandemias & Clima">🌊 Desastres & Pandemias</button>
                </div>
            </div>

            <!-- Events Table -->
            <div class="glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
                <div class="overflow-x-auto max-h-[750px]">
                    <table class="w-full text-left text-sm border-collapse" id="catalogTable">
                        <thead class="sticky top-0 bg-slate-900 border-b border-slate-700 text-xs font-bold text-slate-300 uppercase tracking-wider z-10">
                            <tr>
                                <th class="py-3.5 px-4 whitespace-nowrap">Data & ID</th>
                                <th class="py-3.5 px-4 min-w-[240px]">Fato Histórico</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Categoria</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Local / País</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Sol / Lua / Asc</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Tensão</th>
                                <th class="py-3.5 px-3 text-center whitespace-nowrap">Ação</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800" id="catalogTableBody">
                            <!-- Preenchido via Javascript -->
                        </tbody>
                    </table>
                </div>
                <div class="p-3 bg-slate-900 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                    <span id="catalogCountLabel">Carregando eventos...</span>
                    <span>Clique em 'Ver Mapa' para abrir os planetas e aspectos exatos</span>
                </div>
            </div>
        </section>

        <!-- ============================================================= -->
        <!-- TAB 3: PAÍSES SOBERANOS (107 NAÇÕES)                          -->
        <!-- ============================================================= -->
        <section id="tab-countries" class="tab-pane hidden space-y-6">
            <div class="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 class="font-display text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-2">
                            <span>🌐</span> Astrologia Mundana: Nações Soberanas
                        </h2>
                        <p class="text-xs sm:text-sm text-slate-300 mt-1">
                            Catálogo de 107 países com datas de fundação constitucional, coordenadas e trânsitos mundanos.
                        </p>
                    </div>
                    <div class="w-full md:w-80 relative">
                        <input type="text" id="countriesSearchInput" placeholder="Buscar por país, capital ou continente..."
                            class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-400 pl-10"
                            onkeyup="filterCountriesGrid()">
                        <span class="absolute left-3.5 top-3 text-slate-400 text-sm">🔍</span>
                    </div>
                </div>

                <!-- Continent Filter -->
                <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800" id="countriesContinentFilters">
                    <button type="button" onclick="setCountryContinentFilter('Todos')" class="cont-pill px-3 py-1 rounded-xl text-xs font-bold bg-amber-400 text-slate-950 transition" data-cont="Todos">Todos</button>
                    <button type="button" onclick="setCountryContinentFilter('América do Sul')" class="cont-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cont="América do Sul">América do Sul</button>
                    <button type="button" onclick="setCountryContinentFilter('América do Norte')" class="cont-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cont="América do Norte">América do Norte</button>
                    <button type="button" onclick="setCountryContinentFilter('Europa')" class="cont-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cont="Europa">Europa</button>
                    <button type="button" onclick="setCountryContinentFilter('Ásia')" class="cont-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cont="Ásia">Ásia</button>
                    <button type="button" onclick="setCountryContinentFilter('África')" class="cont-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cont="África">África</button>
                    <button type="button" onclick="setCountryContinentFilter('Oceania')" class="cont-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition" data-cont="Oceania">Oceania</button>
                </div>
            </div>

            <!-- Countries Grid -->
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" id="countriesCardsGrid">
                <!-- Preenchido dinamicamente via JS -->
            </div>
        </section>

        <!-- ============================================================= -->
        <!-- TAB 4: PICOS DE ENERGIA CÓSMICA (2026–2060)                   -->
        <!-- ============================================================= -->
        <section id="tab-peaks" class="tab-pane hidden space-y-6">
            <div class="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-400/20 text-amber-300 border border-amber-400/30">⚡ Catálogo Completo</span>
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">Ordem Cronológica</span>
                        </div>
                        <h2 class="font-display text-2xl sm:text-3xl font-extrabold text-white">
                            Picos de Energia Cósmica por País e Mundiais (2026–2060)
                        </h2>
                        <p class="text-xs sm:text-sm text-slate-300 mt-1 max-w-4xl">
                            Varredura cronológica de alta tensão cósmica nos 5 cenários geopolíticos (Conflitos Bélicos, Quebras Econômicas, Crises Institucionais, Comoção Social e Saltos Tecnológicos).
                        </p>
                    </div>
                    <div class="w-full md:w-80 relative">
                        <input type="text" id="peaksTabSearchInput" placeholder="Buscar por ano, país, aspecto ou precedente..."
                            class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-400 pl-10"
                            onkeyup="filterStandalonePeaks()">
                        <span class="absolute left-3.5 top-3 text-slate-400 text-sm">🔍</span>
                    </div>
                </div>

                <!-- Scenario Filters -->
                <div class="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800" id="peaksScenarioFilters">
                    <button type="button" onclick="setStandaloneScenarioFilter('Todos')" class="p-scen-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-amber-400 text-slate-950 transition" data-scen="Todos">Todos os Cenários (148)</button>
                    <button type="button" onclick="setStandaloneScenarioFilter('WAR_CONFLICT')" class="p-scen-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 text-rose-300 hover:text-white transition" data-scen="WAR_CONFLICT">⚔️ Guerra & Conflito (58)</button>
                    <button type="button" onclick="setStandaloneScenarioFilter('REGIME_CRISIS')" class="p-scen-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 text-purple-300 hover:text-white transition" data-scen="REGIME_CRISIS">🏛️ Crise de Poder (45)</button>
                    <button type="button" onclick="setStandaloneScenarioFilter('ECONOMIC_CRASH')" class="p-scen-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 text-amber-300 hover:text-white transition" data-scen="ECONOMIC_CRASH">📉 Quebra Econômica (22)</button>
                    <button type="button" onclick="setStandaloneScenarioFilter('SOCIAL_UPHEAVAL')" class="p-scen-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 text-sky-300 hover:text-white transition" data-scen="SOCIAL_UPHEAVAL">🌊 Comoção Social (15)</button>
                    <button type="button" onclick="setStandaloneScenarioFilter('TECH_INNOVATION')" class="p-scen-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 text-emerald-300 hover:text-white transition" data-scen="TECH_INNOVATION">🚀 Inovação Tecnológica (8)</button>
                </div>
            </div>

            <!-- Peaks Grid -->
            <div class="space-y-4" id="peaksTabCardsStream">
                <!-- Preenchido via Javascript -->
            </div>
        </section>

        <!-- ============================================================= -->
        <!-- TAB 5: CENÁRIOS ANUAIS & PORTAIS SAZONAIS (2027–2060)         -->
        <!-- ============================================================= -->
        <section id="tab-scenarios" class="tab-pane hidden space-y-6">
            <div class="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 class="font-display text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-2">
                            <span>📅</span> Cenários Anuais & Portais Sazonais (2027–2060)
                        </h2>
                        <p class="text-xs sm:text-sm text-slate-300 mt-1">
                            Série ano a ano com percentis calibrados frente à era 1800–2100, dias &gt; P90 e os 4 portais de equinócios/solstícios.
                        </p>
                    </div>
                </div>
            </div>

            <div class="glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
                <div class="overflow-x-auto max-h-[750px]">
                    <table class="w-full text-left text-sm border-collapse" id="scenariosYearTable">
                        <thead class="sticky top-0 bg-slate-900 border-b border-slate-700 text-xs font-bold text-slate-300 uppercase tracking-wider z-10">
                            <tr>
                                <th class="py-3.5 px-4 whitespace-nowrap">Ano & Pico</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Percentil Anual</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Dias &gt; P90</th>
                                <th class="py-3.5 px-4 min-w-[240px]">Configuração Astronômica</th>
                                <th class="py-3.5 px-4 min-w-[240px]">Precedente Histórico</th>
                                <th class="py-3.5 px-6 min-w-[320px]">Síntese do Cenário</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800" id="scenariosTableBody">
                            <!-- Preenchido via Javascript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ============================================================= -->
        <!-- TAB 6: SIMULADOR & LINHA DO TEMPO                             -->
        <!-- ============================================================= -->
        <section id="tab-simulator" class="tab-pane hidden space-y-6">
            <div class="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 class="font-display text-2xl sm:text-3xl font-extrabold text-white flex items-center gap-2">
                            <span>🔮</span> Linha do Tempo Analítica (1800–2100)
                        </h2>
                        <p class="text-xs sm:text-sm text-slate-300 mt-1">
                            Tabela integral dos 301 anos calculados com decomposição em conflito, inovação e concentração de Barbault.
                        </p>
                    </div>
                    <div class="w-full md:w-80 relative">
                        <input type="text" id="simulatorSearchInput" placeholder="Filtrar por ano, gatilho ou evento..."
                            class="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-sm text-white focus:outline-none focus:border-amber-400 pl-10"
                            onkeyup="filterSimulatorTimeline()">
                        <span class="absolute left-3.5 top-3 text-slate-400 text-sm">🔍</span>
                    </div>
                </div>
            </div>

            <div class="glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
                <div class="overflow-x-auto max-h-[750px]">
                    <table class="w-full text-left text-sm border-collapse">
                        <thead class="sticky top-0 bg-slate-900 border-b border-slate-700 text-xs font-bold text-slate-300 uppercase tracking-wider z-10">
                            <tr>
                                <th class="py-3.5 px-4 whitespace-nowrap">Ano</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Tensão Pico</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Risco Bélico</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Inovação</th>
                                <th class="py-3.5 px-4 whitespace-nowrap">Barbault</th>
                                <th class="py-3.5 px-4 min-w-[280px]">Gatilho Cósmico</th>
                                <th class="py-3.5 px-4 min-w-[280px]">Fatos Registrados / Precedente</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800" id="simulatorTableBody">
                            <!-- Preenchido via Javascript -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- ============================================================= -->
        <!-- TAB 7: PREVISÃO PROBABILÍSTICA (2026–2060)                    -->
        <!-- ============================================================= -->
        <section id="tab-forecast" class="tab-pane hidden space-y-6">
            <div class="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
                <div class="flex items-center gap-2">
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Walk-Forward Validado</span>
                    <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-400/20 text-amber-300 border border-amber-400/30">Horizonte 2026–2060</span>
                </div>
                <h2 class="font-display text-2xl sm:text-3xl font-extrabold text-white">
                    Previsão Probabilística & Skill de Modelagem
                </h2>
                <p class="text-xs sm:text-sm text-slate-300 max-w-4xl leading-relaxed">
                    Resultados do backtesting de hindcast fora da amostra (1951–2024). A ciência de previsão exige que qualquer modelo supere a taxa-base histórica com Brier Skill Score positivo e discriminação real.
                </p>
                <div class="text-xs rounded-xl border border-emerald-500/40 bg-emerald-950/20 text-emerald-200 p-3 leading-relaxed">
                    <strong>Regra Epistemológica:</strong> Os modelos mostrados indicam as curvas calculadas pelo modelo regularizado L2 sobre as 409 features celestes, comparadas estritamente à climatologia empírica histórica.
                </div>
            </div>

            <!-- Forecast Targets Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="forecastTargetsGrid">
                <!-- Preenchido dinamicamente via JS -->
            </div>
        </section>

        <!-- ============================================================= -->
        <!-- TAB 8: METODOLOGIA CIENTÍFICA & MODELOS NULOS                 -->
        <!-- ============================================================= -->
        <section id="tab-methodology" class="tab-pane hidden space-y-6">
            <div class="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
                <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                    <span>🔬</span> Governança Científica & Pré-Registro
                </div>
                <h2 class="font-display text-2xl sm:text-3xl font-extrabold text-white">
                    Metodologia, Modelos Nulos & Validação Estatística
                </h2>
                <p class="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-4xl">
                    O AstroHistory foi projetado como uma plataforma aberta de literacia estatística. Toda afirmação de correlação entre alinhamentos astronômicos e história humana foi submetida a baterias formais de hipótese nula com controle de falsas descobertas (FDR Benjamini-Hochberg).
                </p>
            </div>

            <!-- Tabela dos Testes de Hipótese Formais -->
            <div class="glass-panel rounded-2xl overflow-hidden border border-slate-800 shadow-2xl p-6 space-y-4">
                <h3 class="text-lg font-bold text-white flex items-center gap-2">
                    <span>⚖️</span> Resultados Formais dos Testes Pré-Registrados (Amostra Congelada N=59)
                </h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-sm border-collapse">
                        <thead class="bg-slate-900 border-b border-slate-700 text-xs font-bold text-slate-300 uppercase tracking-wider">
                            <tr>
                                <th class="py-3 px-4">Hipótese / Alvo</th>
                                <th class="py-3 px-4">Método Nulo</th>
                                <th class="py-3 px-4">Tensão Observada</th>
                                <th class="py-3 px-4">Média Nula (± DP)</th>
                                <th class="py-3 px-4">Efeito (z-score)</th>
                                <th class="py-3 px-4">p-value</th>
                                <th class="py-3 px-4">Conclusão</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-800 font-mono text-xs">
                            <tr>
                                <td class="py-3 px-4 font-bold text-white font-sans">H1: Geral vs N3 Deslocamento Circular</td>
                                <td class="py-3 px-4 text-slate-400 font-sans">10.000 permutações circulares</td>
                                <td class="py-3 px-4 text-amber-300">481.1 pts</td>
                                <td class="py-3 px-4 text-slate-300">500.6 ± 38.5</td>
                                <td class="py-3 px-4 text-slate-300">-0.506</td>
                                <td class="py-3 px-4 text-slate-300">0.6117</td>
                                <td class="py-3 px-4 text-rose-400 font-bold font-sans">❌ Nulo Não Rejeitado</td>
                            </tr>
                            <tr>
                                <td class="py-3 px-4 font-bold text-white font-sans">H1: Geral vs N2 Controle Estratificado</td>
                                <td class="py-3 px-4 text-slate-400 font-sans">10.000 datas aleatórias por década</td>
                                <td class="py-3 px-4 text-amber-300">481.1 pts</td>
                                <td class="py-3 px-4 text-slate-300">493.9 ± 36.6</td>
                                <td class="py-3 px-4 text-slate-300">-0.350</td>
                                <td class="py-3 px-4 text-slate-300">0.7163</td>
                                <td class="py-3 px-4 text-rose-400 font-bold font-sans">❌ Nulo Não Rejeitado</td>
                            </tr>
                            <tr>
                                <td class="py-3 px-4 font-bold text-white font-sans">H1: Guerras Interestatais (N=15)</td>
                                <td class="py-3 px-4 text-slate-400 font-sans">Permutação temporal</td>
                                <td class="py-3 px-4 text-amber-300">462.1 pts</td>
                                <td class="py-3 px-4 text-slate-300">499.4 ± 73.3</td>
                                <td class="py-3 px-4 text-slate-300">-0.509</td>
                                <td class="py-3 px-4 text-slate-300">0.6163</td>
                                <td class="py-3 px-4 text-rose-400 font-bold font-sans">❌ Nulo Não Rejeitado</td>
                            </tr>
                            <tr>
                                <td class="py-3 px-4 font-bold text-white font-sans">H2: Walk-Forward Fora da Amostra</td>
                                <td class="py-3 px-4 text-slate-400 font-sans">Treino 1800–1950 → Teste 1951–2025</td>
                                <td class="py-3 px-4 text-amber-300">456.5 pts</td>
                                <td class="py-3 px-4 text-slate-300">501.6 ± 53.0</td>
                                <td class="py-3 px-4 text-slate-300">-0.851</td>
                                <td class="py-3 px-4 text-slate-300">0.4008</td>
                                <td class="py-3 px-4 text-rose-400 font-bold font-sans">❌ Sem Transferência Preditiva</td>
                            </tr>
                            <tr>
                                <td class="py-3 px-4 font-bold text-white font-sans">TOST: Teste de Equivalência a Zero</td>
                                <td class="py-3 px-4 text-slate-400 font-sans">Margens de equivalência Δ = ±0.30 DP</td>
                                <td class="py-3 px-4 text-emerald-300">-0.19 DP</td>
                                <td class="py-3 px-4 text-slate-300">Intervalo [-0.30, +0.30]</td>
                                <td class="py-3 px-4 text-emerald-300">t = 1.76</td>
                                <td class="py-3 px-4 text-emerald-300">0.0410</td>
                                <td class="py-3 px-4 text-emerald-400 font-bold font-sans">✅ Estatisticamente Equivalente a Zero</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

    </main>

    <!-- Modal de Detalhes do Evento -->
    <div id="eventModal" class="fixed inset-0 z-50 hidden bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
        <div class="glass-panel w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-3xl p-6 sm:p-8 space-y-6 border border-slate-700/80 shadow-2xl">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                    <span id="modalEventCategory" class="px-2.5 py-0.5 rounded text-xs font-bold font-mono"></span>
                    <h3 id="modalEventTitle" class="text-xl sm:text-2xl font-bold font-display text-white mt-1"></h3>
                    <div id="modalEventMeta" class="text-xs text-slate-400 font-mono mt-1"></div>
                </div>
                <button type="button" onclick="closeEventModal()" class="p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white text-lg font-bold">&times;</button>
            </div>

            <!-- Consequências Históricas -->
            <div>
                <h4 class="text-xs uppercase font-bold text-slate-400 tracking-wider mb-1">Impacto Histórico & Desdobramentos:</h4>
                <p id="modalEventConsequence" class="text-sm text-slate-200 leading-relaxed"></p>
            </div>

            <!-- Tabela dos Planetas na Efeméride -->
            <div>
                <h4 class="text-xs uppercase font-bold text-amber-300 tracking-wider mb-2">Posições Planetárias Exatas (Swiss Ephemeris):</h4>
                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 text-xs font-mono" id="modalEventPlanets"></div>
            </div>

            <!-- Aspectos e Estrelas -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-800">
                <div>
                    <h4 class="text-xs uppercase font-bold text-rose-300 tracking-wider mb-2">Aspectos Maiores Exatos:</h4>
                    <div class="space-y-1.5 text-xs font-mono" id="modalEventAspects"></div>
                </div>
                <div>
                    <h4 class="text-xs uppercase font-bold text-sky-300 tracking-wider mb-2">Estrelas Fixas Conectadas (Orbe ≤ 0.3°):</h4>
                    <div class="space-y-1.5 text-xs font-mono" id="modalEventStars"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modal de Detalhes do País -->
    <div id="countryModal" class="fixed inset-0 z-50 hidden bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
        <div class="glass-panel w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-3xl p-6 sm:p-8 space-y-6 border border-slate-700/80 shadow-2xl">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                <div class="flex items-center gap-3">
                    <span id="modalCountryFlag" class="text-4xl"></span>
                    <div>
                        <h3 id="modalCountryName" class="text-2xl font-bold font-display text-white"></h3>
                        <div id="modalCountryCapital" class="text-xs text-slate-400 font-mono"></div>
                    </div>
                </div>
                <button type="button" onclick="closeCountryModal()" class="p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white text-lg font-bold">&times;</button>
            </div>

            <div>
                <h4 class="text-xs uppercase font-bold text-amber-300 tracking-wider mb-1">Certidão de Fundação / Independência:</h4>
                <div id="modalCountryFoundation" class="text-sm text-slate-200"></div>
                <div id="modalCountryCoords" class="text-xs text-slate-400 font-mono mt-1"></div>
            </div>

            <div>
                <h4 class="text-xs uppercase font-bold text-slate-400 tracking-wider mb-1">Justificativa Historiográfica:</h4>
                <p id="modalCountryJustification" class="text-xs sm:text-sm text-slate-300 leading-relaxed"></p>
            </div>
        </div>
    </div>

    <!-- Global Footer -->
    <footer class="glass-panel border-t border-slate-800/80 py-8 px-4 sm:px-8 mt-16 text-center text-xs text-slate-400">
        <div class="max-w-[1920px] mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="text-left">
                <div class="flex items-center gap-2">
                    <span class="font-display font-bold text-white tracking-wider">AstroHistory</span>
                    <span class="text-xs text-slate-500 font-mono">• v5.0.0 Static Edition</span>
                </div>
                <p class="text-slate-400 mt-1">
                    Plataforma Standalone de Pesquisa Computacional em Astrologia Mundana & Ephemerides Suíças.
                </p>
            </div>
            <div class="flex flex-wrap items-center gap-4 font-mono text-xs">
                <span>3.406 Fatos Catalogados</span>
                <span>•</span>
                <span>148 Picos (2026–2060)</span>
                <span>•</span>
                <span>107 Países Soberanos</span>
            </div>
        </div>
        <div class="max-w-[1920px] mx-auto mt-4 pt-4 border-t border-slate-800/60 text-[11px] text-slate-500 text-center">
            Swiss Ephemeris &copy; Astrodienst AG • Licenciado sob GNU AGPL-3.0-or-later • Pronto para GitHub Pages e Servidores Estáticos
        </div>
    </footer>

    <!-- INJEÇÃO DO BUNDLE DE DADOS EM JAVASCRIPT -->
    <script>
        window.ASTRO_DATA = {bundle_json};
    </script>

    <!-- MOTOR REATIVO CLIENT-SIDE (ZERO BACKEND) -->
    <script>
        // State
        let currentTab = 'dashboard';
        let currentLang = localStorage.getItem('astro_lang') || 'pt';
        let currentTheme = localStorage.getItem('astro_theme') || 'light';

        let catalogActiveCat = 'Todas';
        let countryActiveCont = 'Todos';
        let peakActiveScen = 'Todos';

        let timelineChart = null;

        // Theme management
        function setAppTheme(theme) {{
            currentTheme = theme;
            localStorage.setItem('astro_theme', theme);
            const doc = document.documentElement;
            doc.classList.remove('theme-light', 'theme-dark', 'theme-oled');
            doc.classList.add('theme-' + theme);
            if (theme === 'light') doc.classList.remove('dark'); else doc.classList.add('dark');

            document.querySelectorAll('.theme-btn').forEach(btn => {{
                if (btn.getAttribute('data-theme') === theme) {{
                    btn.classList.add('bg-amber-400', 'text-slate-950', 'font-bold');
                }} else {{
                    btn.classList.remove('bg-amber-400', 'text-slate-950', 'font-bold');
                }}
            }});
            if (timelineChart) timelineChart.update('none');
        }}

        // Lang management
        function setAppLang(lang) {{
            currentLang = lang;
            localStorage.setItem('astro_lang', lang);
            document.querySelectorAll('.lang-btn').forEach(btn => {{
                if (btn.getAttribute('data-lang') === lang) {{
                    btn.classList.add('bg-amber-400', 'text-slate-950', 'font-bold');
                    btn.classList.remove('text-slate-400');
                }} else {{
                    btn.classList.remove('bg-amber-400', 'text-slate-950', 'font-bold');
                    btn.classList.add('text-slate-400');
                }}
            }});
        }}

        // Tab switcher
        function switchMainTab(tab) {{
            currentTab = tab;
            document.querySelectorAll('.tab-pane').forEach(el => el.classList.add('hidden'));
            const target = document.getElementById('tab-' + tab);
            if (target) target.classList.remove('hidden');

            document.querySelectorAll('.nav-tab-btn').forEach(btn => {{
                if (btn.getAttribute('data-tab') === tab) {{
                    btn.className = "nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 bg-amber-400 text-slate-950 shadow-sm";
                }} else {{
                    btn.className = "nav-tab-btn px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800/80 transition flex items-center gap-1.5";
                }}
            }});

            window.scrollTo({{ top: 0, behavior: 'smooth' }});

            if (tab === 'dashboard' && timelineChart) {{
                setTimeout(() => timelineChart.resize(), 50);
            }}
        }}

        function toggleMobileNav() {{
            const m = document.getElementById('nav-mobile');
            if (m) m.classList.toggle('hidden');
        }}

        // Initial setup on DOM Ready
        document.addEventListener('DOMContentLoaded', () => {{
            setAppTheme(currentTheme);
            setAppLang(currentLang);

            initDashboardCharts();
            renderHomePeaksPreview();
            renderCatalogTable();
            renderCountriesGrid();
            renderStandalonePeaks();
            renderScenariosTable();
            renderSimulatorTimeline();
            renderForecastTargets();
        }});

        // --- DASHBOARD CHARTS ---
        function initDashboardCharts() {{
            const tl = window.ASTRO_DATA.timeline;
            const years = tl.map(y => y.year);
            const peakTension = tl.map(y => y.peak);
            const conflict = tl.map(y => y.conflict);
            const tech = tl.map(y => y.tech);
            const barbault = tl.map(y => y.barbault);

            const ctx = document.getElementById('timelineChartCanvas')?.getContext('2d');
            if (!ctx) return;

            timelineChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: years,
                    datasets: [
                        {{
                            label: 'Tensão Cósmica de Pico (0–1000)',
                            data: peakTension,
                            borderColor: '#f43f5e',
                            backgroundColor: 'rgba(244, 63, 94, 0.1)',
                            borderWidth: 2,
                            tension: 0.25,
                            pointRadius: 2,
                            fill: false
                        }},
                        {{
                            label: 'Faixa de Controle Nulo N3 (P5–P95)',
                            data: years.map(() => 564.0),
                            borderColor: 'rgba(148, 163, 184, 0.35)',
                            borderWidth: 1,
                            borderDash: [5, 5],
                            pointRadius: 0,
                            fill: '+1',
                            backgroundColor: 'rgba(148, 163, 184, 0.08)'
                        }},
                        {{
                            label: 'Controle Nulo Inferior (P5)',
                            data: years.map(() => 437.0),
                            borderColor: 'rgba(148, 163, 184, 0.35)',
                            borderWidth: 1,
                            borderDash: [5, 5],
                            pointRadius: 0,
                            fill: false
                        }},
                        {{
                            label: 'Risco Bélico (0–1000)',
                            data: conflict,
                            borderColor: '#fbbf24',
                            borderWidth: 1.5,
                            pointRadius: 1,
                            fill: false
                        }},
                        {{
                            label: 'Inovação Científica (0–1000)',
                            data: tech,
                            borderColor: '#38bdf8',
                            borderWidth: 1.5,
                            borderDash: [4, 4],
                            pointRadius: 1,
                            fill: false
                        }},
                        {{
                            label: 'Concentração Planetária — Barbault (0–1000)',
                            data: barbault,
                            borderColor: '#a855f7',
                            borderWidth: 1.5,
                            pointRadius: 1,
                            fill: false
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ display: false }} }},
                        y: {{ min: 0, max: 1000, ticks: {{ color: '#94a3b8', stepSize: 200 }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
                    }},
                    plugins: {{
                        legend: {{ position: 'bottom', labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }}
                    }}
                }}
            }});

            // Categorias Doughnut
            const catCtx = document.getElementById('categoryDoughnutCanvas')?.getContext('2d');
            if (catCtx) {{
                const catData = window.ASTRO_DATA.stats.categories;
                new Chart(catCtx, {{
                    type: 'doughnut',
                    data: {{
                        labels: catData.map(c => c.category),
                        datasets: [{{
                            data: catData.map(c => c.cnt),
                            backgroundColor: ['#f43f5e', '#fbbf24', '#38bdf8', '#a855f7', '#34d399', '#f97316'],
                            borderWidth: 0
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{ legend: {{ position: 'right', labels: {{ color: '#94a3b8', font: {{ size: 11 }} }} }} }}
                    }}
                }});
            }}

            // Sun Signs Bar
            const sunCtx = document.getElementById('sunSignBarCanvas')?.getContext('2d');
            if (sunCtx) {{
                const sunData = window.ASTRO_DATA.stats.sun_signs_distribution;
                new Chart(sunCtx, {{
                    type: 'bar',
                    data: {{
                        labels: sunData.map(s => s.sun_sign),
                        datasets: [{{
                            label: 'Ocorrências nos 3.406 Fatos',
                            data: sunData.map(s => s.cnt),
                            backgroundColor: 'rgba(251, 191, 36, 0.75)',
                            borderRadius: 4
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ display: false }} }},
                            y: {{ ticks: {{ color: '#94a3b8', stepSize: 20 }}, grid: {{ color: 'rgba(255,255,255,0.05)' }} }}
                        }},
                        plugins: {{ legend: {{ display: false }} }}
                    }}
                }});
            }}
        }}

        function setTimelineRange(start, end, btn) {{
            document.querySelectorAll('.chart-btn').forEach(b => {{
                b.className = "chart-btn px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-400 hover:text-white";
            }});
            if (btn) btn.className = "chart-btn px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-400 text-slate-950 font-bold";

            const tl = window.ASTRO_DATA.timeline.filter(y => y.year >= start && y.year <= end);
            timelineChart.data.labels = tl.map(y => y.year);
            timelineChart.data.datasets[0].data = tl.map(y => y.peak);
            timelineChart.data.datasets[1].data = tl.map(() => 564.0);
            timelineChart.data.datasets[2].data = tl.map(() => 437.0);
            timelineChart.data.datasets[3].data = tl.map(y => y.conflict);
            timelineChart.data.datasets[4].data = tl.map(y => y.tech);
            timelineChart.data.datasets[5].data = tl.map(y => y.barbault);
            timelineChart.update();
        }}

        // Home Peaks Preview
        function renderHomePeaksPreview() {{
            const container = document.getElementById('homePeaksPreviewGrid');
            if (!container) return;
            const peaks = window.ASTRO_DATA.peaks.peaks.slice(0, 6);
            container.innerHTML = peaks.map(p => `
                <div class="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2 hover:border-amber-400/40 transition">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-1.5">
                            <span class="font-display font-black text-lg text-white">${{p.year}}</span>
                            <span class="text-[11px] font-mono text-slate-400">(${{p.peak_date}})</span>
                        </div>
                        <span class="px-2 py-0.5 rounded text-[10px] font-bold font-mono ${{p.alert_level === 'Crítico' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'}}">${{p.alert_level}}</span>
                    </div>
                    <div class="flex items-center gap-1.5">
                        <span class="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-200 font-semibold">${{p.country_flag}} ${{p.country_name_pt}}</span>
                        <span class="px-2 py-0.5 rounded text-[11px] font-bold ${{p.badge_class}}">${{p.scenario_icon}} ${{p.scenario_label_pt}}</span>
                    </div>
                    <div class="text-xs font-mono text-amber-300 font-bold">${{p.cosmic_signature}}</div>
                    <p class="text-xs text-slate-400 line-clamp-2 leading-relaxed">${{p.prospective_synthesis}}</p>
                    <div class="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px]">
                        <span class="text-slate-500 font-mono">Precedente: <strong class="text-slate-300">${{p.historical_precedent_year}}</strong></span>
                        <span class="font-mono font-bold text-amber-300">${{p.energy_score_1000}}/1000</span>
                    </div>
                </div>
            `).join('');
        }}

        // --- CATALOG TABLE ---
        function renderCatalogTable() {{
            const tbody = document.getElementById('catalogTableBody');
            if (!tbody) return;
            const query = (document.getElementById('catalogSearchInput')?.value || '').toLowerCase().trim();

            const filtered = window.ASTRO_DATA.events.filter(ev => {{
                const matchCat = (catalogActiveCat === 'Todas' || ev.category === catalogActiveCat);
                const matchQuery = (!query || ev.title.toLowerCase().includes(query) || (ev.country && ev.country.toLowerCase().includes(query)) || String(ev.date).includes(query));
                return matchCat && matchQuery;
            }});

            const displayList = filtered.slice(0, 100); // Primeiros 100 para fluidez máxima
            tbody.innerHTML = displayList.map(ev => `
                <tr class="hover:bg-slate-800/60 transition">
                    <td class="py-3 px-4 font-mono text-xs whitespace-nowrap">
                        <div class="font-bold text-white">${{ev.date}}</div>
                        <div class="text-slate-500 text-[10px]">#${{ev.id}} • ${{ev.time}}</div>
                    </td>
                    <td class="py-3 px-4">
                        <div class="font-bold text-white">${{ev.title}}</div>
                        <div class="text-xs text-slate-400 line-clamp-1">${{ev.consequence || ''}}</div>
                    </td>
                    <td class="py-3 px-4 whitespace-nowrap">
                        <span class="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 border border-slate-700 text-slate-300">${{ev.category}}</span>
                    </td>
                    <td class="py-3 px-4 whitespace-nowrap text-xs text-slate-300">
                        ${{ev.city ? ev.city + ', ' : ''}}${{ev.country || ''}}
                    </td>
                    <td class="py-3 px-4 font-mono text-xs whitespace-nowrap">
                        <span class="text-amber-300 font-semibold">☉ ${{ev.sun}}</span>
                        <span class="text-slate-400 ml-1">☽ ${{ev.moon}}</span>
                    </td>
                    <td class="py-3 px-4 font-mono text-xs font-bold text-rose-300 whitespace-nowrap">
                        ${{ev.tension}}
                    </td>
                    <td class="py-3 px-3 text-center whitespace-nowrap">
                        <button type="button" onclick="openEventModal(${{ev.id}})" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-300 text-xs font-semibold border border-slate-700 transition">
                            Ver Mapa
                        </button>
                    </td>
                </tr>
            `).join('');

            const label = document.getElementById('catalogCountLabel');
            if (label) label.innerText = `Exibindo ${{displayList.length}} de ${{filtered.length}} eventos (${{window.ASTRO_DATA.events.length}} no total)`;
        }}

        function setCatalogCategoryFilter(cat) {{
            catalogActiveCat = cat;
            document.querySelectorAll('.cat-pill').forEach(btn => {{
                if (btn.getAttribute('data-cat') === cat) {{
                    btn.className = "cat-pill px-3 py-1 rounded-xl text-xs font-bold bg-amber-400 text-slate-950 transition";
                }} else {{
                    btn.className = "cat-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition";
                }}
            }});
            renderCatalogTable();
        }}

        function filterCatalogEvents() {{
            renderCatalogTable();
        }}

        function openEventModal(id) {{
            const ev = window.ASTRO_DATA.events.find(e => e.id === id);
            if (!ev) return;

            document.getElementById('modalEventTitle').innerText = ev.title;
            document.getElementById('modalEventCategory').innerText = ev.category;
            document.getElementById('modalEventMeta').innerText = `${{ev.date}} às ${{ev.time}} • ${{ev.city}}, ${{ev.country}} • Tensão Cósmica: ${{ev.tension}}/100`;
            document.getElementById('modalEventConsequence').innerText = ev.consequence || 'Sem desdobramentos adicionais registrados.';

            const plContainer = document.getElementById('modalEventPlanets');
            plContainer.innerHTML = (ev.planets || []).map(p => `
                <div class="p-2 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
                    <span class="text-amber-300 font-bold">${{p.sym}} ${{p.name}}</span>
                    <span class="text-slate-300">${{p.deg}}</span>
                </div>
            `).join('');

            const aspContainer = document.getElementById('modalEventAspects');
            aspContainer.innerHTML = (ev.aspects || []).map(a => `
                <div class="flex items-center justify-between text-xs py-1 border-b border-slate-800">
                    <span>${{a.p1}} ${{a.p1_name}} ${{a.asp}} ${{a.p2}} ${{a.p2_name}}</span>
                    <span class="text-slate-400">orbe ${{a.orb}}°</span>
                </div>
            `).join('') || '<div class="text-slate-500">Sem aspectos maiores com orbe estrito</div>';

            const starContainer = document.getElementById('modalEventStars');
            starContainer.innerHTML = (ev.stars || []).map(s => `
                <div class="flex items-center justify-between text-xs py-1 border-b border-slate-800">
                    <span class="text-sky-300 font-bold">★ ${{s.star}} ☌ ${{s.planet}}</span>
                    <span class="text-slate-400">orbe ${{s.orb}}°</span>
                </div>
            `).join('') || '<div class="text-slate-500">Sem conjunções exatas com estrelas fixas</div>';

            document.getElementById('eventModal').classList.remove('hidden');
        }}

        function closeEventModal() {{
            document.getElementById('eventModal').classList.add('hidden');
        }}

        // --- COUNTRIES GRID ---
        function renderCountriesGrid() {{
            const grid = document.getElementById('countriesCardsGrid');
            if (!grid) return;
            const query = (document.getElementById('countriesSearchInput')?.value || '').toLowerCase().trim();

            const filtered = window.ASTRO_DATA.countries.filter(c => {{
                const matchCont = (countryActiveCont === 'Todos' || c.continent === countryActiveCont);
                const matchQuery = (!query || c.name_pt.toLowerCase().includes(query) || (c.capital && c.capital.toLowerCase().includes(query)));
                return matchCont && matchQuery;
            }});

            grid.innerHTML = filtered.map(c => `
                <div class="p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-amber-400/50 transition flex flex-col justify-between space-y-3">
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-3xl">${{c.flag_emoji || '🏳️'}}</span>
                            <span class="text-xs font-mono font-bold text-amber-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">${{c.iso_code}}</span>
                        </div>
                        <h4 class="font-bold text-base text-white">${{c.name_pt}}</h4>
                        <div class="text-xs text-slate-400 font-mono">${{c.capital || ''}} • ${{c.continent}}</div>
                        <div class="text-xs text-slate-300 mt-2 line-clamp-2">${{c.foundation_event || 'Fundação Histórica'}} (${{c.date}})</div>
                    </div>
                    <button type="button" onclick="openCountryModal('${{c.iso_code}}')" class="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-sky-300 text-xs font-semibold border border-slate-700 transition">
                        Ver Certidão de Fundação
                    </button>
                </div>
            `).join('');
        }}

        function setCountryContinentFilter(cont) {{
            countryActiveCont = cont;
            document.querySelectorAll('.cont-pill').forEach(btn => {{
                if (btn.getAttribute('data-cont') === cont) {{
                    btn.className = "cont-pill px-3 py-1 rounded-xl text-xs font-bold bg-amber-400 text-slate-950 transition";
                }} else {{
                    btn.className = "cont-pill px-3 py-1 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition";
                }}
            }});
            renderCountriesGrid();
        }}

        function filterCountriesGrid() {{
            renderCountriesGrid();
        }}

        function openCountryModal(iso) {{
            const c = window.ASTRO_DATA.countries.find(x => x.iso_code === iso);
            if (!c) return;
            document.getElementById('modalCountryFlag').innerText = c.flag_emoji || '🏳️';
            document.getElementById('modalCountryName').innerText = `${{c.name_pt}} (${{c.iso_code}})`;
            document.getElementById('modalCountryCapital').innerText = `Capital: ${{c.capital || 'N/A'}} • ${{c.continent}}`;
            document.getElementById('modalCountryFoundation').innerText = `${{c.foundation_event || 'Momento de Fundação'}} • Data: ${{c.date}} às ${{c.time || '12:00'}}`;
            document.getElementById('modalCountryCoords').innerText = `Coordenadas: Lat ${{c.latitude}}, Long ${{c.longitude}}`;
            document.getElementById('modalCountryJustification').innerText = c.historical_justification || 'Certidão de fundação baseada na historiografia nacional e documentação constitucional.';
            document.getElementById('countryModal').classList.remove('hidden');
        }}

        function closeCountryModal() {{
            document.getElementById('countryModal').classList.add('hidden');
        }}

        // --- PICOS DE ENERGIA TAB ---
        function renderStandalonePeaks() {{
            const container = document.getElementById('peaksTabCardsStream');
            if (!container) return;
            const query = (document.getElementById('peaksTabSearchInput')?.value || '').toLowerCase().trim();

            const filtered = window.ASTRO_DATA.peaks.peaks.filter(p => {{
                const matchScen = (peakActiveScen === 'Todos' || p.scenario_key === peakActiveScen);
                const matchQuery = (!query || String(p.year).includes(query) || p.country_name_pt.toLowerCase().includes(query) || p.cosmic_signature.toLowerCase().includes(query) || p.historical_precedent_title.toLowerCase().includes(query));
                return matchScen && matchQuery;
            }});

            container.innerHTML = filtered.map(p => `
                <div class="p-5 sm:p-6 rounded-2xl bg-slate-900 border ${{p.alert_level === 'Crítico' ? 'border-rose-500/40 bg-rose-950/10' : 'border-amber-500/40 bg-amber-950/10'}} space-y-4">
                    <div class="flex flex-wrap items-center justify-between gap-3">
                        <div class="flex items-center gap-2">
                            <span class="text-2xl font-black font-display text-white">${{p.year}}</span>
                            <span class="text-xs font-mono text-slate-400">(${{p.peak_date}})</span>
                            <span class="px-2.5 py-0.5 rounded-lg bg-slate-800 text-xs font-semibold text-slate-200 border border-slate-700">${{p.country_flag}} ${{p.country_name_pt}}</span>
                            <span class="px-2.5 py-0.5 rounded-lg border text-xs font-bold ${{p.badge_class}}">${{p.scenario_icon}} ${{p.scenario_label_pt}}</span>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="font-mono text-lg font-black ${{p.alert_level === 'Crítico' ? 'text-rose-300' : 'text-amber-300'}}">${{p.energy_score_1000}}/1000</span>
                            <span class="px-2 py-0.5 rounded text-xs font-bold font-mono uppercase ${{p.alert_level === 'Crítico' ? 'bg-rose-500/20 text-rose-300 border border-rose-500/50' : 'bg-amber-500/20 text-amber-300 border border-amber-500/50'}}">🚨 ${{p.alert_level}}</span>
                        </div>
                    </div>
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-3 text-xs">
                        <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                            <div class="text-[11px] font-bold text-slate-400 uppercase">🪐 Assinatura Astrológica:</div>
                            <div class="font-mono font-bold text-amber-300 mt-1">${{p.cosmic_signature}}</div>
                            <div class="text-slate-400 mt-0.5">${{p.cosmic_signature_detail || ''}}</div>
                        </div>
                        <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                            <div class="text-[11px] font-bold text-slate-400 uppercase">🏛️ Precedente Histórico:</div>
                            <div class="font-bold text-sky-300 mt-1">${{p.historical_precedent_title}}</div>
                            <div class="text-slate-400 mt-0.5">${{p.historical_precedent_summary || ''}}</div>
                        </div>
                        <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800">
                            <div class="text-[11px] font-bold text-slate-400 uppercase">🔮 Tendência do Cenário:</div>
                            <div class="text-slate-200 mt-1 leading-relaxed">${{p.prospective_synthesis}}</div>
                        </div>
                    </div>
                </div>
            `).join('');
        }}

        function setStandaloneScenarioFilter(scen) {{
            peakActiveScen = scen;
            document.querySelectorAll('.p-scen-btn').forEach(btn => {{
                if (btn.getAttribute('data-scen') === scen) {{
                    btn.className = "p-scen-btn px-3 py-1.5 rounded-xl text-xs font-bold bg-amber-400 text-slate-950 transition";
                }} else {{
                    btn.className = "p-scen-btn px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:text-white transition";
                }}
            }});
            renderStandalonePeaks();
        }}

        function filterStandalonePeaks() {{
            renderStandalonePeaks();
        }}

        // --- SCENARIOS TABLE ---
        function renderScenariosTable() {{
            const tbody = document.getElementById('scenariosTableBody');
            if (!tbody) return;
            const proj = window.ASTRO_DATA.projections.projections || [];
            tbody.innerHTML = proj.map(p => `
                <tr class="hover:bg-slate-800/60 transition">
                    <td class="py-3 px-4 font-mono font-bold text-white whitespace-nowrap">
                        ${{p.year}} <span class="text-xs text-slate-400 font-normal">(${{p.peak_date}})</span>
                    </td>
                    <td class="py-3 px-4 font-mono font-bold whitespace-nowrap" style="color: ${{p.tier_color}};">
                        ${{p.annual_percentile_1000}}/1000 (${{p.tier_label}})
                    </td>
                    <td class="py-3 px-4 font-mono text-xs whitespace-nowrap">
                        ${{p.days_above_p90}} dias
                    </td>
                    <td class="py-3 px-4 text-xs font-mono text-amber-300">
                        ${{p.cosmic_trigger}}
                    </td>
                    <td class="py-3 px-4 text-xs text-sky-300 font-bold">
                        ${{p.top_precedent ? p.top_precedent.title + ' (' + p.top_precedent.year + ')' : ''}}
                    </td>
                    <td class="py-3 px-6 text-xs text-slate-300 leading-relaxed">
                        ${{p.scenarios_and_possibilities}}
                    </td>
                </tr>
            `).join('');
        }}

        // --- SIMULATOR TIMELINE ---
        function renderSimulatorTimeline() {{
            const tbody = document.getElementById('simulatorTableBody');
            if (!tbody) return;
            const query = (document.getElementById('simulatorSearchInput')?.value || '').toLowerCase().trim();

            const tl = window.ASTRO_DATA.timeline.filter(y => {{
                return (!query || String(y.year).includes(query) || y.trigger.toLowerCase().includes(query) || (y.top_event && y.top_event.toLowerCase().includes(query)));
            }});

            tbody.innerHTML = tl.slice(0, 150).map(y => `
                <tr class="hover:bg-slate-800/60 transition">
                    <td class="py-3 px-4 font-mono font-bold text-white whitespace-nowrap">
                        ${{y.year}} ${{y.is_hist ? '<span class=\"text-[10px] px-1.5 py-0.5 rounded bg-amber-400/20 text-amber-300\">Fato</span>' : '<span class=\"text-[10px] px-1.5 py-0.5 rounded bg-sky-400/20 text-sky-300\">Futuro</span>'}}
                    </td>
                    <td class="py-3 px-4 font-mono font-bold text-rose-300 whitespace-nowrap">${{y.peak}}</td>
                    <td class="py-3 px-4 font-mono text-amber-300 whitespace-nowrap">${{y.conflict}}</td>
                    <td class="py-3 px-4 font-mono text-sky-300 whitespace-nowrap">${{y.tech}}</td>
                    <td class="py-3 px-4 font-mono text-purple-300 whitespace-nowrap">${{y.barbault}}</td>
                    <td class="py-3 px-4 text-xs font-mono text-slate-300">${{y.trigger}}</td>
                    <td class="py-3 px-4 text-xs text-slate-200">${{y.top_event ? y.top_event + ' (' + y.top_year + ')' : 'Alinhamento geral'}}</td>
                </tr>
            `).join('');
        }}

        function filterSimulatorTimeline() {{
            renderSimulatorTimeline();
        }}

        // --- FORECAST TARGETS ---
        function renderForecastTargets() {{
            const grid = document.getElementById('forecastTargetsGrid');
            if (!grid) return;
            const targets = window.ASTRO_DATA.forecast.targets || {{}};

            grid.innerHTML = Object.entries(targets).map(([k, t]) => `
                <div class="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                    <div class="flex items-center justify-between border-b border-slate-800 pb-3">
                        <h4 class="font-bold text-base text-white">${{t.label}}</h4>
                        <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold ${{t.skill.verdict.includes('Sem skill') ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}}">
                            ${{t.skill.verdict}}
                        </span>
                    </div>
                    <div class="space-y-2 text-xs font-mono">
                        <div class="flex justify-between text-slate-400">
                            <span>Brier Skill Score (BSS):</span>
                            <strong class="text-white">${{t.skill.bss}}</strong>
                        </div>
                        <div class="flex justify-between text-slate-400">
                            <span>ROC AUC:</span>
                            <strong class="text-white">${{t.skill.auc}}</strong>
                        </div>
                        <div class="flex justify-between text-slate-400">
                            <span>Taxa-Base Histórica:</span>
                            <strong class="text-amber-300">${{t.base_rate_pct}}% ao mês</strong>
                        </div>
                        <div class="flex justify-between text-slate-400">
                            <span>Modelo Utilizado:</span>
                            <span class="text-slate-300 font-sans">${{t.model}}</span>
                        </div>
                    </div>
                    <p class="text-xs text-slate-400 pt-2 border-t border-slate-800 leading-relaxed">
                        ${{t.narrative || 'Previsão probabilística anual calibrada contra climatologia histórica.'}}
                    </p>
                </div>
            `).join('');
        }}
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    build_standalone()
