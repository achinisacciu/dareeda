import io
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go


def _find_typst() -> str:
    configured = os.environ.get("TYPST_BIN")
    if configured and Path(configured).exists():
        return configured

    p = shutil.which("typst")
    if p:
        return p

    local_app = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        Path(local_app) / "Microsoft" / "WinGet" / "Links" / "typst.exe",
        Path(local_app) / "Microsoft" / "WinGet" / "Packages" / "Typst.Typst_Microsoft.Winget.Source_8wekyb3d8bbwe" / "typst.exe",
        Path(r"C:\Program Files\typst\typst.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        "Typst non trovato. Installa con: winget install --id Typst.Typst "
        "oppure configura TYPST_BIN."
    )


def export_chart(chart: dict, out_path: Path, width: int = 920, height: int = 460) -> bool:
    try:
        fig = go.Figure(data=chart.get("data", []), layout=chart.get("layout", {}))
        fig.update_layout(
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
            font=dict(family="Arial", size=11, color="#1A1816"),
            margin=dict(t=80, b=80, l=70, r=30),
        )
        fig.write_image(str(out_path), width=width, height=height, scale=1.8)
        return True
    except Exception:
        return False


def _collect_charts(data: dict, img_dir: Path) -> dict:
    chart_paths: dict[str, str] = {}
    counter = [0]

    def _walk(obj, prefix):
        if isinstance(obj, dict):
            if "data" in obj and "layout" in obj:
                key = f"chart_{counter[0]:04d}"
                counter[0] += 1
                out = img_dir / f"{key}.png"
                if export_chart(obj, out):
                    chart_paths[prefix] = key
                return

            for name, value in obj.items():
                _walk(value, f"{prefix}.{name}" if prefix else name)
            return

        if isinstance(obj, list):
            for index, item in enumerate(obj):
                _walk(item, f"{prefix}[{index}]")

    _walk(data, "")
    return chart_paths


