"""Fill build/figures-manifest.json with files, pixel sizes and verbatim figure metadata.

Run after figures.py. Updates entries in place (order and existing keys preserved).
Text fields are verbatim from the PDF text layer (layout whitespace collapsed, line-break
hyphenation none, ligatures ﬁ/ﬂ expanded). Labels such as "Source:", "Sources:", "Notes:",
"Data:" and "Created by Urban Institute." are kept as printed. `alt` is our own wording.
Extra keys: panel_titles / panel_meta (image-sets), group_title (super-title shared by
several entries), meta_note (provenance caveats, not for display).
For entries with several files, width/height are lists parallel to `files`.
"""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "build/figures-manifest.json"
IMG = ROOT / "docs/assets/img"

META = {
    "mpc-p01-cover": dict(
        alt="Elevated CTA ‘L’ train curving past historic and modern high-rise buildings, a colorful mural and a surface parking lot in Chicago’s South Loop at golden hour.",
        meta_note="Rendered from the cover page with the title/subtitle text and the vector MPC logo removed; no photo credit is printed."),
    "mpc-p03-illustration": dict(
        credit="illustration: Lucie Van der Elst",
        alt="Illustration of a worker in a hard hat and mask holding a clipboard beside a person studying charts on a tablet, with a smokestack and factory in the background."),
    "mpc-p03-top5-areas": dict(
        alt="Row of house icons, 60% of them shaded, broken out by community area: Near North Side (19%), Near West Side (14%), Loop (13%), West Town (7%) and Near South Side (7%).",
        meta_note="No printed title, caption or source. The stat text (“60% of the approximately 120,000 new housing units in the city built since 2006 were concentrated in just 5 community areas.”) and the area labels are part of the graphic."),
    "mpc-p05-workshop-photos": dict(
        caption="At a workshop, participants review and share feedback on research and policy recommendations developed during the Zoning and Land Use Assessment.",
        alt=["Workshop participants seated at round tables reviewing printed research materials, with map posters on easels by the windows.",
             "Participants in conversation around a table at a workshop session."],
        meta_note="Two photos; the single printed caption sits beside the second (smaller) photo and describes both."),
    "mpc-p08-who-stats": dict(
        alt="Infographic: 700+ individuals from 450+ organizations engaged with MPC; participants came from 80+ government agencies and departments, 200+ civic and community organizations, 24 ward offices and 90+ private sector partners; 14 Steering Committee meetings + 7 Community Advisory Group meetings = 21 advisory group meetings; 50+ one-on-one conversations, 10+ focus group sessions and 5 public events and workshops.",
        meta_note="No printed title, caption or source. All figures are PDF text inside the graphic; background photos behind the bottom row of tiles."),
    "mpc-p09-zine": dict(
        alt="Promotional graphic reading “Read Our New Zine! Understand zoning. Shape our city!” listing zoning basics, zoning history and case studies, 3 languages, and informed by community partners, above the covers of the English, Spanish and Chinese editions of In the Zone.",
        meta_note="No caption; the adjacent sidebar text (“A zine to demystify zoning”) is body text. QR code below the sidebar is not exported (it encodes the zine link, which is in the page LINKS)."),
    "mpc-p10-funnel": dict(
        alt="",
        meta_note="No funnel graphic exists on PDF p10: the 120+ → 13 → seven priority outcomes progression is body text only. The page’s graphics are the three values boxes (Equity, Sustainability, Public health) and seven icon-labelled priority outcomes, all text."),
    "mpc-p11-photos": dict(
        alt=["A participant kneels to write on feedback posters propped on chairs along a sunny window wall.",
             "Close-up of a dot-voting board rating draft recommendations.",
             "A hand placing sticky notes on a board titled “What data, research, or context is missing?” and “What are some case studies to explore?”"],
        meta_note="Three photos, no printed captions."),
    "mpc-p13-afford-maps": dict(
        source="Created by Urban Institute. Source: Census ACS 2018–2022",
        panel_titles=[
            "Housing affordability for the typical Chicago renter in 2022",
            "Housing affordability for the typical Chicago homeowner in 2022",
            "Housing affordability for renters in their own neighborhoods in 2022",
            "Housing affordability for homeowners in their own neighborhoods in 2022"],
        panel_meta=[
            dict(title="Housing affordability for the typical Chicago renter in 2022",
                 caption="The percent of income the median Chicago household would spend on the median rent by census tract.",
                 legend_title="Typical Chicago household would spend this percentage of their income on the typical rental in each census tract"),
            dict(title="Housing affordability for the typical Chicago homeowner in 2022",
                 caption="The ratio of affordable monthly mortgage payment for the median Chicago household to median home value purchase price, by census tract. Assumes 27% of monthly income to principal and interest, 20% downpayment, and 7.05% interest rates in 2022.",
                 legend_title="Indicates whether the typical Chicagoan buying a house in this tract would be cost burdened"),
            dict(title="Housing affordability for renters in their own neighborhoods in 2022",
                 caption="The percent of income the median Chicago household in each census tract would spend on the median rent in the same census tract.",
                 legend_title="Typical household in each census tract would spend this percentage of their income on the typical rental in their own neighborhood"),
            dict(title="Housing affordability for homeowners in their own neighborhoods in 2022",
                 caption="The ratio of affordable monthly mortgage payment for the median Chicago household in each census tract to median home value purchase price in the same tract. Assumes 27% of monthly income to principal and interest, 20% downpayment, and 7.05% interest rates in 2022.",
                 legend_title="Indicates whether the typical household in the census tract buying a house in their own neighborhood would be cost burdened")],
        alt=["Map of Chicago census tracts showing the share of income the typical Chicago household would spend on each tract’s typical rent (>40% to <15%); most tracts fall in the 15–29% range, with the highest burdens near downtown and the North Side lakefront.",
             "Map of Chicago census tracts showing whether the typical Chicagoan buying a house there would be cost burdened; the North Side and near downtown are very cost burdened while most of the South and West Sides are affordable or very affordable.",
             "Map showing the share of income households in each tract would spend on rent in their own neighborhood; high burdens (>30%) are widespread on the South and West Sides.",
             "Map showing whether typical households would be cost burdened buying a house in their own neighborhood; cost-burdened tracts are scattered citywide, with many on the South and West Sides."],
        meta_note="Source line prints once under the 2×2 set (bottom left) and applies to all four maps. legend_title values are transcribed from the map images (not in the PDF text layer)."),
    "mpc-p14-afford-bars": dict(
        caption="The percent of census tracts where the median household by race and ethnicity in Chicago can afford the median rent (left) or buy the median home (right) in that tract.",
        note="Note: 2000 median incomes: All households: $38,625; White families: $62,680; Hispanic families: $37,166; Black families: $32,776; Asian families: $47,838\n2018–2022 median incomes: All households: $71,673; White families: $154,749; Hispanic families: $68,370; Black families: $53,587; Asian families: $89,416",
        source="Created by Urban Institute ; Source: Census 1990–2010; Census ACS 2018–2022, both via National Equity Atlas.",
        alt="Two horizontal bar charts comparing 2000 and 2022 shares of tracts where the median household, white, Hispanic, Black and Asian family could afford the median rental unit (left) and ownership unit (right); the Black family’s share falls most, to about 61% for rentals and under 40% for ownership.",
        meta_note="No title printed outside the image; the panel titles “Affordability of median rental unit, by tract” and “Affordability of median ownership unit, by tract” are inside the image. Space before ‘;’ in source is as printed."),
    "mpc-p15-structure-map": dict(
        title="Multifamily housing is the predominant type of existing housing in many community areas",
        source="Source: Census ACS, 2020-2024 estimates",
        alt="Map of Chicago community areas colored by most common structure type: 1-unit homes dominate the outer Northwest, Southwest and South Sides, 2–4-unit buildings much of the inner North, West and South Sides, and 50+ unit buildings the lakefront and downtown."),
    "mpc-p15-capacity-map": dict(
        title="Chicago zoning limits room for new housing: many community areas are completely built out under current regulations",
        caption="The percentage of zoning capacity, or room for housing, that is used by housing already built.",
        note="Note: Does not include parcels zoned for PD or PMD. Does not account for zoning bonuses.",
        source="Created by Urban Institute. Source: Chicago zoning 2023",
        alt="Map of Chicago census tracts showing the share of zoning capacity for housing used in 2023; much of the Northwest Side and city periphery exceeds 100%, while parts of the mid-South and near West Sides use under 50%."),
    "mpc-p16-permits-map": dict(
        title="Permits for new housing, by project unit count, 2006-2024",
        caption="New units permitted between 2006 and 2024. Most new multifamily units were constructed in Planned Development areas.",
        source="Created by Urban Institute. Source: Building permit data, City of Chicago",
        alt="Dot map of new housing permits 2006–2024 sized by project unit count and colored by whether they were developed in a Planned Development zone; PD projects cluster downtown and along the lakefront. An inset stacked bar chart shows about 70,000 units permitted in PD zones versus under 25,000 in any other zoning category.",
        meta_note="Map and bar chart are one raster in the PDF; this file is the whole graphic (map, both legends, bars). mpc-p16-permits-bars is a crop of its bar-chart half; title/caption/source are shared."),
    "mpc-p16-permits-bars": dict(
        title="Permits for new housing, by project unit count, 2006-2024",
        caption="New units permitted between 2006 and 2024. Most new multifamily units were constructed in Planned Development areas.",
        source="Created by Urban Institute. Source: Building permit data, City of Chicago",
        alt="Stacked bar chart of units permitted 2006–2024 by zoning category (B, C, D, PD, R) and project size; PD reaches about 70,000 units, almost all in 50+ unit projects, followed by R at about 24,000 and B at about 13,000.",
        meta_note="Cropped from the right half of the same raster as mpc-p16-permits-map (shared title/caption/source)."),
    "mpc-p19-pd-chart": dict(
        title="PD by land area (square feet)",
        alt="",
        meta_note="Not a chart in the PDF: p19 prints a table headed “PD by land area (square feet)” with 2003 and 2023 columns (Number of PDs, Total area (square feet)); the text agent emits it as an HTML table."),
    "mpc-p20-business-bars": dict(
        title="Businesses are most concentrated in majority-white areas",
        source="Source: City of Chicago business license data, 2023; Census ACS 2018-2022",
        alt="Bar chart of average businesses per 1,000 residents: Majority White tracts 15, Majority Black 9, Majority Latinx 11, Majority Asian 12."),
    "mpc-p20-vacancy-bars": dict(
        title="Majority-Black tracts see the highest business and residential property vacancy rates",
        source="Source: Census ACS 2018-2022; Vacancy rates from U.S. Postal Service, aggregated by HUD, 2022. Identifies addresses that have not collected mail for 90 days or longer; includes both residential and business locations.",
        alt="Bar chart of vacancy rates: Majority White tracts 3%, Majority Black 10%, Majority Latinx 5%, Majority Asian 2%."),
    "mpc-p21-ped-streets-map": dict(
        title="Zoning-designated “pedestrian streets” are concentrated on the North side",
        source="Source: City of Chicago zoning map, 2023",
        alt="Map of Chicago community areas with designated pedestrian corridors marked in red; nearly all are on the North Side, with a few on the near South and West Sides.",
        meta_note="Native raster used: on the page, the business-zoning table overlaps the map’s top-right corner."),
    "mpc-p21-business-zoning-grid": dict(
        title="Business zoning types vary across demographic groups, showing auto-oriented zoning is more common for Black and Latinx Chicagoans",
        note="This looks at top 30% most populous tracts for each demographic (roughly 75 to 85 percent of the citywide population for each demographic). For example, in the top 30% of tracts with the most Latinx Chicagoans, 21% of all commercial is zoned for B3 Business.",
        source="Source: Census ACS 2018-2022; City of Chicago zoning map, 2023.",
        alt="Table of the share of commercial land in each zoning type for Latinx, Black, White and Asian Chicagoans: B1-B2 9/8/8/6%; B3 21/21/15/12%; C1-C3 13/13/8/8%; Downtown 10/2/18/18%; Planned Development 47/56/52/56%; share of all land zoned commercial or within PD 18/17/26/33%.",
        meta_note="Content exists only as a raster (Datawrapper export); file added as fallback. note is transcribed from the image (also contains “Created with Datawrapper”)."),
    "mpc-p23-pm25-race": dict(
        title="Racial composition in highest and lowest PM 2.5 tracts",
        source="Source: University of Illinois HeRoP Lab; Data collected between 2014 and 2018",
        alt="Paired bars comparing each group’s share of the population in the highest and lowest PM 2.5 tracts: Latinx 50% vs 15%, White 29% vs 34%, Black 10% vs 43%, Asian 9% vs 5%; a grey line marks each group’s citywide share.",
        meta_note="A hidden duplicate title “Racial Composition in Highest and Lowest PM 2.5 Tracts” exists in the text layer (not visible); the visible title is used. Legend labels: “City of Chicago Racial Composition”, “Highest PM 2.5 Tracts (Top 20% of Tracts)”, “Lowest PM 2.5 Tracts (Bottom 20% of Tracts)”. The grey citywide reference lines carry no printed values."),
    "mpc-p23-pm25-map": dict(
        title="Small particulate air pollution exposure citywide",
        alt="Map of satellite-derived PM 2.5 by tract from lowest to highest; the highest exposure is along the industrial Southwest Side, near downtown and in the far Southeast Side.",
        meta_note="No source printed directly under the map; the only source in this spread (“Source: University of Illinois HeRoP Lab; Data collected between 2014 and 2018”) is under the race chart in the left column."),
    "mpc-p24-pollution-map": dict(
        group_title="Pollution is concentrated where tree coverage is sparse",
        source="Source: EPA EJ Screen; Year: 2019-2023",
        note="*varies by pollution source; the index reflects the variety of ways people encounter pollution, from breathing it in to living near a waste site.",
        alt="Map of the overall pollution index percentile by tract; the highest percentiles (81–100) are concentrated on the near Southwest Side, around downtown and along interstates.",
        meta_note="No individual title; group_title spans both maps on p24. Source/note print at the bottom of the left column (pollution map + pollution race chart)."),
    "mpc-p24-tree-map": dict(
        group_title="Pollution is concentrated where tree coverage is sparse",
        source="Source: Chicago Region Trees Initiative; Year: 2017",
        alt="Map of tree coverage by tract (1–10% to 26–100%); the densest canopy is on the far North, Northwest and South Sides, with sparse cover near downtown and the Southwest Side.",
        meta_note="No individual title; group_title spans both maps on p24. Source prints at the bottom of the right column (tree map + tree race chart)."),
    "mpc-p24-pollution-race": dict(
        title="Racial composition in highest and lowest pollution tracts",
        source="Source: EPA EJ Screen; Year: 2019-2023",
        note="*varies by pollution source; the index reflects the variety of ways people encounter pollution, from breathing it in to living near a waste site.",
        alt="Paired bars of each group’s share of the population in the highest vs lowest pollution tracts: Latinx 37% vs 21%, White 34% vs 42%, Black 14% vs 26%, Asian 13% vs 7%; a grey line marks each group’s citywide share.",
        meta_note="Legend labels: “City of Chicago Racial Composition”, “Highest Pollution Tracts (Top 20% of Tracts)”, “Lowest Pollution Tracts (Bottom 20% of Tracts)”. Grey reference lines carry no printed values."),
    "mpc-p24-tree-race": dict(
        title="Racial composition in highest and lowest tree cover tracts",
        source="Source: Chicago Region Trees Initiative; Year: 2017",
        alt="Paired bars of each group’s share of the population in the highest vs lowest tree cover tracts: Latinx 16% vs 24%, White 37% vs 41%, Black 36% vs 15%, Asian 7% vs 16%; a grey line marks each group’s citywide share.",
        meta_note="Legend labels: “City of Chicago Racial Composition”, “Highest Tree Cover Tracts (25%+ coverage)”, “Lowest Tree Cover Tracts (Less than 10% coverage)”. Grey reference lines carry no printed values."),
    "mpc-p25-mfg-map": dict(
        title="Concentration of manufacturing zoning districts citywide",
        source="Source: City of Chicago zoning districts, 2023",
        alt="Map of census tracts by share of land zoned for manufacturing (none to 51–100%); manufacturing zoning concentrates along the river and rail corridors on the Southwest Side and in the far Southeast Side."),
    "mpc-p25-mfg-pollution-bar": dict(
        title="Average pollution index near vs. not near manufacturing",
        source="Source: EPA EJ Screen; Year: 2019-2023",
        note="*varies by pollution source",
        alt="Horizontal bar chart: tracts with land zoned for manufacturing average about the 60th pollution index percentile, versus about the 40th for tracts without.",
        meta_note="Source/note print once below the line chart and cover both p25 charts. Values are read from the bars; no data labels are printed."),
    "mpc-p25-mfg-pollution-line": dict(
        title="Average pollution index by share of tract zoned for manufacturing",
        source="Source: EPA EJ Screen; Year: 2019-2023",
        note="*varies by pollution source",
        alt="Line chart rising from about the 41st pollution index percentile for tracts with no manufacturing to about the 80th for tracts that are 50% or more manufacturing.",
        meta_note="Values are read from the line; no data labels are printed."),
    "mpc-p26-mfg-share": dict(
        title="Share of land zoned for manufacturing in most populous areas for each demographic",
        caption="This looks at the top 30% most populous tracts for each demographic (roughly 75 to 85 percent of the citywide population for each demographic). For example, in the top 30% of tracts with the most Latinx Chicagoans, 29% of the land is zoned for manufacturing.",
        alt="Bar chart of land zoned for manufacturing: City of Chicago 17%, Latinx Chicagoans 29%, Black Chicagoans 23%, Asian Chicagoans 9%, White Chicagoans 6%."),
    "mpc-p26-climate-maps": dict(
        source="Source: City of Chicago 2023 Cool Chi/Heat Watch, Chicago Metropolitan Agency for Planning (CMAP), City of Chicago data portal",
        panel_titles=["All-day heat index", "Flooding index", "Combined heat and flooding index"],
        panel_meta=[
            dict(title="All-day heat index", caption="", legend_title=""),
            dict(title="Flooding index", caption="", legend_title=""),
            dict(title="Combined heat and flooding index", caption="", legend_title="")],
        alt=["Map of the all-day heat index in five classes from 1 (lowest heat index) to 5 (highest heat index); the highest values cover much of the South and Southwest Sides.",
             "Map of the flooding index from 1 (lowest flooding susceptibility) to 5 (highest flooding susceptibility); high susceptibility spans the West, Southwest and South Sides.",
             "Map of the combined heat and flooding index from 1 (lowest heat + flood impact) to 5 (highest heat + flood impact); the highest combined impact is on the Southwest and South Sides."],
        meta_note="Legends have class labels but no legend titles."),
    "mpc-p27-heatflood-table": dict(
        title="Racial and ethnic composition by combined heat + flood index",
        source="Source: Census ACS 2018-2022",
        alt="Table of population shares by heat + flood susceptibility quintile. Above the 80th percentile (greatest susceptibility): Black 50%, Latinx 33%, White 14%, Asian 1%, Other 2%. 60th–80th: 27/43/22/6/2%. 40th–60th: 20/33/38/6/3%. 20th–40th: 20/20/45/11/4%. Below the 20th (lowest susceptibility): 22/15/47/11/5%. City of Chicago: 28/29/33/7/3%.",
        meta_note="Content exists only as a raster; file added as fallback. Values in alt are transcribed from the image."),
    "mpc-p27-tree-illustration": dict(
        alt="",
        meta_note="Decorative line drawing of three trees in the “Chicago’s fractured tree governance” sidebar; empty alt intended. Rendered with overlapping sidebar text removed."),
    "mpc-p35-usi-map": dict(
        title="Cumulative Urban Services Index Score",
        alt="Map of block groups by cumulative Urban Services Index score quartile; the 4th (highest) quartile concentrates along the North Side lakefront, downtown and the inner West Side."),
    "mpc-p36-density-map": dict(
        title="Cumulative Density Score",
        alt="Map of block groups by cumulative density score quartile; the densest areas are downtown and along the North Side."),
    "mpc-p36-typology-map": dict(
        title="Infrastructure-Density Typologies",
        alt="Map of four infrastructure-density typologies: high infrastructure, high density on the North Side lakefront; low infrastructure, low density around O’Hare, the Far South and Southeast; moderate infrastructure, low density across the West, Southwest and South Sides; and scattered low infrastructure, moderate density on the Northwest Side."),
    "mpc-p37-insurance-map": dict(
        alt="Map of the share of residents with private insurance by tract (0–0.16 to 0.8–0.96); the highest shares are on the North Side and near downtown.",
        meta_note="No printed title, caption or source; legend title in image: “Share of Residents with Private Insurance (*100)”."),
    "mpc-p37-food-maps": dict(
        title="Northside communities have access to more healthy food stores, and less healthy food stores are evenly distributed",
        source="Data: USDA SNAP Food Vendors 2025",
        alt="Two maps of SNAP food vendors by community area: less healthy stores (convenience, drug and dollar stores) are spread fairly evenly across the city, while more healthy stores (grocery stores, supermarkets, super stores, farmer’s markets, restaurant food centers) are concentrated on the North Side."),
    "mpc-p38-food-bars": dict(
        title="USDA SNAP vendor counts by zone",
        source="Source: 2025 USDA SNAP Vendors (grocery stores, supermarkets, and super stores) and 2023 Chicago zoning data",
        note="Note: This excludes specialty stores, pharmacies, corner stores, convenience stores, and farmers markets",
        alt="Horizontal stacked bar chart of food store counts by zoning district, split into grocery stores, super stores and supermarkets; B3 has the most (about 240), followed by B1 (about 120), PD (about 95) and C1 (about 60).",
        meta_note="The title exists in the PDF text layer but is hidden behind the chart image on the printed page; included because it is the only title for this chart."),
    "mpc-p39-zoning-share": dict(
        title="Share of zoned land, 2023",
        note="Numbers may not add exactly to 100% due to rounding.",
        alt="",
        meta_note="Not a separate chart: these are the column header and note of the Appendix: Zoning districts table (pp 37–38 printed / 39–40 PDF). Values: R 52% (RS 41%, RT 8%, RM 3%), PD 13%, M 11%, POS 8%, PMD 6%, B 6%, C 3%, D 1%, T <1%."),
    "mpc-p41-zoning-map": dict(
        title="Chicago Zoning Map (2023)",
        alt="Citywide zoning map colored by district type: RS residential covers most of the city, with RT and RM residential, commercial and business corridors along arterials, manufacturing and planned manufacturing districts along rail and river corridors, downtown districts in the center, and parks along the lakefront."),
    "urban-hero": dict(
        credit="halbergman",
        alt="Aerial view of a dense Chicago residential block of narrow two- and three-flat buildings and houses, with tree-lined streets and alleys."),
    "urban-fig1": dict(
        title="Without Reforms to the City’s Zoning Code, Permitting Requests from Now Until 2041 Will Likely Be Concentrated In and Around Chicago’s Near Northwest Neighborhoods",
        subtitle="Estimated probability of a permit for new housing development being requested on a given parcel by 2041, based on the Urban Institute’s Housing Market Forecaster",
        source="Sources: Authors’ analysis of Cook County Assessor parcel data, City of Chicago zoning data, and 2020–24 census tract–level American Community Survey data.",
        note="Notes: These estimates assume the city makes no changes to its zoning code and permits continue at the same pace as they did from 2011 to 2025 under the same economic conditions. Estimates are for cumulative development from 2026 to 2041.",
        alt="Parcel-level map of Chicago showing the probability that a parcel is developed by 2041 (0% to 30%+); the highest probabilities are north and northwest of downtown, with the lowest on the far South, Southwest and West Sides.",
        meta_note="Title/subtitle print on PDF p4, the map and Sources/Notes on p5. The PDF prints no “Figure 1” label."),
    "urban-fig2": dict(
        title="Under Chicago’s Current Zoning, Most Housing Units Permitted Between Now and 2041 Will Likely Be Concentrated In and Around the City’s Downtown",
        subtitle="Estimated housing unit permits per ward by 2041, based on the Urban Institute’s Housing Market Forecaster",
        source="Sources: Authors’ analysis of Cook County Assessor parcel data, City of Chicago zoning data, and 2020–24 census tract–level American Community Survey data.",
        note="Notes: These estimates assume the city makes no changes to its zoning code and permits continue at the same pace as they did from 2011 to 2025 under the same economic conditions. Estimates are for cumulative development from 2026 to 2041.",
        alt="Map of estimated housing units added per ward by 2041 (0 to 10,000); the downtown and near-lakefront wards are darkest, with most outlying wards adding far fewer.",
        meta_note="Title/subtitle print on PDF p6, the map and Sources/Notes on p7. The PDF prints no “Figure 2” label."),
    "urban-table1": dict(
        title="These Reforms Could Increase Housing Supply, but Wouldn’t Fully Meet the City’s Housing Needs",
        subtitle="Estimated effects of zoning reforms by 2041 compared with baseline",
        source="Source: Authors’ analysis of Cook County Assessor parcel data, City of Chicago zoning data, and 2020–24 census tract–level American Community Survey data.",
        note="Notes: Estimated effect is only for parcels where residential uses are allowed by right. The model does not include potential planned developments. For reform 1, we assume triplexes are allowed only on lots with at least 2,500 square feet; we also increase the allowed floor area ratio to 1.05. For reform 2, we allow more units on larger parcels (scaling up as the parcel size grows) and increase the allowed floor area ratio to 1.25. For reform 3, we assume that parcel areas that could be affected by this change could be as small as 1,650 square feet, and that the allowed floor area ratio is increased to 2.5. Reform 2 fully encompasses reform 1, in that it would also allow duplexes or triplexes if the lot is too small to allow bigger projects.",
        alt="",
        meta_note="Rendered as an HTML table (no image). The PDF prints no “Table 1” label. In the “Permits on affected parcels (in units)” column, +8,100 and +9,500 print in light grey (#ababab)."),
    "urban-fig3": dict(
        title="Combining Reforms That Allow Small-Scale Apartments Plus Transit-Oriented Upzoning Would Unlock More Housing Supply Across the City",
        subtitle="Estimated additional units permitted by 2041, compared with baseline, by reform",
        source="Sources: Authors’ analysis of Cook County Assessor parcel data, City of Chicago zoning data, and 2020–24 census tract–level American Community Survey data.",
        note="Notes: These estimates assume economic conditions between 2011 and 2025 persist. Estimates are for cumulative development from 2026 to 2041.",
        panel_titles=[
            "Reform 1: Allowing duplexes and triplexes",
            "Reform 2: Legalizing small apartment buildings (four to nine units)",
            "Reform 3: Enabling higher-density multifamily buildings within ¼ mile of transit",
            "Reform 4: Combining reforms 2 and 3"],
        panel_meta=[
            dict(title="Reform 1: Allowing duplexes and triplexes", caption="", legend_title="Units permitted above baseline"),
            dict(title="Reform 2: Legalizing small apartment buildings (four to nine units)", caption="", legend_title="Units permitted above baseline"),
            dict(title="Reform 3: Enabling higher-density multifamily buildings within ¼ mile of transit", caption="", legend_title="Units permitted above baseline"),
            dict(title="Reform 4: Combining reforms 2 and 3", caption="", legend_title="Units permitted above baseline")],
        alt=["Ward map of additional units permitted above baseline under reform 1 (0 to 1,300); the largest gains are in the far Northwest and Southwest Sides.",
             "Ward map of additional units permitted above baseline under reform 2; similar pattern to reform 1 but with larger gains in the far Northwest and Southwest Sides.",
             "Ward map of additional units permitted above baseline under reform 3; gains concentrate in Northwest Side wards around Jefferson Park, Portage Park and Lincoln Square, with little change elsewhere.",
             "Ward map of additional units permitted above baseline under reform 4 (reforms 2 and 3 combined); the largest gains, up to about 1,300 units, are in Northwest Side wards, with notable gains in the far Southwest."],
        meta_note="Panel label for each map prints immediately above it: Reform 1 label on p10 above the p10 map; Reform 2/3/4 labels at the bottom of p10/p11/p12 introduce the maps on p11/p12/p13. Mapping confirmed by data (reform 2 > reform 1 everywhere; reform 3 concentrated in the Northwest per the text; reform 4 darkest). legend_title is inside each image. Sources/Notes print once, on p13."),
    "urban-adu-scenarios": dict(
        alt="",
        meta_note="No chart in the PDF; figures come from body text on pp 14–15: 343 ADUs permitted 2021–2025 in the pilot areas; removing owner-occupancy rules in some pilot areas could have added about 100 (about 30 percent); a citywide pilot without owner-occupancy rules could have permitted about 860 more, for a total of 1,203 (3.5 times actual)."),
    "urban-adu-types": dict(
        alt="",
        meta_note="No chart in the PDF; figures come from body text on p14: 28 percent above-garage coach or carriage houses, 66 percent internal conversions, remaining 6 percent external additions, legalizations or unclear."),
}

