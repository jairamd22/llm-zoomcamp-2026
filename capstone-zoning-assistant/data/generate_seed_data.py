"""
Generates the seed dataset for the Property & Zoning Research Assistant.

The dataset is a *synthetic but realistic* zoning code for a single city
("City of Riverbend"), modeled on the structure of Austin, TX's Land
Development Code (district naming, rule categories, numbering scheme).

Why synthetic: it makes the repo fully self-contained and reproducible
with zero download steps, and avoids shipping a snapshot of a real
municipal code that would immediately be stale. Swapping in a real city's
code (e.g. from Municode or an open-data portal) only requires producing
a CSV with the same columns.

Output:
    data/zoning.csv   -- one row per zoning rule/section (the retrieval corpus)
    data/parcels.csv  -- one row per parcel (property records)

Run:  python data/generate_seed_data.py
"""

import csv
import hashlib
import random
from pathlib import Path

random.seed(42)

HERE = Path(__file__).parent

# ---------------------------------------------------------------------------
# Districts (Austin-style naming)
# ---------------------------------------------------------------------------

RESIDENTIAL = {
    "SF-1": dict(name="Single-Family Large Lot", min_lot=10000, height=35,
                 coverage=35, far=0.35, front=40, side=10, rear=20),
    "SF-2": dict(name="Single-Family Standard Lot", min_lot=5750, height=35,
                 coverage=40, far=0.40, front=25, side=5, rear=10),
    "SF-3": dict(name="Family Residence", min_lot=5750, height=35,
                 coverage=40, far=0.40, front=25, side=5, rear=10),
    "MF-1": dict(name="Multifamily Limited Density", min_lot=8000, height=40,
                 coverage=45, far=0.60, front=25, side=10, rear=15),
    "MF-2": dict(name="Multifamily Low Density", min_lot=8000, height=40,
                 coverage=50, far=0.80, front=25, side=10, rear=15),
    "MF-3": dict(name="Multifamily Medium Density", min_lot=8000, height=60,
                 coverage=55, far=1.00, front=15, side=10, rear=15),
}

COMMERCIAL = {
    "GR": dict(name="Community Commercial", height=60, coverage=75, far=1.00,
               front=10, side=0, rear=10),
    "CS": dict(name="General Commercial Services", height=60, coverage=80,
               far=2.00, front=10, side=0, rear=10),
    "LO": dict(name="Limited Office", height=40, coverage=50, far=0.70,
               front=25, side=10, rear=15),
}

ALL_DISTRICTS = list(RESIDENTIAL) + list(COMMERCIAL)


def make_id(section, title):
    return hashlib.md5(f"{section}|{title}".encode()).hexdigest()[:8]


rules = []


def add(section, district, category, title, text):
    rules.append({
        "id": make_id(section, title),
        "section": section,
        "district": district,
        "category": category,
        "title": title,
        "text": " ".join(text.split()),
    })


# ---------------------------------------------------------------------------
# Article 2 -- District site development regulations
# ---------------------------------------------------------------------------

for i, (code, d) in enumerate(RESIDENTIAL.items(), start=1):
    base = f"2.{i}"
    add(f"{base}.1", code, "lot standards",
        f"Minimum lot size in {code}",
        f"""In the {code} ({d['name']}) zoning district, the minimum lot
        area for a detached single-family or residential use is
        {d['min_lot']:,} square feet. A lot legally platted before the
        effective date of this code that does not meet the minimum lot
        area is a legal nonconforming small lot and may be developed
        subject to the small-lot standards in Section 6.3.""")
    add(f"{base}.2", code, "height",
        f"Maximum building height in {code}",
        f"""The maximum height of a principal structure in the {code}
        ({d['name']}) district is {d['height']} feet, measured from the
        average of the highest and lowest grade adjacent to the building
        to the highest point of the roof. Chimneys, antennas, and
        rooftop mechanical equipment may exceed the height limit by up
        to 5 feet if set back from all roof edges.""")
    add(f"{base}.3", code, "lot coverage",
        f"Maximum impervious cover and building coverage in {code}",
        f"""In the {code} district, maximum building coverage is
        {d['coverage']} percent of gross lot area and maximum
        floor-to-area ratio (FAR) is {d['far']}. Building coverage
        includes the principal structure, accessory buildings larger
        than 120 square feet, and covered porches. Uncovered decks,
        pools, and at-grade patios are excluded from building coverage
        but count toward impervious cover, which may not exceed
        {min(d['coverage'] + 10, 65)} percent.""")
    add(f"{base}.4", code, "setbacks",
        f"Setback requirements in {code}",
        f"""Required yards in the {code} ({d['name']}) district are:
        front setback {d['front']} feet, interior side setback
        {d['side']} feet, and rear setback {d['rear']} feet. On a corner
        lot, the street side setback is 15 feet. Eaves, bay windows, and
        similar architectural features may project up to 2 feet into a
        required yard. No setback reduction is permitted within a
        floodplain overlay.""")

