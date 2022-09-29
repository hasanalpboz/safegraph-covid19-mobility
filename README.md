# COVID - Mobility Analysis

This repository contains the code to generate results in our paper titled "One City, Two Tales: Using Mobility Networks to Understand NYC Neighborhood Resilience and Fragility during the COVID-19 Pandemic".

## Data

- Census Block Group (CBG) level weekly mobility data from [Safegraph](https://docs.safegraph.com/docs/weekly-patterns)
- CBG level demographic data from the [US Census Bureau](https://www.census.gov)
- Daily confirmed COVID cases by ZCTA from [CSSE at Johns Hopkins University](https://github.com/CSSEGISandData/COVID-19_Unified-Dataset/blob/master/COVID-19.rds)

## Project Folders

- scripts/notebooks/node-dissimilarity.ipynb: Dissimilarity calculation between paired 2019-2020 networks. Generates Fig 1.
- scripts/notebooks/huff-model-pso.ipynb: Huff Model implementation.
- scripts/notebooks/mobility-change.ipynb: Analyzes mobility by boroughs over time and centrality metrics by demographic groups. Generates Fig 2 and 5.
- scripts/notebooks/bridge-cbgs.ipynb: Implements the proposed bridge cbg discovery method and analyzes them by demographic groups. 
- scripts/plot-bridge-cbgs.ipynb: Generates Fig 3 and 4.
- scripts/notebooks/google-mobility-report.ipynb: Generates Fig 6.