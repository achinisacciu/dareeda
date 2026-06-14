import datetime

import polars as pl
from eda.modules.univariate import run


def test_univariate_datetime_builds_year_and_month_charts():
    dates = [datetime.datetime(2024, (i % 12) + 1, (i % 28) + 1) for i in range(48)]
    values = list(range(48))
    df = pl.DataFrame({"event_date": dates, "value": values})

    result = run(
        df=df,
        df_full=df,
        semantic_types={"event_date": "datetime", "value": "numeric_continuous"},
        groups={"datetime": ["event_date"], "numeric_continuous": ["value"]},
    )

    event_date = result["event_date"]
    assert "error" not in event_date
    assert event_date["semantic_type"] == "datetime"
    assert event_date["stats"]["n_unique"] == 48
    assert event_date["charts"]["by_year"]["data"]
    assert event_date["charts"]["by_month"]["data"]
