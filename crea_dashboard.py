import os
import glob
import csv
import json
from collections import defaultdict

# --- CONFIGURAZIONE ---
CARTELLA_BASE = '.'
NOME_FILE_OUTPUT = 'Dashboard_AlmaLaurea.html'

def parse_csv_perfetto(filepath):
    """Motore di estrazione basato sui marcatori grezzi di AlmaLaurea"""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        rows = list(csv.reader(f))
    
    data_points = []
    current_section = "Dati Generali"
    current_question = "Generale"
    current_subgroup = "Dati"

    for i in range(len(rows)):
        row = rows[i]
        if len(row) == 0: continue
        
        col0_raw = row[0]
        col1_raw = row[1] if len(row) > 1 else ""
        
        has_marker_in_name = 'Â' in col0_raw or '\xa0' in col0_raw
        has_marker_in_value = 'Â' in col1_raw or '\xa0' in col1_raw
        
        col0_clean = col0_raw.replace('Â', '').replace('\xa0', '').strip()
        col1_clean = col1_raw.replace('Â', '').replace('\xa0', '').strip()
        
        if not col0_clean: continue

        is_next_empty = False
        if i + 1 < len(rows):
            next_row = rows[i+1]
            if len(next_row) == 0 or not next_row[0].strip():
                is_next_empty = True

        if is_next_empty:
            current_section = col0_clean
            current_question = "Dati Generali"
            current_subgroup = "Dati"
            continue

        is_numeric = False
        val_num = None
        if col1_clean:
            try:
                val_num = float(col1_clean.replace(',', '.'))
                is_numeric = True
            except ValueError:
                if col1_clean == '-':
                    val_num = 0.0
                    is_numeric = True

        is_header = False
        if not is_numeric:
            is_header = True
        elif has_marker_in_name or has_marker_in_value:
            is_header = True
        else:
            name_lower = col0_clean.lower()
            if "(%)" in name_lower or "(medie" in name_lower or "(per 100" in name_lower:
                is_header = True

        if is_header:
            if ":" in col0_clean:
                parts = col0_clean.split(":", 1)
                current_question = parts[0].strip()
                current_subgroup = parts[1].strip()
            else:
                current_question = col0_clean
                current_subgroup = "Dati"
                
            if is_numeric:
                data_points.append({
                    'Sezione': current_section,
                    'Domanda': current_question,
                    'Sottogruppo': current_subgroup,
                    'Voce': 'Valore Globale',
                    'Valore': val_num
                })
            continue

        if is_numeric:
            data_points.append({
                'Sezione': current_section,
                'Domanda': current_question,
                'Sottogruppo': current_subgroup,
                'Voce': col0_clean,
                'Valore': val_num
            })
            
    return data_points

