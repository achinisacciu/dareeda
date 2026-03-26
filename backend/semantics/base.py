class BaseDetector:
    name = "base"

    def detect(self, df, col_name):
        """
        Returns:
        {
            "semantic_type": str,
            "confidence": float (0-1),
            "meta": dict
        }
        """
        raise NotImplementedError