for j, (code, d) in enumerate(COMMERCIAL.items(), start=len(RESIDENTIAL) + 1):
    base = f"2.{j}"
    add(f"{base}.1", code, "height",
        f"Maximum building height in {code}",
        f"""The maximum height in the {code} ({d['name']}) district is
        {d['height']} feet. Additional height up to 25 percent above the
        limit may be granted through the density bonus program in
        Section 7.4 in exchange for on-site affordable housing or
        ground-floor pedestrian-oriented uses.""")
    add(f"{base}.2", code, "lot coverage",
        f"Maximum coverage and FAR in {code}",
        f"""In the {code} district, maximum building coverage is
        {d['coverage']} percent and maximum floor-to-area ratio is
        {d['far']}. There is no minimum lot size, but lots abutting a
        residential district must provide the compatibility buffer
        described in Section 5.2.""")
    add(f"{base}.3", code, "setbacks",
        f"Setback requirements in {code}",
        f"""Required setbacks in the {code} district are: front
        {d['front']} feet, interior side {d['side']} feet, rear
        {d['rear']} feet. Where a {code} lot shares a property line with
        a lot zoned SF-1, SF-2, or SF-3, the abutting side or rear
        setback increases to 25 feet and a solid screening fence or
        vegetative buffer at least 6 feet high is required.""")

# ---------------------------------------------------------------------------
# Article 3 -- Accessory dwelling units (ADUs)
# ---------------------------------------------------------------------------

add("3.1", "SF-1;SF-2;SF-3", "accessory dwelling unit",
    "Where accessory dwelling units are permitted",
    """One accessory dwelling unit (ADU), also called a secondary
    apartment, granny flat, or backyard cottage, is permitted by right on
    any lot in the SF-1, SF-2, or SF-3 district that contains a
    single-family residence, provided the lot is at least 5,750 square
    feet. ADUs are not permitted on lots developed with a duplex or
    two-family residential use.""")
add("3.2", "SF-1;SF-2;SF-3", "accessory dwelling unit",
    "ADU size and height limits",
    """An accessory dwelling unit may not exceed 1,100 square feet of
    gross floor area or a floor-to-area ratio of 0.15, whichever is
    smaller, and may not exceed two stories or 30 feet in height. An ADU
    above a detached garage is measured to the same height limit. The ADU
    counts toward the maximum building coverage and impervious cover of
    the lot.""")
add("3.3", "SF-1;SF-2;SF-3", "accessory dwelling unit",
    "ADU placement and separation",
    """A detached accessory dwelling unit must be located behind the rear
    wall plane of the principal residence, at least 10 feet from the
    principal structure, and must observe a 5-foot side and rear setback.
    An ADU may not be located between the principal structure and the
    front lot line.""")
add("3.4", "SF-1;SF-2;SF-3", "accessory dwelling unit",
    "ADU parking and occupancy",
    """One additional off-street parking space is required for an
    accessory dwelling unit, except that no additional parking is
    required if the lot is within one-quarter mile of a high-frequency
    transit corridor. Either the principal residence or the ADU must be
    owner-occupied to use the unit as a short-term rental; long-term
    rental of either unit is permitted without owner occupancy.""")

# ---------------------------------------------------------------------------
# Article 4 -- Permits and review procedures
# ---------------------------------------------------------------------------

add("4.1", "ALL", "permits",
    "When a building permit is required",
    """A building permit is required before constructing, enlarging,
    structurally altering, or demolishing any building or structure,
    including foundations, additions, garages, carports over 200 square
    feet, and swimming pools. A permit is not required for one-story
    detached accessory buildings of 120 square feet or less, fences 6
    feet or lower, at-grade patios, or ordinary repairs such as painting
    and flooring.""")
add("4.2", "ALL", "permits",
    "Documents required for a residential building permit",
    """A residential building permit application must include a site plan
    showing lot lines, setbacks, existing and proposed structures, and
    impervious cover calculations; construction drawings; an energy code
    compliance form; and, if the lot is in a regulated floodplain, an
    elevation certificate. Projects that add more than 5,000 square feet
    of impervious cover also require a drainage plan.""")
add("4.3", "ALL", "permits",
    "Foundation and site work permits",
    """Before pouring a foundation, the applicant must hold an approved
    building permit, schedule a setback/form inspection, and obtain a
    separate site development permit if the project disturbs more than
    one acre or is within 150 feet of a waterway. Pouring a foundation
    before the form inspection is a stop-work violation subject to a
    fine of up to $2,000 per day.""")
