# World Zero 2026 Extension Matrix

Date: 2026-09-17
Status: proposed model scope; mechanisms require implementation and qualification

This matrix turns omitted/compressed 1972 mechanisms into explicit World Zero modules. Inclusion does not mean every listed variable must appear in V0. The model should add mechanisms in staged, testable increments.

| System | World3 treatment | World Zero modernization | Candidate state/flow variables | Important feedbacks | Main failure risk |
|---|---|---|---|---|---|
| Demography | Four broad age groups, fertility/mortality feedbacks | Regional fertility transition, education, migration, healthy life years, dependency | age cohorts, TFR/desired fertility, education stock, migration flows, healthy-life expectancy | education/child survival -> fertility; ageing -> labour/fiscal load; climate/health -> mortality/morbidity | fitting population while misrepresenting fertility mechanism |
| Production/capital | Industrial and service capital | Sectoral productive capacity + infrastructure quality | productive capital, service/public capital, infrastructure depreciation, output | investment -> capacity; climate/resource costs -> depreciation/output; demand -> investment | GDP/output proxy absorbs unrelated mechanisms |
| Distribution | Minimal | Income/wealth distribution and access | labour share, owner/worker income, consumption bands, public-service access | inequality -> consumption/fertility/health/trust; damages -> unequal exposure -> policy response | ideological hard-coding or unobservable latent scalar |
| Finance | Minimal | Debt, financing cost and fiscal capacity as bounded amplifiers | public/private debt, debt service, interest/financing spread, fiscal space | stress -> financing cost -> investment delay; transition investment -> debt/capacity | nominal finance incorrectly overrides physical constraints |
| Energy | Folded into resources/capital | Energy-service system with electricity, fuels, grids and storage | generation capacity by class, storage, grid capacity, fuel flows, useful energy services | deployment -> learning -> cost -> deployment; electrification -> power demand; climate -> cooling/grid stress | using LCOE alone as system cost |
| Fossil resources | Generic nonrenewable stock | Separate oil/gas/coal stocks and extraction cost/intensity | recoverable stocks, production, reserve additions, extraction energy/cost | depletion -> cost -> substitution/demand; price -> exploration/investment | reserve/resource definitions treated as fixed geology only |
| Critical/industrial minerals | Generic nonrenewable stock | Material-specific mining, refining, recycling and concentration | copper/lithium/nickel/cobalt/graphite/rare-earth/other stocks, recycling, processing | clean-tech buildout -> mineral demand; scarcity -> price/substitution/recycling; geopolitics -> availability | combinatorial explosion; false precision |
| Materials/circularity | Limited | Material footprint, lifetime stocks, secondary supply | in-use stocks, waste flows, recycling yields, material intensity | durable stock -> future scrap; design efficiency -> material intensity | counting recycled material as new resource without losses |
| Agriculture | Land, yield, fertilizer, food | Food-land-water-soil-nutrient system + access | cropland/pasture, soil condition, irrigation, nutrients, yield, food stocks/losses | inputs -> yield; degradation -> yield decline; prices/income -> diet/access; climate -> yield | global calories hide malnutrition/access |
| Freshwater | Indirect | Blue/green water availability, withdrawals and stress | renewable water, soil moisture proxy, withdrawals, storage, groundwater stress | climate/land -> water; irrigation -> food; pumping -> energy; scarcity -> allocation | one global water stock is meaningless |
| Climate/carbon | Persistent pollution proxy | Carbon cycle + temperature/damage interface | CO2/CH4 or CO2e burden, temperature anomaly, carbon sinks, climate hazard index | emissions -> warming -> damages/adaptation -> output/emissions | duplicating full climate models unnecessarily |
| Biosphere | Largely absent | Biosphere integrity/ecosystem function | habitat/land integrity proxies, ecosystem-function index, restoration flows | land use/pollution/climate -> biodiversity; ecosystem condition -> crop/water resilience | treating one biodiversity index as directly observed truth |
| Biogeochemical flows | Pollution aggregate | Nitrogen/phosphorus loading and fertilizer dependency | reactive N/P application, surplus/loading, nutrient efficiency | fertilizer -> food; surplus -> water/ecosystem damage; energy -> fertilizer cost | unit/scale mismatch |
| Novel entities/pollution | Persistent pollution stock | Multiple pollutant classes where data support dynamics | air-pollution burden, persistent chemicals/plastics proxy, waste | output/consumption -> waste; regulation/technology -> abatement; pollution -> health/ecosystems | arbitrary aggregation into a moralized 'pollution score' |
| Ocean | Minimal | Ocean acidification/climate interaction at global level | ocean pH/aragonite proxy, marine productivity/fisheries proxy | CO2 -> acidification; warming/acidification -> marine food/ecosystems | overbuilding ocean model outside project scope |
| Technology | Scenario/parameter heavy | Endogenous learning/diffusion for selected technologies | cumulative capacity, cost, efficiency, R&D/adoption stocks | deployment -> learning -> cost -> deployment; supply chain -> delay | assuming learning continues indefinitely |
| Digital/AI | Absent | Optional productivity/energy-demand accelerator with uncertainty | data-centre power, digital capital/productivity multiplier | compute investment -> productivity/energy demand; grid constraint -> deployment | speculative AI singularity dominates model |
| Institutions | Scenario switches | State capacity, policy delay, trust/tension and coordination proxies | response capacity, policy lag, social tension/trust proxies | crisis perception -> policy; inequality/damage -> tension; tension -> implementation drag | encoding political preference as causal law |
| Trade | Mostly implicit | Regional trade and dependence | food/energy/material trade, import dependence, shipping/logistics capacity | regional shortage -> trade/price; conflict -> fragmentation; trade -> resilience/dependence | equilibrium assumptions erase physical logistics |
| Conflict/shocks | Mostly absent | Stochastic/endogenous stress events | conflict intensity/risk, trade disruption, disaster shocks | scarcity/inequality -> risk; conflict -> capital loss/trade/food/energy stress | deterministic 'scarcity causes war' fallacy |
| Adaptation | Limited | Explicit adaptation capital and diminishing residual damage | adaptation stock, maintenance, protection investment | damages -> adaptation investment -> lower damages; inequality/fiscal limits -> uneven adaptation | adaptation as unlimited damage eraser |
| Wellbeing | Output proxies | Multi-dimensional diagnostic, not single optimization target | disposable income, healthy life, services, inequality, environmental quality, food/energy access | system states -> wellbeing -> fertility/trust/policy | composite index hides tradeoffs/value judgments |

