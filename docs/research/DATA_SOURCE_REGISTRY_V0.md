# World Zero Data Source Registry V0

Date: 2026-09-17
Status: candidate source registry; exact datasets/vintages must be frozen during implementation

World Zero must be reconstructible from exact data vintages. A URL is not a dataset binding. Each implementation dataset must eventually record provider, product/table, release/version date, download timestamp, geography, units, transformation code and content digest.

| Domain | Candidate authoritative source | Candidate observables | Notes / hazards |
|---|---|---|---|
| Population/fertility/mortality | UN DESA World Population Prospects 2024 | population by age/sex, births, deaths, fertility, life expectancy | projections must not be mixed with observations during historical calibration |
| Health | WHO Global Health Observatory; IHME where licensing permits | mortality causes, healthy life expectancy, disease burden | methodology revisions can create artificial time breaks |
| Education | UNESCO UIS / World Bank EdStats | attainment, enrollment, female education | coverage differs by country/year |
| GDP/capital/development | World Bank WDI; UN National Accounts; Penn World Table | GDP, investment, capital proxies, sector shares | PPP vs market exchange rates must not be mixed silently |
| Inequality | World Inequality Database / World Inequality Report 2026 | income/wealth shares, pretax/posttax distributions | modeled imputations and survey/tax data have different uncertainty |
| Labour income | ILO/OECD | labour income share, employment, wage measures | informal economy measurement varies regionally |
| Public finance/debt | IMF WEO/Fiscal Monitor/Global Debt Database; World Bank | public debt, fiscal balance, interest burden | nominal/real and public/private definitions vary |
| Energy balances | IEA World Energy Balances / Global Energy Review; Energy Institute where appropriate | primary/final energy, fuels, electricity generation/demand | some detailed IEA datasets are licensed; build open-data fallback plan |
| Renewable capacity/cost | IRENA | installed capacity, generation cost, technology learning | LCOE is not a full system-integration cost |
| Electricity/grid | IEA, IRENA, Ember, regional system operators | generation mix, demand, storage, grid investment | global consistency and licensing need review |
| Fossil resources | USGS/EIA/IEA/BGR and resource-specific geological sources | production, reserves/resources, extraction intensity | reserves are economic/technical quantities, not fixed physical stocks |
| Critical minerals | IEA Global Critical Minerals Outlook; USGS Mineral Commodity Summaries | demand, production, refining concentration, recycling, project pipeline | material definitions and scenario assumptions differ |
| Material footprint | UNEP International Resource Panel / Global Material Flows Database | extraction, domestic material consumption, material footprint | footprint estimates depend on MRIO methodology |
| Emissions/carbon | Global Carbon Budget, EDGAR, UNFCCC | fossil/land CO2, emissions by region, sinks | revisions matter; territorial vs consumption accounting differs |
| Climate | IPCC, WMO, NASA GISTEMP, NOAA, Berkeley Earth | global/regional temperature, forcing, extremes | World Zero should not duplicate a full GCM; use reduced-form climate state |
| Land/agriculture | FAOSTAT; FAO SOLAW 2025 | cropland/pasture, yields, fertilizer, irrigation, production, land degradation | degradation metrics are heterogeneous and often modeled |
| Water | FAO AQUASTAT; UNESCO/UN-Water | withdrawals, renewable water, water stress, irrigation | groundwater and green-water coverage is uneven |
| Food access/nutrition | FAO SOFI/FAOSTAT; WFP | undernourishment, food prices, dietary supply | food availability != access != nutrition |
| Soil | FAO/ISRIC/GLAD and scientific syntheses | soil organic carbon, erosion/degradation proxies | slow-changing stock with high spatial heterogeneity |
| Nutrients | FAOSTAT, UNEP, scientific global N/P budgets | fertilizer use, N/P surplus/loading | difficult global observation of environmental loss pathways |
| Biodiversity/ecosystems | IPBES, Living Planet/GBIF/IUCN where methodologically appropriate | habitat integrity, extinction risk, ecosystem-function proxies | avoid treating advocacy indices as directly observed state without measurement model |
| Planetary boundaries | Stockholm Resilience Centre / peer-reviewed boundary updates | control variables for nine boundaries | boundaries are risk guardrails, not deterministic event thresholds |
| Fisheries/ocean | FAO fisheries; NOAA; Global Ocean Acidification observing networks | catch, stock status, pH/carbonate proxies | marine ecosystem dynamics may exceed V0 scope |
| Air pollution | WHO, State of Global Air, EDGAR | PM2.5, ozone, precursor emissions | health damage functions must state population exposure assumptions |
| Plastics/novel entities | UNEP/OECD | plastics production/waste, chemicals/pollution proxies | no single globally complete 'novel entities' time series exists |
| Trade | UN Comtrade, BACI/CEPII, FAOSTAT trade | bilateral materials/food/energy trade | product concordance and re-exports complicate physical flows |
| Institutions | World Governance Indicators, V-Dem, QoG, tax/public-service data | state capacity proxies, rule/institution measures | latent political constructs should not be treated as direct physical stocks |
| Conflict | UCDP/PRIO, ACLED where licensing allows | conflict onset/intensity, fatalities, disruptions | avoid deterministic scarcity-to-conflict equation |
| Disasters | EM-DAT, WMO | disaster losses, mortality, affected population | reporting coverage improves through time |
| Technology/digital | IEA, IRENA, ITU, OECD, industry/open datasets | data-centre energy, broadband/digital adoption, compute proxies | AI productivity effects are highly uncertain and should remain scenario/ensemble parameters initially |

## Mandatory dataset manifest fields

Every ingested dataset should eventually use a machine-readable manifest containing at least:

```yaml
schema_id: WORLD_ZERO_DATASET_MANIFEST_V1
dataset_id: <stable project id>
provider: <organization>
product: <dataset/table name>
release_date: <YYYY-MM-DD or documented release>
retrieved_at: <timestamp>
source_url: <canonical source>
license: <license or access terms>
geography: <coverage and region mapping>
time_coverage: <start/end>
frequency: <annual/monthly/etc>
units: <source units>
transformations:
  - <exact transformation step>
missing_data_policy: <declared policy>
uncertainty: <source uncertainty or project assumption>
content_sha256: <digest of raw immutable payload>
transform_code_commit: <git sha>
```

## Observation-model rule

World Zero distinguishes:

- **latent model state** — a simulated concept such as soil condition or institutional response capacity;
- **direct observation** — a measured quantity with known units;
- **derived observation** — an estimate produced by a model or accounting transformation;
- **composite index** — a constructed indicator combining multiple inputs;
- **scenario input** — an assumed future path, not observed history.

Calibration must never silently treat all five classes as equally direct evidence.

## Correlation / double-counting warning

Many candidate indicators share the same upstream activity. For example GDP, industrial output, electricity use, material footprint and CO2 emissions are correlated partly because they measure overlapping economic throughput. Fitting all of them does not create five independent confirmations of the same mechanism.

The validation harness should record evidence families and report both raw metric count and effective/clustered evidence count.

## Data-access constraint

Prefer open, reproducible sources for the project baseline. Licensed sources may be used for research/validation when permitted, but a public/open World Zero release must be reconstructible without silently depending on inaccessible proprietary data.
