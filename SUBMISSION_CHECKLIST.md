# Submission and rubric checklist

This checklist maps the supplied rubric to report evidence. It is not a grade prediction.

| Rubric item | Evidence in this package |
| --- | --- |
| Premise — 22 points | Section 1: engineering question, IVP, initial conditions, parameters, controlled comparisons and modeling assumptions |
| Method — 22 points | Section 2 and Appendix A: accuracy/stability/cost justification, RK4 stages, nonlinear Taylor matching, local/global error, stability polynomial and algorithm |
| Correct implementation — 22 points | Section 3: observed fourth-order convergence, independent exact-solution checks, 25-pair parameter evaluation; seven automated tests; full custom solver in Appendix C |
| Results — 22 points | Section 4: 357-case sensitivity grid, refinement at every point, exact vacuum comparisons, three engineering figures, numerical table, physical interpretation and limits |
| Contributions — 6 points | Section 5: supplied group roles and approximate shares; each includes technical work |
| Reproducibility — 6 points | Section 6, Appendix B and README: all source, pinned dependencies, data, figures, automated reproduction and execution record |
| GitHub bonus — up to 3 points | Repository created and actual URL inserted in the report; **team must upload the final package** |
| Generative AI disclosure | Section 7 and README describe substantive AI assistance |

## Required team actions before submission

- [ ] Read the report and understand the equations, numerical checks and physical limitations.
- [ ] Confirm that names, contribution descriptions and percentages are accurate; edit them if needed. The assistant cannot verify individual human contributions.
- [ ] Upload the extracted package contents to [the project repository](https://github.com/justinchiang0207/AE370-Sounding-Rocket-Ascent---Initial-Value-Problem).
- [x] Insert the actual repository URL in `main.tex` and recompile the PDF.
- [ ] After uploading, check that the PDF link opens the repository and that the final PDF and source are present there.
- [ ] Submit the compiled PDF through the course's prescribed submission channel.

## Completed numerical checks

- Seven unit tests passed in the recorded execution.
- Nominal observed adjacent-step orders: approximately 4.184, 4.098 and 4.050.
- Refined numerical reference checked by one additional step halving.
- Ballistic constant-acceleration solution and powered variable-mass vacuum solution tested independently of the RK4 method.
- All 25 nominal phase-step pairs evaluated for accuracy and cost.
- All 357 atmospheric grid cases checked at three step sizes.
- All 357 vacuum cases compared with the exact powered-plus-coast apogee.
- No flight-data validation or physical uncertainty quantification is claimed.

The instructor determines the grade and bonus; completing a checklist cannot guarantee 100/100 or the three bonus points.
