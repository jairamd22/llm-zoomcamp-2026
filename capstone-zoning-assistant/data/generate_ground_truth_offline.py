"""
Offline ground-truth generator for retrieval evaluation.

Produces data/ground-truth-retrieval.csv with ~5 user-style questions per
zoning record, using paraphrase templates and domain synonym substitution
("ADU" vs "granny flat", "setback" vs "how far from the property line",
etc.). This intentionally includes synonym-heavy phrasings so the
evaluation can *measure* keyword search's paraphrase gap instead of
assuming it.

The LLM-generated alternative (used for the reported final numbers if you
have an API key) is in notebooks/evaluation-data-generation.ipynb and
writes to the same CSV with the same columns: id, question.

Run:  python data/generate_ground_truth_offline.py
"""

import csv
import random
from pathlib import Path

import pandas as pd

random.seed(1)
HERE = Path(__file__).parent

SYN = {
    "accessory dwelling unit": ["ADU", "granny flat", "backyard cottage",
                                "secondary apartment", "guest house"],
    "setback": ["setback", "distance from the property line",
                "how far from the lot line", "yard requirement"],
    "height": ["height", "how tall", "number of stories", "vertical limit"],
    "lot coverage": ["lot coverage", "impervious cover", "FAR",
                     "how much of my lot I can build on"],
    "permit": ["permit", "approval", "city sign-off", "paperwork"],
    "flood": ["flood zone", "floodplain", "FEMA zone", "flood risk area"],
}


def pick(key):
    return random.choice(SYN.get(key, [key]))


TEMPLATES = {
    "accessory dwelling unit": [
        "Can I build a {syn} on my lot in the {district} district?",
        "What are the size limits for a {syn}?",
        "Do I need extra parking for a {syn}?",
        "Where on my property can I put a {syn}?",
        "How big can a {syn} be and how tall?",
    ],
    "setbacks": [
        "What is the {syn} in the {district} zone?",
        "How close to the street can I build in {district}?",
        "What are the required yards for a house zoned {district}?",
        "Can my roof eaves stick into the required yard?",
        "What's the {syn} on a corner lot in {district}?",
    ],
    "height": [
        "What's the {syn} limit for buildings in {district}?",
        "How is building {syn} measured in the {district} district?",
        "Can my chimney go above the {syn} limit in {district}?",
        "What is the tallest structure allowed in {district}?",
        "Is there a way to build taller than the {syn} limit in {district}?",
    ],
    "lot coverage": [
        "What's the maximum {syn} in the {district} district?",
        "Does a deck count toward {syn} in {district}?",
        "How much {syn} is allowed on a {district} lot?",
        "What is the FAR limit in {district}?",
        "Do covered porches count against {syn}?",
    ],
    "lot standards": [
        "What's the minimum lot size in the {district} district?",
        "My lot is smaller than the minimum in {district} — can I still build?",
        "What are the rules for small substandard lots?",
        "How wide does a lot have to be to build a house?",
        "Can I develop a lot platted before the current code?",
    ],
    "permits": [
        "Do I need a {syn} to {act}?",
        "What documents do I need for a residential building {syn}?",
        "What {syn}s are required before pouring a foundation?",
        "How do I get a variance from a setback rule?",
        "What's the process to rezone my property?",
    ],
    "flood": [
        "What are the rules for building in a {syn}?",
        "My parcel is in FEMA zone AE — what does that mean for construction?",
        "How high does the finished floor need to be in the {syn}?",
        "Are there limits on building near a creek or waterway?",
        "Can I add fill to my lot in the {syn}?",
    ],
    "historic": [
        "What approvals do I need in a historic district?",
        "Can I renovate the outside of a house in a historic overlay?",
        "Do I need a Certificate of Appropriateness to remodel?",
        "What are the rules for new construction in a historic overlay?",
        "Does demolishing an old house need historic review?",
    ],
    "parking": [
        "How many parking spaces do I need for a {use}?",
        "What are the off-street parking requirements?",
        "Are parking minimums reduced near transit?",
        "Can required parking be located off-site?",
        "How much parking does a restaurant need?",
    ],
    "use regulations": [
        "Can I run a business out of my home?",
        "Is a duplex allowed in the {district} district?",
        "What commercial uses are allowed in {district}?",
        "What happens if a nonconforming use stops for a while?",
        "How many units per acre are allowed in {district}?",
    ],
    "short-term rental": [
        "What do I need to legally rent my house on Airbnb?",
        "Can I use my ADU as a short-term rental?",
        "Is there a cap on non-owner-occupied short-term rentals?",
        "Do short-term rentals need a license?",
        "What are the rules for renting for under 30 days?",
    ],
    "fences": [
        "How tall can my fence be in the front yard?",
        "Do I need a permit for an 8 foot fence?",
        "What are the fence height rules next to a commercial lot?",
        "Can I build a 6 foot fence in my backyard?",
        "What are the fence placement requirements?",
    ],
    "trees": [
        "Do I need a permit to cut down a big tree on my property?",
        "What counts as a protected or heritage tree?",
        "Can I remove a tree that's in the way of my addition?",
        "What mitigation is required for tree removal?",
        "What size tree requires a removal permit?",
    ],
    "signs": [
        "What signs can I put up in a residential neighborhood?",
        "Are billboards allowed in residential districts?",
        "Can I put a sign up for my home business?",
        "How big can a yard sign be?",
        "What are the sign rules for houses?",
    ],
    "drainage": [
        "What stormwater requirements apply if I add a big driveway?",
        "Do I need detention for new impervious cover?",
        "What are the runoff rules for new construction?",
        "When is a drainage plan required?",
        "How does the city regulate stormwater from my project?",
    ],
    "compatibility": [
        "What buffer is required between commercial and residential lots?",
        "Are there noise limits for a business next to houses?",
        "What are the compatibility rules near single-family zoning?",
        "How tall can a commercial building be next to homes?",
        "What screening is required next to a residential district?",
    ],
    "density bonus": [
        "How can a project get extra height or FAR?",
        "What is the density bonus program?",
        "What affordable housing is required for a height bonus?",
        "Can I exceed the base height limit legally?",
        "What do I get for including affordable units?",
    ],
}

ACTS = ["build a garage", "remodel a kitchen", "demolish a shed",
        "pour a foundation", "add a pool", "build a carport"]
USES = ["duplex", "single-family home", "apartment building", "retail store",
        "office"]


def main():
    df = pd.read_csv(HERE / "zoning.csv")
    rows = []
    for _, rec in df.iterrows():
        cat = rec["category"]
        templates = TEMPLATES.get(cat, ["What does section {section} say about {title}?"])
        district = rec["district"].split(";")[0]
        seen = set()
        for t in templates:
            q = t.format(
                syn=pick("accessory dwelling unit") if cat == "accessory dwelling unit"
                else pick("setback") if cat == "setbacks"
                else pick("height") if cat == "height"
                else pick("lot coverage") if cat == "lot coverage"
                else pick("permit") if cat == "permits"
                else pick("flood") if cat == "flood"
                else "",
                district=district,
                act=random.choice(ACTS),
                use=random.choice(USES),
                section=rec["section"],
                title=rec["title"],
            )
            if q not in seen:
                seen.add(q)
                rows.append({"id": rec["id"], "question": q})

    out = HERE / "ground-truth-retrieval.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "question"])
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} questions to {out}")


if __name__ == "__main__":
    main()
