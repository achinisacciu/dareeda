class DatetimeFeaturesRule:
    def apply(self, df, semantics):
        date_cols = [c for c, v in semantics.items() if v["semantic_type"] == "date"]

        features = []

        for d in date_cols:
            features.extend([
                {
                    "name": f"{d}_year",
                    "formula": f"year({d})",
                    "confidence": 0.9,
                    "status": "pending",
                    "type": "derived_feature",
                },
                {
                    "name": f"{d}_month",
                    "formula": f"month({d})",
                    "confidence": 0.9,
                    "status": "pending",
                    "type": "derived_feature",
                },
            ])

        return features
