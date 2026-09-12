/*
 * T1D-CVD meta-calculator — open, transparent risk-model engine.
 *
 * Pure JavaScript ports of published cardiovascular risk equations, checked
 * against source-paper worked examples or live tools where available. Every
 * coefficient is in this file or the separately licensed qrisk3.js. Runs in the browser and
 * in Node (for the test harness).
 *
 * IMPORTANT: this engine does not invent a new model. It reproduces published
 * calculator equations with endpoint-specific implementation-check status so they can be
 * run side by side with explicit assumptions and sensitivity settings. It is an
 * exploratory research comparison tool, NOT a validated accuracy claim.
 *
 * Units (canonical): cholesterol mmol/L; HbA1c % (DCCT) with mmol/mol helper;
 * SBP/DBP mmHg; eGFR mL/min/1.73m2.
 */
(function (root) {
  "use strict";
  const exp = Math.exp, log = Math.log, log2 = Math.log2, min = Math.min, max = Math.max;
  const MGDL = 38.67;          // mmol/L -> mg/dL (cholesterol)
  const MMOL_NONHDL = 0.02586; // mg/dL -> mmol/L (PREVENT)

  function hba1cPctToMmol(p) { return 10.929 * (p - 2.15); }
  function hba1cMmolToPct(m) { return m / 10.929 + 2.15; }

  // ----------------------------------------------------------------- Steno T1 (Vistisen 2016)
  const STENO = {
    cvd: { alpha: -6.046429053, age: 0.040672727, female: -0.234111177, duration: 0.013062752,
      sbp: 0.005814221, ldl: 0.082287009, hba1c: 0.012209026, micro: 0.437359313, macro: 0.738916137,
      legfr_lt40: -0.404318528, legfr_ge40: -0.345596046, smoking: 0.204224209, noex: 0.229279688 },
    ihd_stroke: { alpha: -5.716956267, age: 0.044302014, female: -0.208960873, duration: 0.007769067,
      sbp: 0.006514040, ldl: 0.117920173, hba1c: 0.008561294, micro: 0.295662570, macro: 0.532588474,
      legfr_lt40: -0.504447543, legfr_ge40: -0.443012444, smoking: 0.308949210, noex: 0.183553384 },
  };
  function steno(p, years, outcome) {
    const c = STENO[outcome || "cvd"];
    const a1c = hba1cPctToMmol(p.hba1c_pct);
    const micro = p.albuminuria === "micro" ? 1 : 0, macro = p.albuminuria === "macro" ? 1 : 0;
    const egfrCoef = p.age < 40 ? c.legfr_lt40 : c.legfr_ge40;
    const lp = c.alpha + c.age * p.age + c.female * (p.female ? 1 : 0) + c.duration * p.duration
      + c.sbp * p.sbp + c.ldl * p.ldl + c.hba1c * a1c + c.micro * micro + c.macro * macro
      + egfrCoef * log2(p.egfr) + c.smoking * (p.smoker ? 1 : 0) + c.noex * (p.regular_exercise ? 0 : 1);
    return (1 - exp(-exp(lp) * (years || 10))) * 100;
  }

  // ----------------------------------------------------------------- SCORE2 region recalibration scales (shared)
  const SCALES = {
    male: { low: [-0.5699, 0.7476], moderate: [-0.1565, 0.8009], high: [0.3207, 0.9360], very_high: [0.5836, 0.8294] },
    female: { low: [-0.7380, 0.7019], moderate: [-0.3143, 0.7701], high: [0.5710, 0.9369], very_high: [0.9412, 0.8329] },
  };
  function cloglogRecal(lp, baseline, sex, region) {
    const s = SCALES[sex][region];
    return -Math.expm1(-exp(s[0] + s[1] * (log(-log(baseline)) + lp)));
  }

  // ----------------------------------------------------------------- SCORE2-Diabetes (ESC 2023)
  const S2D_S0 = { male: 0.9605, female: 0.9776 };
  const S2D = {
    male: { age: 0.5368, smk: 0.4774, sbp: 0.1322, dm: 0.6457, tc: 0.1102, hdl: -0.1087, age_smk: -0.0672,
      age_sbp: -0.0268, age_dm: -0.0983, age_tc: -0.0181, age_hdl: 0.0095, dm_agedx: -0.0998, a1c: 0.0955,
      legfr: -0.0591, legfr2: 0.0058, a1c_age: -0.0134, legfr_age: 0.0115 },
    female: { age: 0.6624, smk: 0.6139, sbp: 0.1421, dm: 0.8096, tc: 0.1127, hdl: -0.1568, age_smk: -0.1122,
      age_sbp: -0.0167, age_dm: -0.1272, age_tc: -0.0200, age_hdl: 0.0186, dm_agedx: -0.1180, a1c: 0.1173,
      legfr: -0.0640, legfr2: 0.0062, a1c_age: -0.0196, legfr_age: 0.0169 },
  };
  function score2diabetes(p) {
    if (p.age < 40 || p.age >= 80) return NaN;
    const sex = p.female ? "female" : "male", b = S2D[sex];
    const cage = (p.age - 60) / 5, csbp = (p.sbp - 120) / 20, ctc = p.total_chol - 6, chdl = (p.hdl - 1.3) / 0.5;
    const cdx = (p.onset_age - 50) / 5, ca1c = (hba1cPctToMmol(p.hba1c_pct) - 31) / 9.34, legfr = (log(p.egfr) - 4.5) / 0.15;
    const smk = p.smoker ? 1 : 0;
    const lp = b.age * cage + b.smk * smk + b.sbp * csbp + b.dm * 1 + b.tc * ctc + b.hdl * chdl
      + b.age_smk * cage * smk + b.age_sbp * cage * csbp + b.age_dm * cage + b.age_tc * cage * ctc
      + b.age_hdl * cage * chdl + b.dm_agedx * cdx + b.a1c * ca1c + b.legfr * legfr + b.legfr2 * legfr * legfr
      + b.a1c_age * ca1c * cage + b.legfr_age * legfr * cage;
    return cloglogRecal(lp, S2D_S0[sex], sex, p.risk_region) * 100;
  }

  // ----------------------------------------------------------------- SCORE2 (ESC 2021, 40-69)
  // Coefficients: SCORE2 working group, Eur Heart J 2021;42:2439, tabulated to 4 d.p. in Hageman
  // et al., Eur Heart J 2022;43:241 (Table 1). NOTE: the fitted SCORE2 model DOES contain a diabetes
  // term (0.6457 men / 0.8096 women) and an age×diabetes interaction (−0.0983 / −0.1272), but SCORE2
  // "is not intended for use in individuals with diabetes" and in its target population that term is
  // always 0 (Hageman 2022, footnote a). The default below therefore reproduces SCORE2 exactly as it is
  // deployed (charts/HeartScore) for people without diabetes, i.e. with the diabetes term at 0 — which is
  // what a clinician "borrowing" SCORE2 for a T1D patient would obtain. Pass {diabetesTerm: true} to
  // apply the published diabetes coefficients instead (sensitivity analysis; also off-label in T1D).
  const S2_S0 = { male: 0.9605, female: 0.9776 };
  const S2 = {
    male: { age: 0.3742, smk: 0.6012, sbp: 0.2777, tc: 0.1458, hdl: -0.2698, age_smk: -0.0755,
      age_sbp: -0.0255, age_tc: -0.0281, age_hdl: 0.0426, dm: 0.6457, age_dm: -0.0983 },
    female: { age: 0.4648, smk: 0.7744, sbp: 0.3131, tc: 0.1002, hdl: -0.2606, age_smk: -0.1088,
      age_sbp: -0.0277, age_tc: -0.0226, age_hdl: 0.0613, dm: 0.8096, age_dm: -0.1272 },
  };
  function score2(p, opts) {
    if (p.age < 40 || p.age >= 70) return NaN;
    const sex = p.female ? "female" : "male", b = S2[sex];
    const dm = (opts && opts.diabetesTerm && p.diabetes !== false) ? 1 : 0; // default 0: SCORE2 as deployed
    const cage = (p.age - 60) / 5, csbp = (p.sbp - 120) / 20, ctc = p.total_chol - 6, chdl = (p.hdl - 1.3) / 0.5, smk = p.smoker ? 1 : 0;
    const lp = b.age * cage + b.smk * smk + b.sbp * csbp + b.tc * ctc + b.hdl * chdl
      + b.age_smk * cage * smk + b.age_sbp * cage * csbp + b.age_tc * cage * ctc + b.age_hdl * cage * chdl
      + b.dm * dm + b.age_dm * cage * dm;
    return cloglogRecal(lp, S2_S0[sex], sex, p.risk_region) * 100;
  }

  // ----------------------------------------------------------------- PCE (ACC/AHA 2013)
  const PCE = {
    white_female: { ln_age: -29.799, ln_age2: 4.884, ln_tc: 13.540, ln_age_tc: -3.114, ln_hdl: -13.578,
      ln_age_hdl: 3.149, ln_sbp_t: 2.019, ln_sbp_u: 1.957, smk: 7.574, ln_age_smk: -1.665, dm: 0.661, S0: 0.9665, mean: -29.18 },
    black_female: { ln_age: 17.114, ln_tc: 0.940, ln_hdl: -18.920, ln_age_hdl: 4.475, ln_sbp_t: 29.291,
      ln_age_sbp_t: -6.432, ln_sbp_u: 27.820, ln_age_sbp_u: -6.087, smk: 0.691, dm: 0.874, S0: 0.9533, mean: 86.61 },
    white_male: { ln_age: 12.344, ln_tc: 11.853, ln_age_tc: -2.664, ln_hdl: -7.990, ln_age_hdl: 1.769,
      ln_sbp_t: 1.797, ln_sbp_u: 1.764, smk: 7.837, ln_age_smk: -1.795, dm: 0.658, S0: 0.9144, mean: 61.18 },
    black_male: { ln_age: 2.469, ln_tc: 0.302, ln_hdl: -0.307, ln_sbp_t: 1.916, ln_sbp_u: 1.809, smk: 0.549, dm: 0.645, S0: 0.8954, mean: 19.54 },
  };
  function pce(p) {
    if (p.age < 40 || p.age >= 80) return NaN;
    const grp = (p.ethnicity === "black" ? "black" : "white") + "_" + (p.female ? "female" : "male");
    const b = PCE[grp], g = (k) => b[k] || 0;
    const la = log(p.age), ltc = log(p.total_chol * MGDL), lhdl = log(p.hdl * MGDL), lsbp = log(p.sbp), smk = p.smoker ? 1 : 0;
    let ind = g("ln_age") * la + g("ln_age2") * la * la + g("ln_tc") * ltc + g("ln_age_tc") * la * ltc
      + g("ln_hdl") * lhdl + g("ln_age_hdl") * la * lhdl + g("smk") * smk + g("ln_age_smk") * la * smk
      + g("dm") * ((p.diabetes === false) ? 0 : 1); // default: T1D patient
    if (p.on_bp_treatment) ind += g("ln_sbp_t") * lsbp + g("ln_age_sbp_t") * la * lsbp;
    else ind += g("ln_sbp_u") * lsbp + g("ln_age_sbp_u") * la * lsbp;
    return (1 - Math.pow(b.S0, exp(ind - b.mean))) * 100;
  }

  const qrisk3 = (typeof module !== "undefined" && module.exports) ? require("./qrisk3.js") : root.QRISK3;

  // ----------------------------------------------------------------- AHA PREVENT (2024) total CVD 10y
  const PREVENT = {
    female: { c: -3.307728, age: 0.7939329, nonhdl: 0.0305239, hdl: -0.1606857, sbp_lo: -0.2394003, sbp_hi: 0.3600781, dm: 0.8667604, smk: 0.5360739, egfr_lo: 0.6045917, egfr_hi: 0.0433769, bptx: 0.3151672, statin: -0.1477655, bptx_sbphi: -0.0663612, statin_nonhdl: 0.1197879, age_nonhdl: -0.0819715, age_hdl: 0.0306769, age_sbphi: -0.0946348, age_dm: -0.27057, age_smk: -0.078715, age_egfrlo: -0.1637806 },
    male: { c: -3.031168, age: 0.7688528, nonhdl: 0.0736174, hdl: -0.0954431, sbp_lo: -0.4347345, sbp_hi: 0.3362658, dm: 0.7692857, smk: 0.4386871, egfr_lo: 0.5378979, egfr_hi: 0.0164827, bptx: 0.288879, statin: -0.1337349, bptx_sbphi: -0.0475924, statin_nonhdl: 0.150273, age_nonhdl: -0.0517874, age_hdl: 0.0191169, age_sbphi: -0.1049477, age_dm: -0.2251948, age_smk: -0.0895067, age_egfrlo: -0.1543702 },
  };
  function prevent(p) {
    if (p.age < 30 || p.age >= 80) return NaN;
    const b = PREVENT[p.female ? "female" : "male"];
    const nonhdl = (p.total_chol - p.hdl) - 3.5, hdl_t = (p.hdl - 1.3) / 0.3, age_t = (p.age - 55) / 10;
    const sbp_lo = (min(p.sbp, 110) - 110) / 20, sbp_hi = (max(p.sbp, 110) - 130) / 20;
    const egfr_lo = (min(p.egfr, 60) - 60) / -15, egfr_hi = (max(p.egfr, 60) - 90) / -15;
    const dm = (p.diabetes === false) ? 0 : 1, smk = p.smoker ? 1 : 0, bptx = p.on_bp_treatment ? 1 : 0, stat = p.on_statin ? 1 : 0;
    const lp = b.c + b.age * age_t + b.nonhdl * nonhdl + b.hdl * hdl_t + b.sbp_lo * sbp_lo + b.sbp_hi * sbp_hi
      + b.dm * dm + b.smk * smk + b.egfr_lo * egfr_lo + b.egfr_hi * egfr_hi + b.bptx * bptx + b.statin * stat
      + b.bptx_sbphi * bptx * sbp_hi + b.statin_nonhdl * stat * nonhdl + b.age_nonhdl * age_t * nonhdl
      + b.age_hdl * age_t * hdl_t + b.age_sbphi * age_t * sbp_hi + b.age_dm * age_t * dm + b.age_smk * age_t * smk + b.age_egfrlo * age_t * egfr_lo;
    return 100 * exp(lp) / (1 + exp(lp));
  }

  // ----------------------------------------------------------------- Framingham general CVD (D'Agostino 2008)
  const FRS = {
    female: { S0: 0.95012, mean: 26.1931, ln_age: 2.32888, ln_tc: 1.20904, ln_hdl: -0.70833, ln_sbp_u: 2.76157, ln_sbp_t: 2.82263, smk: 0.52873, dm: 0.69154 },
    male: { S0: 0.88936, mean: 23.9802, ln_age: 3.06117, ln_tc: 1.12370, ln_hdl: -0.93263, ln_sbp_u: 1.93303, ln_sbp_t: 1.99881, smk: 0.65451, dm: 0.57367 },
  };
  function framingham(p) {
    if (p.age < 30 || p.age >= 75) return NaN;
    const b = FRS[p.female ? "female" : "male"];
    const lp = b.ln_age * log(p.age) + b.ln_tc * log(p.total_chol * MGDL) + b.ln_hdl * log(p.hdl * MGDL)
      + (p.on_bp_treatment ? b.ln_sbp_t : b.ln_sbp_u) * log(p.sbp) + b.smk * (p.smoker ? 1 : 0) + b.dm * ((p.diabetes === false) ? 0 : 1);
    return 100 * (1 - Math.pow(b.S0, exp(lp - b.mean)));
  }

  // ----------------------------------------------------------------- UKPDS Risk Engine (CHD+stroke)
  // UKPDS 56 (Stevens 2001, Clin Sci 101:671) and UKPDS 60 (Kothari 2002, Stroke 33:1776).
  // Both engines define AGE as age AT DIAGNOSIS of diabetes; duration since diagnosis enters
  // separately through d^T (Stevens Table 2/3; Kothari Table 3). Passing current age would count
  // duration twice (b1^T extra) — the wrapper below therefore uses onset age.
  // CHD lipid term is exp-centred on ln(TC/HDL) = 1.59; the STROKE lipid term is linear,
  // 1.138^(TC/HDL − 5.11) (Kothari 2002, model equation and worked example).
  function ukpdsCHD(ageDx, female, afrocarib, smoker, hba1c_pct, sbp, tc_hdl, duration, t) {
    const q = 0.0112 * Math.pow(1.059, ageDx - 55) * Math.pow(0.525, female ? 1 : 0) * Math.pow(0.390, afrocarib ? 1 : 0)
      * Math.pow(1.350, smoker ? 1 : 0) * Math.pow(1.183, hba1c_pct - 6.72) * Math.pow(1.088, (sbp - 135.7) / 10)
      * Math.pow(3.845, log(tc_hdl) - 1.59);
    const d = 1.078;
    return 1 - exp(-q * Math.pow(d, duration) * (1 - Math.pow(d, t)) / (1 - d));
  }
  function ukpdsStroke(ageDx, female, smoker, af, sbp, tc_hdl, duration, t) {
    const q = 0.00186 * Math.pow(1.092, ageDx - 55) * Math.pow(0.700, female ? 1 : 0) * Math.pow(1.547, smoker ? 1 : 0)
      * Math.pow(8.554, af ? 1 : 0) * Math.pow(1.122, (sbp - 135.5) / 10) * Math.pow(1.138, tc_hdl - 5.11);
    const d = 1.145;
    return 1 - exp(-q * Math.pow(d, duration) * (1 - Math.pow(d, t)) / (1 - d));
  }
  function ukpds(p) {
    const ageDx = (p.onset_age != null) ? p.onset_age : p.age - p.duration; // age at diagnosis (UKPDS definition)
    const afrocarib = p.ethnicity === "black";
    const chd = ukpdsCHD(ageDx, p.female, afrocarib, p.smoker, p.hba1c_pct, p.sbp, p.tc_hdl_ratio, p.duration, 10);
    const str = ukpdsStroke(ageDx, p.female, p.smoker, p.af, p.sbp, p.tc_hdl_ratio, p.duration, 10);
    return 100 * (1 - (1 - chd) * (1 - str)); // independence approximation (not from the UKPDS papers)
  }

  // ----------------------------------------------------------------- ADVANCE (Kengne 2011) 4y -> 10y extrapolated
  const ADV = { age_dx: 0.06187, female: -0.4736, duration: 0.08263, pp: 0.00665, retino: 0.38248, af: 0.60106, a1c: 0.09945, ln_acr: 0.19341, nonhdl: 0.12619, treated_htn: 0.24219 };
  // ACR entered in mg/g (the unit the ln_acr coefficient was fitted on): normal<30, micro 30-300, macro>300.
  // Native endpoint is 4-year; the 10-year figure below is a constant-hazard extrapolation beyond validation.
  const ADV_S0_4 = 0.951044, ADV_MEANLP = 6.5267, ACR_MAP = { normal: 10, micro: 100, macro: 500 };
  function advance(p, horizon) {
    const lp = ADV.age_dx * p.onset_age + ADV.female * (p.female ? 1 : 0) + ADV.duration * p.duration
      + ADV.pp * (p.sbp - p.dbp) + ADV.retino * (p.retinopathy ? 1 : 0) + ADV.af * (p.af ? 1 : 0)
      + ADV.a1c * p.hba1c_pct + ADV.ln_acr * log(ACR_MAP[p.albuminuria]) + ADV.nonhdl * (p.total_chol - p.hdl) + ADV.treated_htn * (p.on_bp_treatment ? 1 : 0);
    const r4 = 1 - Math.pow(ADV_S0_4, exp(lp - ADV_MEANLP));
    const h = horizon || 10;
    return 100 * (h === 4 ? r4 : 1 - Math.pow(1 - r4, h / 4));
  }

  // ----------------------------------------------------------------- Cederholm NDR 5y (T1D)
  const CED_B = { duration: 0.08426, onset: 0.04742, ln_tchdl: 0.80050, ln_a1c: 1.27275, ln_sbp: 1.20050, smoker: 0.56688, macro: 0.41995, prior: 1.25506 };
  const CED_C = { duration: 28.014, onset: 16.601, ln_tchdl: 1.1470, ln_a1c: 2.0605, ln_sbp: 4.8598, smoker: 0.1483, macro: 0.1237, prior: 0.0612 };
  const CED_S0_5 = 0.97136;
  function cederholm(p) {
    const onset = p.onset_age;
    const lp = CED_B.duration * (p.duration - CED_C.duration) + CED_B.onset * (onset - CED_C.onset)
      + CED_B.ln_tchdl * (log(p.tc_hdl_ratio) - CED_C.ln_tchdl) + CED_B.ln_a1c * (log(p.hba1c_pct) - CED_C.ln_a1c)
      + CED_B.ln_sbp * (log(p.sbp) - CED_C.ln_sbp) + CED_B.smoker * ((p.smoker ? 1 : 0) - CED_C.smoker)
      + CED_B.macro * ((p.albuminuria === "macro" ? 1 : 0) - CED_C.macro) + CED_B.prior * ((p.prior_cvd ? 1 : 0) - CED_C.prior);
    return 100 * (1 - Math.pow(CED_S0_5, exp(lp)));
  }

  // ----------------------------------------------------------------- model registry
  // category: T1D | T2D | general. implementationChecked means that selected
  // reference, live-tool, or regression checks passed; it is not external
  // clinical validation in a T1D outcomes cohort.
  // Registry fields: ageRange = hard coded-age limits (NaN outside, as in the source implementations);
  // extrapolation(p) = optional caution when inputs fall outside the derivation range stated in the
  // source paper.
  const MODELS = {
    "Steno-CVD":        { category: "T1D", horizon: "10y", endpoint: "composite CVD (IHD, stroke, HF, PAD)", implementationChecked: true, fn: (p) => steno(p, 10, "cvd"), note: "Composite incl. heart failure & PAD; derivation 18–90 y, no prior CVD. Selected live-tool output reproduced to reported precision; 10-y risk internally validated only (external validation was 5-y)." },
    "Steno-IHD/stroke": { category: "T1D", horizon: "10y", endpoint: "IHD or stroke (narrower)", implementationChecked: true, fn: (p) => steno(p, 10, "ihd_stroke"), note: "Secondary, narrower IHD-or-stroke endpoint; coefficients source-checked against Vistisen 2016 Supplemental Table 4. Separately fitted equation for a narrower endpoint." },
    "Cederholm (5y)":   { category: "T1D", horizon: "5y",  endpoint: "CHD or stroke, 5-year", implementationChecked: true, fn: (p) => cederholm(p), extrapolation: (p) => (p.age < 30 || p.age > 65) ? "outside derivation age range 30–65 y" : null, note: "Native 5-year endpoint (derivation age 30–65 y); shown separately and excluded from the 10-year agreement matrix." },
    "SCORE2-Diabetes":  { category: "T2D", horizon: "10y", endpoint: "CV death, MI, stroke", ageRange: [40, 79], implementationChecked: true, fn: (p) => score2diabetes(p), note: "Derived in type-2 diabetes; no T1D calibration study; coded age 40–79." },
    "SCORE2":           { category: "general", horizon: "10y", endpoint: "CV death, MI, stroke", ageRange: [40, 69], implementationChecked: true, fn: (p) => score2(p), note: "General population, not intended for people with diabetes; run as deployed, i.e. with its published diabetes term at 0 (Hageman 2022); coded age 40–69." },
    "QRISK3":           { category: "general", horizon: "10y", endpoint: "CHD, ischaemic stroke, TIA", ageRange: [25, 84], implementationChecked: true, fn: (p) => qrisk3(p), extrapolation: (p) => p.on_statin ? "Statin use at baseline was excluded from QRISK3 derivation" : null, note: "Dedicated T1D term; UK-calibrated; SBP variability and Townsend score set to 0; coded age 25–84." },
    "PCE (ACC/AHA)":    { category: "general", horizon: "10y", endpoint: "hard ASCVD", ageRange: [40, 79], implementationChecked: true, fn: (p) => pce(p), note: "Hard ASCVD; diabetes represented as binary; coded age 40–79." },
    "AHA PREVENT":      { category: "general", horizon: "10y", endpoint: "total CVD incl. HF", ageRange: [30, 79], implementationChecked: true, fn: (p) => prevent(p), note: "Base total-CVD equation incl. heart failure; diabetes binary; coded age 30–79." },
    "Framingham":       { category: "general", horizon: "10y", endpoint: "general CVD composite", ageRange: [30, 74], implementationChecked: true, fn: (p) => framingham(p), note: "Broad general-population CVD composite; diabetes binary; coded age 30–74." },
    "UKPDS":            { category: "T2D", horizon: "10y", endpoint: "CHD + stroke (independence approx.)", implementationChecked: true, fn: (p) => ukpds(p), extrapolation: (p) => { const dx = (p.onset_age != null) ? p.onset_age : p.age - p.duration; const w = []; if (dx < 25 || dx > 65) w.push("age at diagnosis outside 25–65 y"); if (p.duration > 20) w.push("more than 20 y since diagnosis"); return w.length ? w.join("; ") + " (UKPDS: extrapolation)" : null; }, note: "Published-paper T2D equations; the stroke lipid form conflicts with Oxford’s 2024 parameter sheet (see repository METHODS.md). Age enters as age AT DIAGNOSIS with duration separately; beyond 20 y of diabetes the papers call the output an extrapolation." },
    "ADVANCE*":         { category: "T2D", horizon: "10y*", endpoint: "CV death, MI, stroke (4-y native)", implementationChecked: false, fn: (p) => advance(p, 10), extrapolation: (p) => { const dx = (p.onset_age != null) ? p.onset_age : p.age - p.duration; const w = []; if (p.age < 55) w.push("age < 55 y"); if (dx < 30) w.push("diagnosis before 30 y"); return w.length ? w.join("; ") + " (ADVANCE cohort: ≥55 y, diagnosed ≥30 y)" : null; }, note: "Reconstructed centring constant 6.5267; native four-year endpoint extrapolated to ten years under a constant-hazard assumption; albuminuria category mapped to ACR 10/100/500 mg/g." },
  };

  // Common analytic bands for ordinal agreement; not universal treatment thresholds.
  function band(pct) { return Number.isFinite(pct) ? (pct < 10 ? 0 : (pct < 20 ? 1 : 2)) : -1; }
  const BAND_LABEL = ["<10%", "10–<20%", "≥20%"];

  const API = { hba1cPctToMmol, hba1cMmolToPct, MODELS, band, BAND_LABEL,
    steno, score2diabetes, score2, pce, qrisk3, prevent, framingham, ukpds, ukpdsCHD, ukpdsStroke, advance, cederholm };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  else root.T1DCVD = API;
})(typeof window !== "undefined" ? window : globalThis);
