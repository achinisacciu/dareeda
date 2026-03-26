import Plot from 'react-plotly.js';
import { DAREEDA_THEME, applyTheme } from '../utils/chartTheme';

const CONFIG = {
  responsive: true,
  displayModeBar: 'hover',
  displaylogo: false,
  modeBarButtonsToRemove: ['sendDataToCloud', 'editInChartStudio', 'lasso2d', 'select2d'],
  toImageButtonOptions: {
    format: 'png',
    width: 1200,
    height: 600,
    scale: 2,
    filename: 'dareeda_chart',
  },
};

export function PlotlyChart({ chart, height = 380, className = '', type = 'auto' }) {
  if (!chart || !chart.data) {
    return (
      <div className="chart-container u-flex u-items-center u-justify-center u-flex-col u-gap-3">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
          <rect x="3" y="3" width="18" height="18" rx="2"/>
          <path d="M3 9h18M9 21V9"/>
        </svg>
        <p className="u-text-muted u-text-sm">Grafico non disponibile</p>
      </div>
    );
  }

  const chartType = type === 'auto' ? detectChartType(chart.data) : type;

  const dataWithTheme = chart.data.map((trace, i) => {
    const baseColor = DAREEDA_THEME.colorway[i % DAREEDA_THEME.colorway.length];
    const normalizedMarkerColor = normalizeBrandColor(
      trace.marker?.color || trace.marker_color || trace.fillcolor || baseColor,
      baseColor,
    );
    const normalizedLineColor = normalizeBrandColor(
      trace.line?.color || trace.marker?.line?.color || trace.line_color || baseColor,
      baseColor,
    );
    const normalizedFillColor = trace.fillcolor
      ? normalizeBrandColor(trace.fillcolor, normalizedMarkerColor)
      : undefined;
    const colorscale = trace.colorscale ? normalizeColorscale(trace.colorscale) : undefined;

    if (trace.type === 'heatmap') {
      return {
        ...trace,
        colorscale,
        zsmooth: trace.zsmooth || false,
        hoverlabel: {
          bgcolor: '#FFFFFF',
        },
      };
    }

    if (trace.type === 'bar') {
      const preferInsideLabels = trace.textposition === 'outside' || trace.textposition === 'auto';
      return {
        ...trace,
        marker: {
          ...trace.marker,
          color: normalizedMarkerColor,
          line: {
            width: 1,
            color: normalizeBrandColor(trace.marker?.line?.color || '#FFFFFF', '#FFFFFF'),
          },
        },
        textposition: preferInsideLabels ? 'inside' : trace.textposition,
        insidetextanchor: 'end',
        textfont: preferInsideLabels
          ? {
              color: '#FFFFFF',
              size: 11,
              ...trace.textfont,
            }
          : trace.textfont,
        cliponaxis: false,
        constraintext: 'inside',
      };
    }

    if (trace.type === 'pie') {
      return {
        ...trace,
        textfont: {
          color: '#1A1816',
          size: 12,
          ...trace.textfont,
        },
        marker: {
          ...trace.marker,
          colors: (trace.marker?.colors || DAREEDA_THEME.colorway).map((color, idx) =>
            normalizeBrandColor(color, DAREEDA_THEME.colorway[idx % DAREEDA_THEME.colorway.length])
          ),
          line: { width: 1, color: '#FFFFFF' },
        },
      };
    }

    return {
      ...trace,
      line: {
        width: 2,
        ...trace.line,
        shape: trace.line?.shape || (chartType === 'area' ? 'spline' : 'linear'),
        smoothing: trace.line?.shape === 'spline' || chartType === 'area'
          ? (trace.line?.smoothing ?? 1.1)
          : trace.line?.smoothing,
        color: normalizedLineColor,
      },
      marker: {
        size: 6,
        ...trace.marker,
        line: {
          width: 1,
          color: normalizeBrandColor(trace.marker?.line?.color || '#FFFFFF', '#FFFFFF'),
        },
        color: normalizedMarkerColor,
      },
      marker_color: normalizedMarkerColor,
      line_color: normalizedLineColor,
      fill: trace.fill || (chartType === 'area' ? 'tozeroy' : undefined),
      fillcolor: chartType === 'area'
        ? `rgba(${hexToRgb(normalizedMarkerColor)}, 0.12)`
        : normalizedFillColor,
      hovertemplate: trace.hovertemplate ||
        `<b>%{x}</b><br>%{y:,.2f}<extra>${trace.name || ''}</extra>`,
      opacity: trace.opacity || 0.9,
      cliponaxis: trace.cliponaxis ?? false,
    };
  });

  // Calcola rotazione label asse X in base al numero di categorie
  const numCategories = chart.data[0]?.x?.length || 0;
  const tickangle = numCategories > 10 ? -45 : numCategories > 6 ? -25 : 0;

  // Margine bottom dinamico per evitare che le label vengano tagliate
  const marginBottom = tickangle !== 0 ? 120 : 70;

  const hasOutsideLabels = dataWithTheme.some(trace => trace.textposition === 'outside');
  const customLayout = {
    ...chart.layout,
    autosize: true,
    height,
    margin: {
      t: hasOutsideLabels ? 84 : 60,
      b: marginBottom,
      l: 72,
      r: 32,
      autoexpand: true,
    },
    xaxis: {
      tickangle,
      tickfont: { size: 11, color: "#7A756F" },
      automargin: true,
      showline: true,
      showgrid: false,
      ...normalizeAxis(chart.layout?.xaxis),
    },
    yaxis: {
      tickfont: { size: 11, color: "#7A756F" },
      automargin: true,
      showline: false,
      showgrid: true,
      gridcolor: "rgba(0,0,0,0.06)",
      ...normalizeAxis(chart.layout?.yaxis),
    },
    title: chart.layout?.title ? {
      font: { size: 15, family: 'Inter, sans-serif', color: '#1A1816' },
      x: 0.5,
      xanchor: 'center',
      ...chart.layout.title,
    } : undefined,
    legend: {
      orientation: 'h',
      y: -0.25,
      x: 0.5,
      xanchor: 'center',
      bgcolor: '#FFFFFF',
      bordercolor: 'rgba(0,0,0,0.08)',
      borderwidth: 1,
      font: { size: 11, color: '#3A3734' },
      ...chart.layout?.legend,
    },
    annotations: chart.layout?.annotations?.map(ann => ({
      font: { color: '#1A1816', size: 12 },
      bgcolor: '#FFFFFF',
      bordercolor: 'rgba(0,0,0,0.1)',
      borderwidth: 1,
      borderpad: 4,
      ...ann,
    })),
  };

  const finalLayout = applyTheme({
    ...customLayout,
    paper_bgcolor: '#FFFFFF',
    plot_bgcolor: '#FFFFFF',
    uniformtext: {
      minsize: 10,
      mode: 'hide',
    },
  });

  return (
    <div className={`plotly-wrap ${className}`}>
      <Plot
        data={dataWithTheme}
        layout={finalLayout}
        config={CONFIG}
        style={{ width: '100%', height: `${height}px` }}
        useResizeHandler
      />
    </div>
  );
}

