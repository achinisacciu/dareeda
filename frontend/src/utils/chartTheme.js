// ============================================
// DAREEDA CHART THEME - Light Premium SaaS
// ============================================

export const DAREEDA_THEME = {
  font: {
    family: "Inter, -apple-system, sans-serif",
    color: "#3A3734",   // --color-neutral-800
    size: 12
  },

  paper_bgcolor: "#FFFFFF",
  plot_bgcolor:  "#FFFFFF",

  colorway: [
    "#59ADF7",  // Ocean Blue
    "#E4002B",  // Leonardo Red
    "#0904AE",  // Deep Space Blue
    "#112F44",  // Deep Teal
    "#37424A",  // Slate
    "#1B272F",  // Charcoal
  ],

  xaxis: {
    gridcolor: "rgba(0,0,0,0.06)",
    linecolor: "rgba(0,0,0,0.15)",
    linewidth: 1,
    zeroline: false,
    tickfont:  { color: "#7A756F", size: 11 },  // --color-neutral-600
    automargin: true,
  },

  yaxis: {
    gridcolor: "rgba(0,0,0,0.06)",
    linecolor: "rgba(0,0,0,0.15)",
    linewidth: 1,
    zeroline: false,
    tickfont:  { color: "#7A756F", size: 11 },
    automargin: true,
  },

  margin: { t: 40, r: 24, b: 60, l: 64 },

  legend: {
    bgcolor: "rgba(255,255,255,0.9)",
    bordercolor: "rgba(0,0,0,0.08)",
    borderwidth: 1,
    font: { color: "#3A3734", size: 11 },
  },

  hoverlabel: {
    bgcolor: "#FFFFFF",
    bordercolor: "rgba(0,0,0,0.12)",
    font: { color: "#1A1816", family: "Inter, sans-serif", size: 12 },
  },
};

export const applyTheme = (layout = {}) => ({
  ...DAREEDA_THEME,
  ...layout,
  xaxis: { ...DAREEDA_THEME.xaxis, ...(layout.xaxis || {}) },
  yaxis: { ...DAREEDA_THEME.yaxis, ...(layout.yaxis || {}) },
  legend: { ...DAREEDA_THEME.legend, ...(layout.legend || {}) },
  hoverlabel: { ...DAREEDA_THEME.hoverlabel, ...(layout.hoverlabel || {}) },
});