def norm(s):
    return s.replace("ﬁ", "fi").replace("ﬂ", "fl") if isinstance(s, str) else s

def main():
    entries = json.loads(MANIFEST.read_text())
    ids = {e["id"] for e in entries}
    assert set(META) <= ids, set(META) - ids
    missing = ids - set(META)
    assert not missing, f"no metadata for {missing}"
    for e in entries:
        m = META[e["id"]]
        for k, v in m.items():
            if isinstance(v, list):
                v = [{kk: norm(vv) for kk, vv in x.items()} if isinstance(x, dict) else norm(x) for x in v]
            e[k] = norm(v)
        # files: <id>.webp, or <id>--<panel>.webp in manifest panel order, or <id>--N.webp
        if (IMG / f"{e['id']}.webp").exists():
            files = [IMG / f"{e['id']}.webp"]
        elif e.get("panels"):
            files = [IMG / f"{e['id']}--{p}.webp" for p in e["panels"]]
        else:
            files = sorted(IMG.glob(f"{e['id']}--*.webp"))
        files = [f for f in files if f.exists()]
        if e.get("panels"):
            assert len(files) == len(e["panels"]), e["id"]
        e["files"] = [f"assets/img/{f.name}" for f in files]
        sizes = [Image.open(f).size for f in files]
        if len(sizes) == 1:
            e["width"], e["height"] = sizes[0]
        elif sizes:
            e["width"] = [w for w, _ in sizes]
            e["height"] = [h for _, h in sizes]
        else:
            e.pop("width", None); e.pop("height", None)
    MANIFEST.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + "\n")
    for e in entries:
        print(e["id"], e["kind"], len(e["files"]), e.get("width"), e.get("height"))

if __name__ == "__main__":
    main()
