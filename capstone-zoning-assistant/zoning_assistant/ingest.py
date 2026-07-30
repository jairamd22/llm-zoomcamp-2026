"""Ingestion: load the zoning corpus (and parcel records) into minsearch.

minsearch is in-memory, so ingestion runs at application startup —
matching the reference pattern. Project 4 in the portfolio roadmap
replaces this with a scheduled dlt pipeline.
"""

import os

import pandas as pd

from zoning_assistant.minsearch import Index

DATA_PATH = os.getenv("DATA_PATH", "data/zoning.csv")
PARCELS_PATH = os.getenv("PARCELS_PATH", "data/parcels.csv")

TEXT_FIELDS = ["section", "district", "category", "title", "text"]


def load_index(data_path: str = DATA_PATH) -> Index:
    """Build the zoning-rule search index from the CSV corpus."""
    df = pd.read_csv(data_path)
    documents = df.to_dict(orient="records")

    index = Index(
        text_fields=TEXT_FIELDS,
        keyword_fields=["id"],
    )
    index.fit(documents)
    return index


def load_parcels(parcels_path: str = PARCELS_PATH) -> dict:
    """Load parcel records keyed by parcel_id (and by lowercase address)."""
    df = pd.read_csv(parcels_path)
    records = df.to_dict(orient="records")
    by_key = {}
    for r in records:
        by_key[r["parcel_id"].lower()] = r
        by_key[r["address"].lower()] = r
    return by_key
