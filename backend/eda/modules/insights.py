def run(df, df_full, semantic_types, groups):
    """Aggrega i risultati di tutti i moduli in insight prioritizzati."""
    return {
        "generated": True,
        "note": "Gli insight sono generati dinamicamente dal frontend aggregando i risultati di overview, data_quality, univariate, bivariate, ml e inference.",
    }

