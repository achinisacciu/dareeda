import polars as pl
from core.config import settings
from core.sampling import get_sample_info, maybe_sample


def test_no_sampling_small():
    df = pl.DataFrame({"x": list(range(1000))})
    result, sampled, sample_n = maybe_sample(df)
    assert not sampled
    assert sample_n is None
    assert len(result) == 1000

def test_sampling_large():
    df = pl.DataFrame({"x": list(range(settings.sampling_threshold + 1000))})
    result, sampled, sample_n = maybe_sample(df)
    assert sampled
    assert sample_n == settings.sample_size
    assert len(result) == settings.sample_size

def test_sample_info_below():
    info = get_sample_info(50_000)
    assert not info["will_sample"]

def test_sample_info_above():
    info = get_sample_info(200_000)
    assert info["will_sample"]
    assert info["sample_rows"] == settings.sample_size
