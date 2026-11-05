"""What the screen looks at.

Everything here comes from FRED (free, no API key). Credit series are
ICE BofA option-adjusted spreads (OAS) in percent; we convert to basis
points. Rates are constant-maturity Treasury yields in percent.

Note: since April 2026 FRED only serves the last ~3 years of ICE BofA
history, so z-scores use a 1-year window and percentiles are over
roughly 3 years.
"""

# key -> (FRED series id, label)
CREDIT = {
    "ASIA_EM": ("BAMLEMRACRPIASIAOAS", "Asia EM Corp OAS"),
    "ASIA_EM_LIQ": ("BAMLEMALLCRPIASIAUSOAS", "Asia USD EM Liquid Corp OAS"),
    "LATAM_EM": ("BAMLEMRLCRPILAOAS", "LatAm EM Corp OAS"),
    "EMEA_EM": ("BAMLEMRECRPIEMEAOAS", "EMEA EM Corp OAS"),
    "EM_CORP": ("BAMLEMCBPIOAS", "EM Corp OAS"),
    "EM_HG": ("BAMLEMIBHGCRPIOAS", "EM High Grade Corp OAS"),
    "EM_HY": ("BAMLEMHBHYCRPIOAS", "EM High Yield Corp OAS"),
    "US_IG": ("BAMLC0A0CM", "US IG Corp OAS"),
    "US_BBB": ("BAMLC0A4CBBB", "US BBB Corp OAS"),
    "US_HY": ("BAMLH0A0HYM2", "US HY OAS"),
}

RATES = {
    "UST2": ("DGS2", "UST 2y yield"),
    "UST5": ("DGS5", "UST 5y yield"),
    "UST10": ("DGS10", "UST 10y yield"),
    "UST30": ("DGS30", "UST 30y yield"),
}

# Relative-value pairs: name -> (long-spread leg, short-spread leg, label)
# Value = leg A spread minus leg B spread, in bp.
# Wide (high z) => A is cheap vs B. Tight (low z) => A is rich vs B.
PAIRS = {
    "ASIA_vs_EM": ("ASIA_EM", "EM_CORP", "Asia vs EM Corp"),
    "ASIA_vs_LATAM": ("ASIA_EM", "LATAM_EM", "Asia vs LatAm"),
    "ASIA_vs_EMEA": ("ASIA_EM", "EMEA_EM", "Asia vs EMEA"),
    "ASIA_vs_USBBB": ("ASIA_EM", "US_BBB", "Asia EM vs US BBB"),
    "EMHG_vs_USIG": ("EM_HG", "US_IG", "EM HG vs US IG"),
    "EMHY_vs_USHY": ("EM_HY", "US_HY", "EM HY vs US HY"),
    "EM_HY_HG": ("EM_HY", "EM_HG", "EM HY-HG decompression"),
}

# Curve trades on Treasuries, in bp.
# slope = long - short ; fly = 2*belly - wing1 - wing2
CURVES = {
    "UST_2s10s": ("slope", ("UST2", "UST10"), "UST 2s10s"),
    "UST_5s30s": ("slope", ("UST5", "UST30"), "UST 5s30s"),
    "UST_2s5s10s": ("fly", ("UST2", "UST5", "UST10"), "UST 2s5s10s fly"),
}


def all_series_ids():
    return {k: v[0] for k, v in {**CREDIT, **RATES}.items()}


def label(key):
    for table in (CREDIT, RATES):
        if key in table:
            return table[key][1]
    for table in (PAIRS, CURVES):
        if key in table:
            return table[key][-1]
    return key