function detectChartType(data) {
  if (!data || !data[0]) return 'line';
  const trace = data[0];
  if (trace.type === 'bar') return 'bar';
  if (trace.type === 'pie') return 'pie';
  if (trace.type === 'scatter' && trace.mode === 'markers') return 'scatter';
  if (trace.fill === 'tozeroy' || trace.fillcolor) return 'area';
  return 'line';
}

function hexToRgb(hex) {
  if (!hex) return '89, 173, 247';
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
    : '89, 173, 247';
}

function normalizeAxis(axis = {}) {
  const rawTitle = axis?.title;
  const titleText = typeof rawTitle === 'string'
    ? rawTitle
    : rawTitle?.text;

  return {
    ...axis,
    title: titleText ? {
      ...(typeof rawTitle === 'object' ? rawTitle : {}),
      text: /^<b>.*<\/b>$/.test(titleText) ? titleText : `<b>${titleText}</b>`,
      font: {
        size: 12,
        color: '#3A3734',
        family: 'Inter, sans-serif',
        ...(rawTitle?.font || {}),
      },
      standoff: rawTitle?.standoff || 18,
    } : rawTitle,
  };
}

function normalizeBrandColor(color, fallback = '#59ADF7') {
  if (!color || typeof color !== 'string') return fallback;

  const normalized = color.toLowerCase().trim();
  const map = {
    '#ff7a00': '#E4002B',
    '#ff7a40': '#E4002B',
    '#ff4d00': '#E4002B',
    '#ffaa00': '#59ADF7',
    '#f59e0b': '#59ADF7',
    '#003366': '#0904AE',
    '#006600': '#112F44',
    '#007755': '#112F44',
    '#660099': '#0904AE',
    '#999': '#6B7280',
    '#bbb': '#B8B0A8',
    '#888888': '#6B7280',
    '#444444': '#37424A',
    '#555': '#37424A',
    '#2b2b2b': '#1B272F',
  };

  return map[normalized] || color;
}

function normalizeColorscale(colorscale) {
  return colorscale.map(([stop, color], index) => {
    const fallback = DAREEDA_THEME.colorway[index % DAREEDA_THEME.colorway.length];
    return [stop, normalizeBrandColor(color, fallback)];
  });
}
