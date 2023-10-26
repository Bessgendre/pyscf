Develop Branch
===

This branch now aims at the implement of AIMD Raman Spectroscopy calculation with CNEO. 

There should be three steps:

1. calculate the static polarizability $\boldsymbol{\alpha}$. infinitesimal electronic field should be applied to the molecule in three different directions.
2. ensemble average: $\left\langle\text{Tr}\left[\boldsymbol{\beta}(0)\boldsymbol{\beta}(t)\right]\right\rangle$.
3. integration: $\displaystyle \int e^{-i\omega t}dt$, and further $\displaystyle \int d\omega$.