def main():
    print("🚀 Scansione, decodifica e creazione raggruppamenti in corso...")
    
    db = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))))
    anni_set, atenei_set = set(), set()
    
    files = glob.glob(os.path.join(CARTELLA_BASE, "**/*.csv"), recursive=True)
    for f in files:
        try:
            fname = os.path.basename(f)
            ateneo, anno = os.path.splitext(fname)[0].rsplit('-', 1)
            anno = int(anno)
            atenei_set.add(ateneo.upper())
            anni_set.add(anno)
            
            punti = parse_csv_perfetto(f)
            for p in punti:
                db[p['Sezione']][p['Domanda']][p['Sottogruppo']][p['Voce']][ateneo.upper()][anno] = p['Valore']
        except Exception as e:
            pass

    if not anni_set:
        print("❌ Errore: Nessun CSV trovato. Assicurati che i file si chiamino 'ateneo-anno.csv'.")
        return

    anni_list = sorted(list(anni_set))
    atenei_list = sorted(list(atenei_set))

    js_data = {}
    for sez, dom_dict in db.items():
        js_data[sez] = {}
        for dom, sg_dict in dom_dict.items():
            js_data[sez][dom] = {}
            for sg, voce_dict in sg_dict.items():
                js_data[sez][dom][sg] = {}
                for voce, a_dict in voce_dict.items():
                    js_data[sez][dom][sg][voce] = {}
                    for ateneo in atenei_list:
                        history = [a_dict.get(ateneo, {}).get(anno, None) for anno in anni_list]
                        if any(v is not None for v in history):
                            js_data[sez][dom][sg][voce][ateneo] = history

    html_template = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>AlmaLaurea Executive Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
        <style>
            :root {{ --primary: #0f172a; --accent: #2563eb; --bg: #f8fafc; --panel: #ffffff; }}
            body {{ font-family: 'Inter', system-ui, sans-serif; margin: 0; display: flex; height: 100vh; background: var(--bg); overflow: hidden; }}
            
            #sidebar {{ width: 360px; background: var(--panel); border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; overflow-y: auto; flex-shrink: 0; }}
            .sidebar-header {{ background: var(--primary); color: white; padding: 25px; font-weight: bold; text-align: center; font-size: 1.2rem; position: sticky; top: 0; z-index: 10; }}
            
            .special-section {{ padding: 15px 0; background: #eff6ff; border-bottom: 2px solid #bfdbfe; }}
            .special-btn {{ padding: 14px 25px; cursor: pointer; font-size: 1rem; font-weight: 800; color: #1e40af; border-left: 4px solid transparent; transition: 0.2s; display: flex; align-items: center; gap: 10px; }}
            .special-btn:hover, .special-btn.active {{ background: #dbeafe; border-left-color: #2563eb; }}

            .section-box {{ border-bottom: 1px solid #f1f5f9; }}
            .section-title {{ padding: 12px 20px; background: #f1f5f9; font-weight: 800; font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; position: sticky; top: 73px; z-index: 5; }}
            
            .question-item {{ padding: 12px 25px; cursor: pointer; font-size: 0.9rem; color: #334155; border-left: 4px solid transparent; transition: 0.2s; }}
            .question-item:hover {{ background: #f8fafc; color: var(--accent); }}
            .question-item.active {{ background: #eff6ff; border-left-color: var(--accent); font-weight: 600; color: #1e40af; }}
            
            .overview-btn {{ background: #ecfdf5; color: #047857; font-weight: bold; border-bottom: 1px dashed #a7f3d0; }}
            .overview-btn:hover, .overview-btn.active {{ background: #d1fae5; border-left-color: #10b981; color: #065f46; }}

            #content {{ flex-grow: 1; padding: 30px; overflow-y: auto; display: flex; flex-direction: column; }}
            .breadcrumb {{ color: #94a3b8; font-size: 0.85rem; margin-bottom: 5px; font-weight: 500; text-transform: uppercase; }}
            .main-title {{ font-size: 1.75rem; color: var(--primary); margin: 0 0 25px 0; }}
            
            .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; margin-bottom: 30px; }}
            .kpi-card {{ background: white; border-radius: 12px; padding: 20px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); display: flex; flex-direction: column; }}
            .kpi-title {{ font-size: 0.95rem; font-weight: 700; color: #64748b; margin-bottom: 15px; line-height: 1.4; }}
            .kpi-chart {{ height: 220px; width: 100%; }}
            
            .horizontal-viewport {{ overflow-x: auto; background: white; border-radius: 12px; padding: 25px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }}
            .vertical-stack {{ display: flex; flex-direction: column; gap: 40px; }}
            .sg-card {{ border-bottom: 2px dashed #e2e8f0; padding-bottom: 30px; }}
            .sg-card:last-child {{ border-bottom: none; padding-bottom: 0; }}
            .sg-label {{ font-size: 1.1rem; font-weight: 700; color: var(--accent); margin-bottom: 15px; display: inline-block; background: #ebf5ff; padding: 6px 14px; border-radius: 8px; }}
            .plot-row {{ height: 380px; }}
            
            /* Torte */
            .pie-section-wrapper {{ margin-top: 50px; background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; }}
            .pie-sg-title {{ font-size: 1.3rem; color: var(--primary); margin: 0 0 5px 0; }}
            .pie-separator {{ font-size: 1rem; color: var(--accent); margin: 0 0 20px 0; padding-top: 15px; border-top: 2px solid #e2e8f0; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }}
            .tabs-header {{ display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; }}
            .tab-btn {{ padding: 10px 24px; background: white; border: 1px solid #cbd5e1; border-radius: 8px; cursor: pointer; font-weight: 600; color: #475569; transition: 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02); font-size: 1rem; }}
            .tab-btn:hover {{ background: #f1f5f9; }}
            .tab-btn.active {{ background: var(--accent); color: white; border-color: var(--accent); box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); }}
            .pie-row {{ height: 420px; }}

            .welcome {{ text-align: center; margin-top: 20%; color: #94a3b8; font-size: 1.3rem; line-height: 1.6; }}
        </style>
    </head>
    <body>
        <div id="sidebar">
            <div class="sidebar-header">DATI ALMALAUREA</div>
            
            <div class="special-section">
                <div class="special-btn" onclick="renderPanoramica(this)">📊 Panoramica Globale</div>
                <div class="special-btn" onclick="renderPerformance(this)">🎯 Performance Ateneo</div>
            </div>
            
            <div id="menu"></div>
        </div>
        <div id="content">
            <div id="display_area">
                <div class="welcome"><strong>Dashboard intelligente attiva.</strong><br>I dati singoli sono stati raggruppati nelle panoramiche di sezione per semplificare il menu.</div>
            </div>
        </div>

        <script>
            const fullData = {json.dumps(js_data)};
            const years = {json.dumps(anni_list)};
            const ateneis = {json.dumps(atenei_list)};
            const palette = ['#e11d48', '#2563eb', '#10b981', '#f59e0b', '#7c3aed', '#db2777', '#0891b2', '#475569'];
            const colors = {{}};
            ateneis.forEach((a, i) => colors[a] = palette[i % palette.length]);

            const menu = document.getElementById('menu');
            const display = document.getElementById('display_area');

            function clearActiveMenus() {{
                document.querySelectorAll('.question-item, .special-btn, .overview-btn').forEach(el => el.classList.remove('active'));
            }}

            window.switchTab = function(sgIdx, year) {{
                document.querySelectorAll('.tab-content-' + sgIdx).forEach(el => el.style.display = 'none');
                document.querySelectorAll('.tab-btn-' + sgIdx).forEach(el => el.classList.remove('active'));
                document.getElementById('tab_' + sgIdx + '_' + year).style.display = 'block';
                document.getElementById('btn_' + sgIdx + '_' + year).classList.add('active');
                const plotDiv = document.getElementById('plot_pie_' + sgIdx + '_' + year);
                if (plotDiv && plotDiv.data) {{ Plotly.Plots.resize(plotDiv); }}
            }};

            // FUNZIONI PANORAMICA E PERFORMANCE GLOBALE (Omesse per brevità in questa spiegazione, funzionano come prima)
            // ... [Le funzioni findDataPaths, renderPanoramica, renderPerformance sono identiche alla versione precedente]
            function findDataPaths(keywords) {{
                let results = [];
                Object.keys(fullData).forEach(sez => {{
                    Object.keys(fullData[sez]).forEach(dom => {{
                        Object.keys(fullData[sez][dom]).forEach(sg => {{
                            Object.keys(fullData[sez][dom][sg]).forEach(voce => {{
                                const text = (dom + " " + sg + " " + voce).toLowerCase();
                                if (keywords.some(k => text.includes(k.toLowerCase()))) {{
                                    results.push({{ sez, dom, sg, voce, data: fullData[sez][dom][sg][voce] }});
                                }}
                            }});
                        }});
                    }});
                }});
                return results;
            }}

            window.renderPanoramica = function(btn) {{
                clearActiveMenus(); btn.classList.add('active');
                const kpisToFind = [
                    {{ keys: ['numero di laureati'], title: 'Numero di Laureati' }},
                    {{ keys: ['tasso di compilazione'], title: 'Tasso Compilazione (%)' }},
                    {{ keys: ['età alla laurea (medie'], title: 'Età Media alla Laurea' }},
                    {{ keys: ['cittadini stranieri'], title: 'Studenti Stranieri (%)' }},
                    {{ keys: ['voto di laurea (medie'], title: 'Voto Medio di Laurea' }},
                    {{ keys: ['durata degli studi (medie'], title: 'Durata Media Studi' }}
                ];
                renderKpiGrid('Executive Summary', '📊 Panoramica Globale', kpisToFind);
            }};

            window.renderPerformance = function(btn) {{
                clearActiveMenus(); btn.classList.add('active');
                const perfGroups = [
                    {{ id: 'sodd', title: '🎓 Soddisfazione del Corso e Docenti', keys: ['complessivamente soddisfatti', 'rapporti con i docenti'] }},
                    {{ id: 'infra', title: '🏢 Infrastrutture', keys: ['valutazione delle aule', 'servizi di biblioteca'] }},
                    {{ id: 'tir', title: '💼 Esperienza Pratica', keys: ['tirocini formativi', 'lavoro coerente'] }}
                ];
                let html = `<div class="breadcrumb">Indicatori di Qualità</div><h1 class="main-title">🎯 Performance Ateneo</h1><div class="vertical-stack" id="perf_stack"></div>`;
                display.innerHTML = html;
                const stack = document.getElementById('perf_stack');

                perfGroups.forEach((group, gIdx) => {{
                    const foundItems = findDataPaths(group.keys);
                    if (foundItems.length > 0) {{
                        let gHtml = `<div class="horizontal-viewport" style="background: #fafafa;"><h2 style="color: #1e40af; border-bottom: 2px solid #bfdbfe; padding-bottom: 10px; margin-top: 0;">${{group.title}}</h2><div style="display: flex; gap: 20px; overflow-x: auto; padding-bottom: 10px;">`;
                        foundItems.forEach((item, iIdx) => {{
                            if (item.voce === 'Valore Globale') return;
                            const divId = `perf_plot_${{gIdx}}_${{iIdx}}`;
                            gHtml += `<div style="min-width: 350px; background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;"><div style="font-size: 0.85rem; color: #64748b; margin-bottom: 5px;">${{item.dom}}</div><div style="font-weight: bold; color: #334155; margin-bottom: 10px;">${{item.voce}}</div><div id="${{divId}}" style="height: 250px;"></div></div>`;
                            setTimeout(() => {{
                                const traces = [];
                                ateneis.forEach(ateneo => {{
                                    if (item.data[ateneo]) traces.push({{ x: years, y: item.data[ateneo], name: ateneo, mode: 'lines+markers', line: {{ color: colors[ateneo], width: 3 }}, marker: {{ size: 6 }} }});
                                }});
                                Plotly.newPlot(divId, traces, {{ margin: {{ t: 10, b: 30, l: 30, r: 10 }}, showlegend: false, xaxis: {{ type: 'category' }}, yaxis: {{ range: [0, 105] }} }}, {{ displayModeBar: false, responsive: true }});
                            }}, 50);
                        }});
                        gHtml += `</div></div>`;
                        stack.innerHTML += gHtml;
                    }}
                }});
            }};

            function renderKpiGrid(breadcrumb, title, kpiList) {{
                display.innerHTML = `<div class="breadcrumb">${{breadcrumb}}</div><h1 class="main-title">${{title}}</h1><div class="kpi-grid" id="kpi_grid"></div>`;
                const grid = document.getElementById('kpi_grid');

                kpiList.forEach((kpi, idx) => {{
                    let found = kpi.dataObj ? [kpi] : findDataPaths(kpi.keys);
                    if (found.length > 0) {{
                        const metric = found[0];
                        const divId = `kpi_plot_${{idx}}`;
                        grid.innerHTML += `<div class="kpi-card"><div class="kpi-title">${{kpi.title}}</div><div id="${{divId}}" class="kpi-chart"></div></div>`;
                        
                        setTimeout(() => {{
                            const traces = [];
                            ateneis.forEach(ateneo => {{
                                const dataArr = metric.dataObj ? metric.dataObj[ateneo] : metric.data[ateneo];
                                if (dataArr) {{
                                    traces.push({{
                                        x: years, y: dataArr,
                                        name: ateneo, mode: 'lines+markers+text',
                                        line: {{ color: colors[ateneo], width: 4 }},
                                        marker: {{ size: 8 }},
                                        text: dataArr.map(v => v ? v.toFixed(1) : ''), textposition: 'top center',
                                        textfont: {{ size: 10, color: colors[ateneo] }},
                                        hovertemplate: `<b>${{ateneo}}</b><br>Valore: %{{y}}<extra></extra>`
                                    }});
                                }}
                            }});
                            const layout = {{ margin: {{ t: 10, b: 30, l: 30, r: 10 }}, legend: {{ orientation: 'h', y: -0.2 }}, hovermode: 'x unified', xaxis: {{ type: 'category', showgrid: false }}, yaxis: {{ showgrid: true, gridcolor: '#f1f5f9' }} }};
                            
                            const tLow = kpi.title.toLowerCase();
                            if (tLow.includes('voto')) layout.yaxis.range = [85, 115];
                            else if (tLow.includes('%')) layout.yaxis.range = [0, 105];
                            else if (tLow.includes('età') || tLow.includes('eta ')) layout.yaxis.range = [22, 35];
                            else layout.yaxis.rangemode = 'tozero';

                            Plotly.newPlot(divId, traces, layout, {{ displayModeBar: false, responsive: true }});
                        }}, 50);
                    }}
                }});
            }}

            // --- 5. LOGICA DI MENU INTELLIGENTE (DECLUTTERING) E PANORAMICA SEZIONE ---
            Object.keys(fullData).sort().forEach(sez => {{
                const group = document.createElement('div');
                group.className = 'section-box';
                group.innerHTML = `<div class="section-title">${{sez}}</div>`;
                
                // Bottone Speciale per la Panoramica della singola Sezione
                const panBtn = document.createElement('div');
                panBtn.className = 'question-item overview-btn';
                panBtn.innerHTML = '📊 Elementi Singoli';
                panBtn.onclick = () => {{
                    clearActiveMenus(); panBtn.classList.add('active');
                    renderSectionOverview(sez);
                }};
                group.appendChild(panBtn);

                // Scansione delle domande di questa sezione
                Object.keys(fullData[sez]).sort().forEach(dom => {{
                    const sgs = Object.keys(fullData[sez][dom]);
                    
                    // Condizione 1: È un "Valore Globale" o una singola metrica isolata?
                    let isSingleMetric = (sgs.length === 1 && Object.keys(fullData[sez][dom][sgs[0]]).length === 1);
                    
                    // Condizione 2: Contiene ESCLUSIVAMENTE la voce 'Valore Globale'?
                    let isOnlyGlobal = true;
                    for (let sg of sgs) {{
                        for (let v of Object.keys(fullData[sez][dom][sg])) {{
                            if (v !== 'Valore Globale') isOnlyGlobal = false;
                        }}
                    }}

                    // Se NON è una metrica isolata, mostrala nel menu normale.
                    // Altrimenti verrà "assorbita" dalla Panoramica Sezione, pulendo il menu!
                    if (!isSingleMetric && !isOnlyGlobal) {{
                        const item = document.createElement('div');
                        item.className = 'question-item';
                        item.textContent = dom;
                        item.onclick = () => {{
                            clearActiveMenus(); item.classList.add('active');
                            drawUI(sez, dom);
                        }};
                        group.appendChild(item);
                    }}
                }});
                menu.appendChild(group);
            }});

            // FUNZIONE: Genera la griglia riassuntiva di tutti i "Valori Globali" di una Sezione
            window.renderSectionOverview = function(sez) {{
                let kpiList = [];
                
                Object.keys(fullData[sez]).forEach(dom => {{
                    Object.keys(fullData[sez][dom]).forEach(sg => {{
                        Object.keys(fullData[sez][dom][sg]).forEach(voce => {{
                            // Raccogliamo i Valori Globali o le metriche isolate
                            const isSingle = (Object.keys(fullData[sez][dom]).length === 1 && Object.keys(fullData[sez][dom][sg]).length === 1);
                            if (voce === 'Valore Globale' || isSingle) {{
                                let cardTitle = (voce === 'Valore Globale' || voce === dom) ? dom : `${{dom}}<br><small>${{voce}}</small>`;
                                kpiList.push({{
                                    title: cardTitle,
                                    dataObj: fullData[sez][dom][sg][voce]
                                }});
                            }}
                        }});
                    }});
                }});

                if (kpiList.length > 0) {{
                    renderKpiGrid(sez, '📊 Elementi Singoli', kpiList);
                }} else {{
                    display.innerHTML = `<div class="breadcrumb">${{sez}}</div><h1 class="main-title">📊 Elementi Singoli</h1><p style="color:#64748b;">Nessun indicatore globale rilevato in questa sezione. Esplora le voci sottostanti nel menu.</p>`;
                }}
            }};

            // FUNZIONE DI RENDERING STANDARD (Identica alla versione precedente per i grafici a scorrimento)
            function drawUI(sez, dom) {{
                const sgMap = fullData[sez][dom];
                const sgs = Object.keys(sgMap);
                let vociUniche = new Set();
                sgs.forEach(s => Object.keys(sgMap[s]).forEach(v => vociUniche.add(v)));
                const voci = Array.from(vociUniche);
                const colWidth = 380; 
                const totalWidth = Math.max(voci.length * colWidth, document.getElementById('content').clientWidth - 100);

                let html = `<div class="breadcrumb">${{sez}}</div><h1 class="main-title">${{dom}}</h1><div class="horizontal-viewport"><div class="vertical-stack" style="width: ${{totalWidth}}px;">`;
                sgs.map((s, i) => {{
                    html += `<div class="sg-card">${{s !== 'Dati' ? `<div class="sg-label">${{s}}</div>` : ''}}<div id="plot_row_${{i}}" class="plot-row"></div></div>`;
                }});
                html += `</div></div>`;

                sgs.forEach((s, sIdx) => {{
                    const pieVoci = voci.filter(v => !v.toLowerCase().includes('medie') && !v.toLowerCase().includes('voto') && !v.toLowerCase().includes('punteggio') && !v.toLowerCase().includes('ritardo') && !v.toLowerCase().includes('valore globale'));
                    if (pieVoci.length > 1) {{
                        html += `<div class="pie-section-wrapper">${{s !== 'Dati' ? `<h2 class="pie-sg-title">${{s}}</h2>` : ''}}<div class="pie-separator">Visualizzazione a torta per anno</div><div class="tabs-header">`;
                        years.map((y, yIdx) => html += `<button id="btn_${{sIdx}}_${{y}}" class="tab-btn tab-btn-${{sIdx}} ${{yIdx === years.length - 1 ? 'active' : ''}}" onclick="switchTab('${{sIdx}}', '${{y}}')">${{y}}</button>`);
                        html += `</div><div class="tabs-body">`;
                        years.map((y, yIdx) => html += `<div id="tab_${{sIdx}}_${{y}}" class="tab-content tab-content-${{sIdx}}" style="display: ${{yIdx === years.length - 1 ? 'block' : 'none'}};"><div class="horizontal-viewport" style="background: transparent; border: none; padding: 0; box-shadow: none;"><div id="plot_pie_${{sIdx}}_${{y}}" class="pie-row"></div></div></div>`);
                        html += `</div></div>`;
                    }}
                }});

                display.innerHTML = html;

                sgs.forEach((s, sIdx) => {{
                    const tracesLines = []; const annotationsLines = [];
                    voci.forEach((v, vIdx) => {{
                        if (sgMap[s][v]) {{
                            Object.keys(sgMap[s][v]).forEach(ateneo => {{
                                tracesLines.push({{ x: years, y: sgMap[s][v][ateneo], name: ateneo, mode: 'lines+markers', line: {{ color: colors[ateneo], width: 3 }}, marker: {{ size: 8 }}, xaxis: 'x' + (vIdx + 1), yaxis: 'y' + (vIdx + 1), legendgroup: ateneo, showlegend: (sIdx === 0 && vIdx === 0) }});
                            }});
                        }}
                        annotationsLines.push({{ text: '<b>' + (v.length > 45 ? v.substring(0, 45) + '...' : v) + '</b>', showarrow: false, font: {{ size: 13, color: '#334155' }}, x: (vIdx + 0.5) / voci.length, y: 1.10, xref: 'paper', yref: 'paper', xanchor: 'center', yanchor: 'bottom' }});
                    }});

                    const layoutLines = {{ grid: {{ rows: 1, columns: voci.length, pattern: 'independent' }}, annotations: annotationsLines, margin: {{ t: 50, b: 40, l: 40, r: 20 }}, legend: {{ orientation: 'h', y: -0.15, x: 0.5, xanchor: 'center' }}, hovermode: 'x unified', paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' }};
                    const context = (dom + " " + s + " " + voci.join(" ")).toLowerCase();
                    voci.forEach((_, i) => {{
                        let axis = {{ showgrid: true, gridcolor: '#f1f5f9', zeroline: false }};
                        if (context.includes('voto di laurea') && !context.includes('diploma') && !context.includes('precedente')) axis.range = [80, 115];
                        else if (context.includes('voto di diploma')) axis.range = [60, 105];
                        else if (context.includes('punteggio') || context.includes('esami in 30')) axis.range = [18, 31];
                        else if (context.includes('età') || context.includes('eta ')) axis.range = [20, 35];
                        else if (context.includes('%')) axis.range = [0, 105];
                        else axis.rangemode = 'tozero';
                        layoutLines['yaxis' + (i+1)] = axis; layoutLines['xaxis' + (i+1)] = {{ type: 'category' }};
                    }});
                    Plotly.newPlot('plot_row_' + sIdx, tracesLines, layoutLines, {{ responsive: true, displayModeBar: false }});

                    const pieVoci = voci.filter(v => !v.toLowerCase().includes('medie') && !v.toLowerCase().includes('voto') && !v.toLowerCase().includes('punteggio') && !v.toLowerCase().includes('ritardo') && !v.toLowerCase().includes('valore globale'));
                    if (pieVoci.length > 1) {{
                        years.forEach((y, yIdx) => {{
                            const tracesPie = []; const annotationsPie = [];
                            const validAteneis = ateneis.filter(a => pieVoci.some(v => sgMap[s][v] && sgMap[s][v][a] && sgMap[s][v][a][yIdx] != null));
                            if (validAteneis.length > 0) {{
                                document.getElementById(`plot_pie_${{sIdx}}_${{y}}`).style.width = Math.max(validAteneis.length * 360, document.getElementById('content').clientWidth - 150) + 'px';
                                validAteneis.forEach((ateneo, aIdx) => {{
                                    tracesPie.push({{ type: 'pie', labels: pieVoci, values: pieVoci.map(v => (sgMap[s][v] && sgMap[s][v][ateneo] && sgMap[s][v][ateneo][yIdx] != null) ? sgMap[s][v][ateneo][yIdx] : 0), name: ateneo, domain: {{ row: 0, column: aIdx }}, hole: 0.4, textinfo: 'percent', hoverinfo: 'label+percent+name', showlegend: aIdx === 0, marker: {{ colors: ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#64748b'] }} }});
                                    annotationsPie.push({{ text: `<b>${{ateneo}}</b>`, font: {{ size: 15, color: '#1e293b' }}, showarrow: false, x: (aIdx + 0.5) / validAteneis.length, y: 1.15, xref: 'paper', yref: 'paper', xanchor: 'center', yanchor: 'bottom' }});
                                }});
                                Plotly.newPlot(`plot_pie_${{sIdx}}_${{y}}`, tracesPie, {{ grid: {{ rows: 1, columns: validAteneis.length }}, annotations: annotationsPie, margin: {{ t: 60, b: 20, l: 20, r: 20 }}, legend: {{ orientation: 'h', y: -0.1, x: 0.5, xanchor: 'center' }}, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' }}, {{ responsive: true, displayModeBar: false }});
                            }}
                        }});
                    }}
                }});
            }}
        </script>
    </body>
    </html>
    """

    with open(NOME_FILE_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"✅ Dashboard Aggiornata con successo: {NOME_FILE_OUTPUT}")

if __name__ == "__main__":
    main()