def _esc(value) -> str:
    text = "" if value is None else str(value)
    replacements = {
        "\\": "\\\\",
        "#": "\\#",
        "[": "\\[",
        "]": "\\]",
        "@": "\\@",
        "<": "\\<",
        ">": "\\>",
        "*": "\\*",
        "_": "\\_",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _fmt_int(value) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return "0"


def _fmt_float(value, suffix: str = "") -> str:
    try:
        return f"{float(value):.2f}{suffix}"
    except Exception:
        return f"0{suffix}"


def _img(rel_path: str, caption: str, width: str = "100%") -> str:
    return f'#figure(image("{rel_path}", width: {width}), caption: [{_esc(caption)}])\n'


def _bullet_list(items: list[str], empty_label: str = "Nessun elemento rilevante.") -> str:
    if not items:
        return f"- {_esc(empty_label)}\n"
    return "".join(f"- {_esc(item)}\n" for item in items)


def _pair_table(rows: list[tuple[str, str]]) -> str:
    normalized = list(rows)
    if len(normalized) % 2 != 0:
        normalized.append(("", ""))

    cells = []
    for label, value in normalized:
        cells.append(f'table.cell(fill: rgb("#F7F7F8"))[*{_esc(label)}*]')
        cells.append(f"[{_esc(value)}]")

    return "#table(\n  columns: 4,\n  stroke: rgb(\"#E7E5E4\"),\n  inset: 8pt,\n  " + ",\n  ".join(cells) + "\n)\n"


def _rows_table(items: list[dict], keys: list[tuple[str, str]], limit: int = 12) -> str:
    if not items:
        return "_Nessun dato disponibile._\n"

    header = ",\n    ".join(f"[*{_esc(label)}*]" for label, _ in keys)
    cells = []
    for item in items[:limit]:
        for _, key in keys:
            cells.append(f"[{_esc(item.get(key, ''))}]")

    return (
        "#table(\n"
        f"  columns: {len(keys)},\n"
        "  stroke: rgb(\"#E7E5E4\"),\n"
        "  inset: 8pt,\n"
        "  table.header(\n"
        f"    {header}\n"
        "  ),\n"
        f"  {', '.join(cells)}\n"
        ")\n"
    )


def _format_cleaning_actions(actions: list[dict]) -> list[str]:
    formatted = []
    for action in actions or []:
        action_type = action.get("type")
        column = action.get("column")
        if action_type == "exclude_column":
            formatted.append(f"Esclusione colonna: {column}")
        elif action_type == "drop_duplicate_rows":
            formatted.append("Rimozione righe duplicate esatte")
        elif action_type == "replace_values":
            formatted.append(f"Conversione token in null: {column}")
        elif action_type == "trim_whitespace":
            formatted.append(f"Trim spazi iniziali/finali: {column}")
    return formatted


def _collect_summary_insights(data: dict) -> list[str]:
    insights = []

    dq = data.get("data_quality", {})
    for value in [
        (dq.get("missing") or {}).get("ai_comment"),
        (dq.get("duplicates") or {}).get("ai_comment"),
        ((data.get("bivariate") or {}).get("num_num") or {}).get("ai_comment"),
        ((data.get("ml_exploratory") or {}).get("feature_importance") or {}).get("ai_comment"),
        (data.get("inference") or {}).get("ai_comment"),
        (data.get("insights") or {}).get("summary"),
        (data.get("insights") or {}).get("ai_comment"),
        (data.get("insights") or {}).get("headline"),
    ]:
        if value:
            insights.append(str(value))

    deduped = []
    seen = set()
    for insight in insights:
        if insight not in seen:
            deduped.append(insight)
            seen.add(insight)
    return deduped[:8]


def _cleaning_rows(actions: list[dict]) -> list[dict]:
    rows = []
    for action in actions or []:
        action_type = action.get("type") or ""
        rows.append({
            "action": action_type,
            "column": action.get("column") or "Dataset",
            "details": (action.get("params") or {}) or "standard",
        })
    return rows


def _generate_typst(data: dict, img_dir: Path, chart_map: dict) -> str:
    del img_dir

    front_matter = data.get("front_matter", {})
    executive = data.get("executive", {})
    profiling = data.get("profiling", {})
    predictive_prep = data.get("predictive_prep", {})
    governance = data.get("governance", {})
    deliverables = data.get("deliverables", {})
    advanced_analytics = data.get("advanced_analytics", {})
    overview = data.get("overview", {})
    quality = data.get("data_quality", {})
    multivariate = data.get("multivariate", {})
    inference = data.get("inference", {})
    ml = data.get("ml_exploratory", {})
    univariate = data.get("univariate", {})
    analysis_context = data.get("analysis_context", {})
    applied_cleaning = data.get("applied_cleaning", {})

    sampling = analysis_context.get("sampling", {})
    accepted_features = data.get("accepted_features", []) or []
    accepted_feature_names = [
        feature.get("name") for feature in accepted_features if feature.get("name")
    ] or (analysis_context.get("accepted_feature_names") or [])
    cleaning_actions = _format_cleaning_actions(
        applied_cleaning.get("actions") or analysis_context.get("cleaning_actions") or []
    )
    summary_insights = _collect_summary_insights(data)

    rows = overview.get("n_rows") or data.get("n_rows_full") or 0
    cols = overview.get("n_cols") or data.get("n_cols") or 0
    filename = data.get("dataset_filename", "Dataset")
    analysis_id = data.get("analysis_id", "")
    cover = front_matter.get("cover", {})
    report_meta = deliverables.get("report_metadata", {}) or front_matter.get("report_metadata", {})
    generated_at = cover.get("generated_at") or datetime.now().strftime("%d/%m/%Y %H:%M")
    target = data.get("target") or analysis_context.get("target") or "Non impostata"
    problem_type = data.get("problem_type") or analysis_context.get("problem_type") or "Non impostato"
    sampling_state = "Campionato" if data.get("sampled") else "Completo"
    sample_rows = data.get("sample_n") or rows
    rows_before_sampling = sampling.get("full_rows_before_sampling") or rows

    missing = quality.get("missing", {})
    missing_global = missing.get("global", {})
    duplicates = quality.get("duplicates", {})
    high_pairs = multivariate.get("high_correlation_pairs", []) or []
    tests = inference.get("tests", []) or []

    cleaning_registry = _cleaning_rows(
        applied_cleaning.get("actions") or analysis_context.get("cleaning_actions") or []
    )

    document = [
        """
#set page(paper: "a4", margin: (x: 1.6cm, y: 1.8cm))
#set text(font: "Arial", size: 10pt, lang: "it")
#set heading(numbering: "1.")
#set par(justify: true, leading: 0.65em)

#align(center)[
  #text(size: 28pt, weight: "bold", fill: rgb("#E4002B"))[DAREEDA]
  #v(4pt)
  #text(size: 12pt, fill: rgb("#37424A"))[Report EDA professionale]
]

#v(14pt)
""",
        _pair_table([
            ("Dataset", filename),
            ("ID analisi", analysis_id),
            ("Generato", generated_at),
            ("Versione tool", data.get("tool_version", "")),
            ("Righe", _fmt_int(rows)),
            ("Colonne", _fmt_int(cols)),
            ("Target", target),
            ("Problema", problem_type),
        ]),
        "\n= Front Matter\n\n",
        _pair_table([
            ("Classificazione", cover.get("classification", "INTERNAL")),
            ("Dataset hash", cover.get("dataset_hash", "n/a")),
            ("Runtime", cover.get("runtime", "n/a")),
            ("Analyst", cover.get("analyst", "DAREEDA")),
            ("Reviewer", cover.get("reviewer", "Pending review")),
            ("Git commit", report_meta.get("git_commit", "n/a")),
            ("Python", ((report_meta.get("environment") or {}).get("python", "n/a"))),
            ("Quality score", str(report_meta.get("quality_score", "n/a"))),
        ]),
        "\n= Executive Summary\n\n",
        _bullet_list(
            ([executive.get("executive_summary")] if executive.get("executive_summary") else []) + summary_insights,
            empty_label="Analisi completata senza commenti sintetici aggiuntivi.",
        ),
        "\n== Business Context\n\n",
        _pair_table([
            ("Progetto", (executive.get("business_context") or {}).get("project", filename)),
            ("Obiettivo", (executive.get("business_context") or {}).get("objective", problem_type)),
            ("Stakeholder", (executive.get("business_context") or {}).get("stakeholder", "Data / Analytics")),
            ("Timeline", (executive.get("business_context") or {}).get("timeline", "Current sprint")),
            ("Impatto atteso", (executive.get("business_context") or {}).get("expected_impact", "Da quantificare")),
            ("Recommendation", ((executive.get("recommendation") or {}).get("label", "n/a"))),
        ]),
        "\n= Contesto e Decisioni\n\n",
        _pair_table([
            ("Modalita dati", sampling_state),
            ("Righe analizzate", _fmt_int(sample_rows)),
            ("Righe origine", _fmt_int(rows_before_sampling)),
            ("Target", target),
            ("Tipo problema", problem_type),
            ("Feature derivate accettate", ", ".join(accepted_feature_names) if accepted_feature_names else "Nessuna"),
            ("Pulizie applicate", ", ".join(cleaning_actions) if cleaning_actions else "Nessuna"),
            ("Output PDF", "Insight, grafici e decisioni utente"),
        ]),
        "\n== Decisioni utente\n\n",
        _bullet_list([
            f"Target selezionata: {target}",
            f"Tipo di problema: {problem_type}",
            (
                f"Feature derivate incluse: {', '.join(accepted_feature_names)}"
                if accepted_feature_names else
                "Nessuna feature derivata accettata."
            ),
            (
                f"Azioni di cleaning applicate: {', '.join(cleaning_actions)}"
                if cleaning_actions else
                "Nessuna azione di cleaning applicata."
            ),
        ]),
        "\n= Panoramica Dataset\n\n",
        _pair_table([
            ("Righe", _fmt_int(rows)),
            ("Colonne", _fmt_int(cols)),
            ("Celle totali", _fmt_int(overview.get("n_cells", 0))),
            ("Memoria", f"{_fmt_float(overview.get('memory_mb', 0))} MB"),
            ("Missing globale", f"{_fmt_float(overview.get('pct_missing_global', 0))}%"),
            ("Colonne derivate", ", ".join(data.get("derived_columns", [])) if data.get("derived_columns") else "Nessuna"),
            ("Colonne dopo cleaning", _fmt_int(applied_cleaning.get("after_cols", cols))),
            ("Righe dopo cleaning", _fmt_int(applied_cleaning.get("after_rows", rows))),
        ]),
    ]

    types_chart_key = "overview.charts.types_distribution"
    if types_chart_key in chart_map:
        document.append(_img(f"images/{chart_map[types_chart_key]}.png", "Distribuzione dei tipi semantici", "84%"))

    document.extend([
        "\n== Struttura colonne\n\n",
        _rows_table(
            overview.get("columns", []),
            [
                ("Nome", "name"),
                ("Tipo semantico", "semantic_type"),
                ("Ruolo", "role"),
                ("Unici", "n_unique"),
                ("Missing %", "pct_missing"),
            ],
            limit=20,
        ),
        "\n= Profiling Avanzato\n\n",
        _pair_table([
            ("Sorgente primaria", (profiling.get("lineage") or {}).get("primary_source", "n/a")),
            ("System of record", (profiling.get("lineage") or {}).get("system_of_record", "n/a")),
            ("Estrazione", (profiling.get("lineage") or {}).get("extraction_mode", "n/a")),
            ("Update frequency", (profiling.get("lineage") or {}).get("update_frequency", "n/a")),
            ("Rows", _fmt_int((profiling.get("structural_overview") or {}).get("n_rows", rows))),
            ("Features", _fmt_int((profiling.get("structural_overview") or {}).get("n_columns", cols))),
            ("Memoria", f"{_fmt_float((profiling.get('structural_overview') or {}).get('memory_mb', 0))} MB"),
            ("PII candidate", _fmt_int(len(profiling.get("pii_candidates") or []))),
        ]),
        "\n= Qualita del Dato\n\n",
        _pair_table([
            ("Righe con missing", f"{_fmt_float(missing_global.get('pct_rows_with_missing', 0))}%"),
            ("Celle mancanti", _fmt_int(missing_global.get("total_missing_cells", 0))),
            ("Percentuale celle", f"{_fmt_float(missing_global.get('pct_missing_cells', 0))}%"),
            ("Righe duplicate", _fmt_int(duplicates.get("n_duplicate_rows", 0))),
            ("Percentuale duplicate", f"{_fmt_float(duplicates.get('pct_duplicate_rows', 0))}%"),
            ("Missing medi per riga", _fmt_float(missing_global.get("mean_missing_per_row", 0))),
            ("Missing mediani per riga", _fmt_float(missing_global.get("median_missing_per_row", 0))),
            ("Focus report", "Pattern missing e segnali di qualita"),
        ]),
    ])

    for key, caption in [
        ("profiling.charts.semantic_treemap", "Semantic types treemap"),
        ("profiling.charts.cardinality_missing_scatter", "Cardinality vs missing"),
        ("data_quality.missing.charts.missing_bar", "Distribuzione dei valori mancanti per colonna"),
        ("data_quality.missing.charts.missing_heatmap", "Heatmap dei missing"),
        ("data_quality.missing.charts.missing_cooccurrence", "Matrice di co-occorrenza dei missing"),
        ("data_quality.missing.charts.missing_pattern_correlation", "Correlazione dei pattern di missing"),
        ("data_quality.missing.charts.missing_dendrogram", "Dendrogramma dei pattern di missing"),
    ]:
        if key in chart_map:
            document.append(_img(f"images/{chart_map[key]}.png", caption))

    document.extend([
        "\n= Pulizia e Riproducibilita\n\n",
        _pair_table([
            ("Azioni registrate", _fmt_int(len(cleaning_registry))),
            ("Righe prima cleaning", _fmt_int(applied_cleaning.get("before_rows", rows))),
            ("Righe dopo cleaning", _fmt_int(applied_cleaning.get("after_rows", rows))),
            ("Colonne prima cleaning", _fmt_int(applied_cleaning.get("before_cols", cols))),
            ("Colonne dopo cleaning", _fmt_int(applied_cleaning.get("after_cols", cols))),
            ("Pipeline", "Riproducibile tramite analysis_context e applied_cleaning"),
        ]),
        "\n== Registro trasformazioni\n\n",
        _rows_table(
            cleaning_registry,
            [
                ("Azione", "action"),
                ("Colonna", "column"),
                ("Dettagli", "details"),
            ],
            limit=20,
        ),
        "\n= Analisi Univariata\n\n",
    ])

    rendered_uni = 0
    for column, column_data in univariate.items():
        if rendered_uni >= 6:
            break
        if column_data.get("error") or column_data.get("skipped"):
            continue

        rendered_uni += 1
        document.append(f"== {_esc(column)}\n\n")
        if column_data.get("ai_comment"):
            document.append(f"_{_esc(column_data['ai_comment'])}_\n\n")

        for chart_name in (column_data.get("charts") or {}):
            key = f"univariate.{column}.charts.{chart_name}"
            if key in chart_map:
                document.append(_img(f"images/{chart_map[key]}.png", f"{column} - {chart_name}", "88%"))
                break

    document.append("\n= Analisi Bivariata e Multivariata\n\n")
    for key, caption in [
        ("bivariate.num_num.charts.correlation_heatmap", "Matrice di correlazione numerica"),
        ("multivariate.correlation_global.chart", "Correlazione globale variabili numeriche"),
        ("multivariate.pca.charts.scree", "PCA scree plot"),
        ("multivariate.pca.charts.scatter_pc1_pc2", "PCA PC1 vs PC2"),
    ]:
        if key in chart_map:
            document.append(_img(f"images/{chart_map[key]}.png", caption, "88%"))

    document.extend([
        "\n== Coppie ad alta correlazione\n\n",
        _rows_table(
            high_pairs,
            [
                ("Variabile A", "var_a"),
                ("Variabile B", "var_b"),
                ("Correlazione", "correlation"),
                ("Flag", "flag"),
            ],
            limit=12,
        ),
        "\n= ML Esplorativo e Inferenza\n\n",
    ])

    fi_comment = (ml.get("feature_importance") or {}).get("ai_comment")
    if fi_comment:
        document.append(f"_{_esc(fi_comment)}_\n\n")

    for key, caption in [
        ("ml_exploratory.feature_importance.charts.bar", "Feature importance"),
        ("ml_exploratory.clustering.charts.scatter", "Clustering esplorativo"),
    ]:
        if key in chart_map:
            document.append(_img(f"images/{chart_map[key]}.png", caption, "86%"))

    document.extend([
        "\n== Test statistici principali\n\n",
        _rows_table(
            tests,
            [
                ("Feature", "feature"),
                ("Target", "target"),
                ("Test", "test"),
                ("p-value", "pvalue"),
                ("FDR", "significant_fdr"),
            ],
            limit=20,
        ),
        "\n= Predictive Preparation\n\n",
        _rows_table(
            predictive_prep.get("encoding_strategy") or [],
            [
                ("Colonna", "column"),
                ("Strategia", "strategy"),
                ("Missing %", "missing_pct"),
            ],
            limit=12,
        ),
        "\n== Leakage Risk\n\n",
        _rows_table(
            predictive_prep.get("leakage_risk_assessment") or [],
            [
                ("Colonna", "column"),
                ("Rischio", "risk"),
                ("Severita", "severity"),
                ("Azione", "recommended_action"),
            ],
            limit=12,
        ),
        "\n= Governance & Compliance\n\n",
        _rows_table(
            governance.get("pii_detection") or [],
            [
                ("Colonna", "column"),
                ("Tipo", "pii_type"),
                ("Confidenza", "confidence"),
                ("Azione", "recommended_action"),
            ],
            limit=12,
        ),
        "\n== Limitazioni\n\n",
        _bullet_list(governance.get("limitations") or [], empty_label="Nessuna limitazione registrata."),
        "\n= Deliverables\n\n",
        _rows_table(
            deliverables.get("outputs") or [],
            [
                ("Output", "name"),
                ("Formato", "format"),
                ("Path", "path"),
                ("Hash", "hash"),
            ],
            limit=12,
        ),
        "\n== Validazione tecnica\n\n",
        _rows_table(
            deliverables.get("validation_checklist") or [],
            [
                ("Check", "check"),
                ("Stato", "status"),
                ("Dettaglio", "detail"),
            ],
            limit=12,
        ),
        "\n== Advanced Analytics\n\n",
        _rows_table(
            advanced_analytics.get("applicability") or [],
            [
                ("Analisi", "analysis"),
                ("Applicabile", "applicable"),
                ("Motivo", "reason"),
            ],
            limit=12,
        ),
        '\n#v(16pt)\n#align(center)[#text(size: 8pt, fill: rgb("#6B7280"))[Generato da DAREEDA]]\n',
    ])

    return "".join(document)


def generate_report_in_memory(analysis_data: dict) -> io.BytesIO:
    # Creiamo una cartella temporanea che si auto-distruggerà
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Creiamo la sottocartella images per Plotly
        img_dir = tmp_path / "images"
        img_dir.mkdir(exist_ok=True)

        # Generiamo le immagini Plotly salvandole temporaneamente
        chart_map = _collect_charts(analysis_data, img_dir)

        # Generiamo il codice Typst
        typst_source = _generate_typst(analysis_data, img_dir, chart_map)

        # Salviamo il file Typst temporaneo
        typ_path = tmp_path / "report.typ"
        typ_path.write_text(typst_source, encoding="utf-8")

        # Troviamo l'eseguibile Typst
        typst_bin = _find_typst()

        # Eseguiamo Typst. Usiamo "-" per l'output: significa che Typst
        # non salverà un file PDF, ma manderà i bytes del PDF nello standard output
        result = subprocess.run(
            [typst_bin, "compile", str(typ_path), "-"],
            capture_output=True,
            cwd=str(tmp_path), # Lavoriamo nella cartella temporanea
        )

        if result.returncode != 0:
            # result.stderr sarà in bytes, lo decodifichiamo per l'errore
            error_msg = result.stderr.decode("utf-8", errors="ignore").strip()[:600]
            raise RuntimeError(f"Typst error: {error_msg}")

        # result.stdout contiene il PDF in formato binario! Lo mettiamo nel buffer
        pdf_buffer = io.BytesIO(result.stdout)
        pdf_buffer.seek(0)

        return pdf_buffer