add("4.4", "ALL", "permits",
    "Demolition permits and historic review",
    """A demolition permit is required to remove any structure over 120
    square feet. If the structure is 45 years old or older, or is within
    a historic overlay district, the application is routed to the
    Historic Preservation Office for review before issuance, which may
    add 30 to 90 days to the timeline.""")
add("4.5", "ALL", "permits",
    "Variances and the Board of Adjustment",
    """A property owner may request a variance from a site development
    regulation (such as a setback or height limit) from the Board of
    Adjustment. The board may grant a variance only on a finding of
    hardship unique to the property that is not self-created and that the
    variance will not alter the character of the area. Use variances --
    permitting a use not allowed in the district -- are prohibited.""")
add("4.6", "ALL", "permits",
    "Rezoning applications",
    """A request to change a property's zoning district requires a
    rezoning application, notification of owners within 300 feet, a
    public hearing before the Planning Commission, and final approval by
    City Council. If owners of 20 percent or more of the land within 200
    feet protest, approval requires a three-fourths vote of Council.""")

# ---------------------------------------------------------------------------
# Article 5 -- Overlays and environmental constraints
# ---------------------------------------------------------------------------

add("5.1", "ALL", "flood",
    "Development in the floodplain overlay",
    """Within the 100-year floodplain (FEMA Zone AE or A), the lowest
    finished floor of any new habitable structure must be at least 2 feet
    above the base flood elevation, and an elevation certificate is
    required at permit application and again before the certificate of
    occupancy. Fill may not raise flood elevations on adjacent
    properties. In the floodway itself, new habitable structures are
    prohibited.""")
add("5.2", "GR;CS;LO", "compatibility",
    "Compatibility buffer next to residential districts",
    """A commercial lot that abuts or is across an alley from a lot zoned
    SF-1, SF-2, SF-3, MF-1, MF-2, or MF-3 must provide a compatibility
    buffer: no structure over 30 feet in height within 50 feet of the
    residential property line, a landscaped buffer strip at least 10 feet
    wide, and no outdoor amplified sound between 10 p.m. and 7 a.m.""")
add("5.3", "ALL", "historic",
    "Historic overlay district requirements",
    """Within a historic overlay district (-H suffix), exterior
    alterations visible from a public street require a Certificate of
    Appropriateness from the Historic Landmark Commission before a
    building permit may be issued. Routine maintenance with in-kind
    materials is exempt. New construction in the overlay must be
    compatible in height, scale, and setback with contributing
    structures.""")
add("5.4", "ALL", "trees",
    "Protected tree removal",
    """A permit is required to remove any tree 19 inches or greater in
    diameter at breast height. Heritage trees (24 inches or greater of
    protected species) may be removed only if the tree is dead,
    diseased, or an imminent hazard, or if preservation would prevent
    reasonable use of the property; mitigation planting or fee-in-lieu
    is required.""")
add("5.5", "ALL", "flood",
    "Impervious cover near waterways",
    """Within 150 feet of a classified waterway, impervious cover is
    limited to 30 percent of net site area regardless of the underlying
    zoning district, and a 50-foot vegetated critical water quality
    buffer must remain undisturbed except for permitted utility and
    trail crossings.""")

# ---------------------------------------------------------------------------
# Article 6 -- Uses, nonconformity, small lots
# ---------------------------------------------------------------------------

add("6.1", "ALL", "use regulations",
    "Home occupations",
    """A home occupation is permitted in any residential district if it
    is conducted entirely within the dwelling or ADU, occupies no more
    than 25 percent of the floor area, has no more than one nonresident
    employee on site, generates no more than 10 customer vehicle trips
    per day, and involves no outdoor storage or display.""")
add("6.2", "ALL", "use regulations",
    "Nonconforming uses and structures",
    """A use or structure that was lawful when established but does not
    conform to current regulations may continue. A nonconforming
    structure may be repaired or maintained, but an enlargement must
    conform to current setbacks and height limits. If a nonconforming
    use is discontinued for more than 90 consecutive days, it may not be
    resumed.""")
add("6.3", "SF-1;SF-2;SF-3", "lot standards",
    "Small lot development standards",
    """A legal nonconforming small lot (platted before the effective
    date, smaller than the district minimum) may be developed with one
    single-family residence if the lot is at least 2,500 square feet and
    25 feet wide. Small lots use reduced setbacks: front 15 feet, side 5
    feet, rear 5 feet, and maximum height is limited to 30 feet.""")
add("6.4", "MF-1;MF-2;MF-3", "use regulations",
    "Duplex and multifamily use permissions",
    """Duplex (two-family) residential use is permitted in SF-3 and all
    MF districts. Multifamily use of three or more units is permitted
    only in MF-1, MF-2, and MF-3. In MF-1 the maximum density is 17 units
    per acre; in MF-2, 23 units per acre; in MF-3, 36 units per acre.""")