## V0 minimum viable modernization

World Zero V0 should resist the temptation to implement every row. A useful first modernized model can be built from:

1. World3-compatible baseline.
2. Macroregional population/production structure.
3. Energy system with fossil vs low-carbon electricity, grid/storage and endogenous learning.
4. Material/resource split: fossil fuels vs a compact critical-mineral basket with recycling.
5. Climate/carbon feedback into agriculture, mortality/productivity and capital depreciation.
6. Food-land-water-soil state.
7. Distribution variable (labour/capital or income bands) feeding access and policy capacity.
8. Observation/provenance and validation harness.

Biodiversity, detailed nitrogen/phosphorus, conflict, finance and broader pollutants should enter after V0 interfaces are stable unless tests show they are required to explain major residuals.

## Regional architecture

Recommended first regional partition: 8-12 macroregions, selected for data availability and structural differences rather than political symbolism. Candidate grouping:

- North America
- Latin America & Caribbean
- Western/Northern Europe
- Eastern Europe & Central Asia
- Middle East & North Africa
- Sub-Saharan Africa
- South Asia
- East Asia
- Southeast Asia
- Oceania

China and the United States may warrant separate regions because of their weight in energy, industry and technology deployment. Region definitions must remain data-manifest-controlled.

Global shared states should be used only where scientifically justified (e.g., atmospheric climate state). Food, energy, income, water, fertility, infrastructure and most resource constraints should retain regional structure.

## Modern empirical anchors

- UN WPP 2024: demographic transition and regional age/fertility trajectories.
- IEA/IRENA: energy mix, electricity demand, technology costs, grids/storage, mineral outlook.
- Global Carbon Budget/IPCC: emissions, carbon burden and climate response constraints.
- FAOSTAT/FAO SOLAW: agriculture, land, water, production and degradation.
- Stockholm Resilience Centre/IPBES: planetary-boundary and biodiversity/nexus constraints.
- UNEP IRP: material extraction/footprint and circularity.
- World Bank/UN/OECD/ILO/WID: output, population, public services, labour share, inequality and development observables.

## Design invariant

Every added mechanism must have:

- a named stock/flow or explicit algebraic relation;
- a physical/social/economic interpretation;
- units and sign conventions;
- a source or calibration basis;
- an uncertainty representation;
- at least one falsification or holdout target;
- declared upstream/downstream dependencies;
- no hidden change of exogenous/endogenous status between scenarios.