add("6.5", "GR;CS", "use regulations",
    "Permitted commercial uses in GR and CS",
    """The GR district permits retail sales, restaurants, personal
    services, medical offices, and similar community-serving commercial
    uses. The CS district additionally permits vehicle repair, outdoor
    storage as an accessory use, warehousing under 10,000 square feet,
    and limited light manufacturing. Residential mixed use is permitted
    above the ground floor in both districts.""")
add("6.6", "ALL", "parking",
    "Off-street parking requirements",
    """Minimum off-street parking: single-family residence, 2 spaces;
    duplex, 2 spaces per unit; multifamily, 1.5 spaces per unit;
    retail and restaurant, 1 space per 300 square feet of gross floor
    area; office, 1 space per 350 square feet. Parking minimums are
    reduced by 50 percent within one-quarter mile of a high-frequency
    transit corridor and may be met off-site within 500 feet by
    agreement.""")
add("6.7", "ALL", "short-term rental",
    "Short-term rental licensing",
    """Operating a short-term rental (a dwelling rented for periods
    under 30 days) requires an annual operating license, proof of
    property insurance, and a local responsible party available 24
    hours. Type 2 (non-owner-occupied) short-term rentals are capped at
    3 percent of the dwelling units in each census tract and are not
    permitted in ADUs unless the principal residence is
    owner-occupied.""")

# ---------------------------------------------------------------------------
# Article 7 -- Miscellaneous / bonus programs
# ---------------------------------------------------------------------------

add("7.1", "ALL", "fences",
    "Fence height and placement",
    """A fence in a residential district may be up to 6 feet high in a
    side or rear yard and up to 4 feet high in the required front yard.
    A solid fence up to 8 feet is permitted along a property line shared
    with a commercial district or an arterial street. Fences over 6 feet
    require a building permit.""")
add("7.2", "ALL", "signs",
    "Signs in residential districts",
    """In residential districts, only the following signs are permitted:
    one non-illuminated sign up to 6 square feet per lot, temporary real
    estate signs, and one home occupation nameplate up to 2 square feet.
    Off-premise advertising signs (billboards) are prohibited citywide
    in residential districts.""")
add("7.3", "ALL", "drainage",
    "Stormwater detention requirements",
    """Development that increases impervious cover by more than 1,000
    square feet on a lot must demonstrate that post-development peak
    stormwater runoff does not exceed pre-development levels for the
    2-year, 10-year, and 100-year storms, using on-site detention,
    rain gardens, or payment into the regional stormwater program where
    available.""")
add("7.4", "GR;CS;MF-3", "density bonus",
    "Density bonus program",
    """In the GR, CS, and MF-3 districts, a project may exceed the base
    height limit by up to 25 percent and the base FAR by up to 0.5 if at
    least 10 percent of residential units are affordable to households
    at 60 percent of median family income for 40 years, or an equivalent
    fee-in-lieu is paid.""")

# ---------------------------------------------------------------------------
# Parcels
# ---------------------------------------------------------------------------

STREETS = ["Oakmont Ave", "Cedar Bend Dr", "Riverside Blvd", "Juniper St",
           "Lamar Ln", "Pecan Grove Rd", "Bluff View Ct", "Mesquite Way"]

parcels = []
for n in range(1, 41):
    district = random.choice(ALL_DISTRICTS)
    res = district in RESIDENTIAL
    lot = (random.choice([2800, 4200, 5750, 6500, 7200, 8400, 10500, 12000])
           if res else random.choice([7000, 12000, 20000, 32000]))
    parcels.append({
        "parcel_id": f"RB-{2400 + n}",
        "address": f"{random.randint(100, 9899)} {random.choice(STREETS)}",
        "zoning_district": district,
        "lot_size_sqft": lot,
        "lot_width_ft": random.choice([25, 40, 50, 60, 75, 100]),
        "land_use": ("single-family" if res and district.startswith("SF")
                     else "multifamily" if res else "commercial"),
        "flood_zone": random.choice(["X", "X", "X", "X", "AE"]),
        "historic_overlay": random.choice(["no", "no", "no", "yes"]),
        "year_built": random.choice([0, 1948, 1962, 1975, 1988, 1996, 2004, 2015]),
    })

# ---------------------------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------------------------

with open(HERE / "zoning.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rules[0].keys()))
    w.writeheader()
    w.writerows(rules)

with open(HERE / "parcels.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(parcels[0].keys()))
    w.writeheader()
    w.writerows(parcels)

print(f"Wrote {len(rules)} zoning rules and {len(parcels)} parcels.")
