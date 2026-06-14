/*
 * T1D-CVD meta-calculator — open, transparent risk-model engine.
 *
 * Pure JavaScript ports of published cardiovascular risk equations, checked
 * against source-paper worked examples or live tools where available. Every
 * coefficient is in this file — no hidden parameters. Runs in the browser and
 * in Node (for the test harness).
 *
 * IMPORTANT: this engine does not invent a new model. It reproduces published
 * calculator equations with endpoint-specific validation status so they can be
 * run side by side, compared, and recalibrated transparently. It is an
 * agreement/decision-support tool, NOT a validated accuracy claim.
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
  function cloglogRecal(unc, sex, region) {
    const s = SCALES[sex][region];
    return 1 - exp(-exp(s[0] + s[1] * log(-log(1 - unc))));
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
    const sex = p.female ? "female" : "male", b = S2D[sex];
    const cage = (p.age - 60) / 5, csbp = (p.sbp - 120) / 20, ctc = p.total_chol - 6, chdl = (p.hdl - 1.3) / 0.5;
    const cdx = (p.onset_age - 50) / 5, ca1c = (hba1cPctToMmol(p.hba1c_pct) - 31) / 9.34, legfr = (log(p.egfr) - 4.5) / 0.15;
    const smk = p.smoker ? 1 : 0;
    const lp = b.age * cage + b.smk * smk + b.sbp * csbp + b.dm * 1 + b.tc * ctc + b.hdl * chdl
      + b.age_smk * cage * smk + b.age_sbp * cage * csbp + b.age_dm * cage + b.age_tc * cage * ctc
      + b.age_hdl * cage * chdl + b.dm_agedx * cdx + b.a1c * ca1c + b.legfr * legfr + b.legfr2 * legfr * legfr
      + b.a1c_age * ca1c * cage + b.legfr_age * legfr * cage;
    const unc = 1 - Math.pow(S2D_S0[sex], exp(lp));
    return cloglogRecal(unc, sex, p.risk_region) * 100;
  }

  // ----------------------------------------------------------------- SCORE2 (ESC 2021, 40-69)
  const S2_S0 = { male: 0.9605, female: 0.9776 };
  // Published SCORE2 (2021) has SIX predictors only — age, smoking, SBP, total & HDL
  // cholesterol, and their age interactions. It deliberately has NO diabetes term
  // (that is the raison d'etre of the separate SCORE2-Diabetes model). Do not add one.
  const S2 = {
    male: { age: 0.3742, smk: 0.6012, sbp: 0.2777, tc: 0.1458, hdl: -0.2698, age_smk: -0.0755,
      age_sbp: -0.0255, age_tc: -0.0281, age_hdl: 0.0426 },
    female: { age: 0.4648, smk: 0.7744, sbp: 0.3131, tc: 0.1002, hdl: -0.2606, age_smk: -0.1088,
      age_sbp: -0.0277, age_tc: -0.0226, age_hdl: 0.0613 },
  };
  function score2(p) {
    if (p.age < 40 || p.age > 69) return NaN;
    const sex = p.female ? "female" : "male", b = S2[sex];
    const cage = (p.age - 60) / 5, csbp = (p.sbp - 120) / 20, ctc = p.total_chol - 6, chdl = (p.hdl - 1.3) / 0.5, smk = p.smoker ? 1 : 0;
    const lp = b.age * cage + b.smk * smk + b.sbp * csbp + b.tc * ctc + b.hdl * chdl
      + b.age_smk * cage * smk + b.age_sbp * cage * csbp + b.age_tc * cage * ctc + b.age_hdl * cage * chdl;
    const unc = 1 - Math.pow(S2_S0[sex], exp(lp));
    return cloglogRecal(unc, sex, p.risk_region) * 100;
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
    if (p.age < 40 || p.age > 79) return NaN;
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

  // ----------------------------------------------------------------- QRISK3 (2017)
  const Q = require_qrisk();
  function require_qrisk() {
    return {
      S0: { female: 0.988876402378082, male: 0.977268040180206 },
      ieth: { female: { 1: 0, 2: 0.28040314332995425, 3: 0.56298994142075398, 4: 0.29590000851116516, 5: 0.072785379877982545, 6: -0.17072135508857317, 7: -0.39371043314874971, 8: -0.32632495283530272, 9: -0.17127056883241784 },
        male: { 1: 0, 2: 0.27719248760308279, 3: 0.47446360714931268, 4: 0.52961729919689371, 5: 0.035100159186299017, 6: -0.35807899669327919, 7: -0.40056485232165140, 8: -0.41522792889830173, 9: -0.26321348134749967 } },
      ismoke: { female: { 0: 0, 1: 0.13386833786546262, 2: 0.56200858012438537, 3: 0.66749593377502547, 4: 0.84948177644830847 },
        male: { 0: 0, 1: 0.19128222863388983, 2: 0.55241588192645552, 3: 0.63835053027506072, 4: 0.78983819881858019 } },
      main: { female: { age1: -8.1388109247726188, age2: 0.79733376689699098, bmi1: 0.29236092275460052, bmi2: -4.1513300213837665, rati: 0.15338035820802554, sbp: 0.013131488407103424, sbps5: 0.0078894541014586095, town: 0.077223790588590108, b_AF: 1.5923354969269663, b_corticosteroids: 0.59520725304601851, b_migraine: 0.30126726087034500, b_ra: 0.21364803435181942, b_renal: 0.65194569493845833, b_sle: 0.75880938654267693, b_treatedhyp: 0.50931593683423004, b_type1: 1.7267977510537347, b_type2: 1.0688773244615468, fh_cvd: 0.45445319020896213 },
        male: { age1: -17.839781666005575, age2: 0.0022964880605765492, bmi1: 2.4562776660536358, bmi2: -8.3011122314711354, rati: 0.17340196856327111, sbp: 0.012910126542553305, sbps5: 0.010251914291290456, town: 0.033268201277287295, b_AF: 0.88209236928054657, b_corticosteroids: 0.45485399750445543, b_migraine: 0.25584178074159913, b_ra: 0.20970658013956567, b_renal: 0.71853261288274384, b_sle: 0.44015721744575220, b_treatedhyp: 0.51659871082695474, b_type1: 1.2343425521675175, b_type2: 0.85942071430932221, fh_cvd: 0.54055469009390156 } },
      center: { female: { age1: 0.053274843841791, age2: 4.332503318786621, bmi1: 0.154946178197861, bmi2: 0.144462317228317, rati: 3.476326465606690, sbp: 123.130012512207030, sbps5: 9.002537727355957, town: 0.392308831214905 },
        male: { age1: 0.234766781330109, age2: 77.284080505371094, bmi1: 0.149176135659218, bmi2: 0.141913309693336, rati: 4.300998687744141, sbp: 128.571578979492190, sbps5: 8.756621360778809, town: 0.526304900646210 } },
      smkA1: { female: { 1: -4.7057161785851891, 2: -2.7430383403573337, 3: -0.86608088829392182, 4: 0.90241562369710648 }, male: { 1: -0.21011133933516346, 2: 0.75268676447503191, 3: 0.99315887556405791, 4: 2.1331163414389076 } },
      smkA2: { female: { 1: -0.075589244643193026, 2: -0.11951192874867074, 3: -0.10366306397571923, 4: -0.13991853591718389 }, male: { 1: -0.00049854870275326121, 2: -0.00079875633317385414, 3: -0.00083706184266251296, 4: -0.00078400319155637289 } },
      a1: { female: { b_AF: 19.938034889546561, b_corticosteroids: -0.98408045235936281, b_migraine: 1.7634979587872999, b_renal: -3.5874047731694114, b_sle: 19.690303738638292, b_treatedhyp: 11.872809733921812, b_type1: -1.2444332714320747, b_type2: 6.8652342000009599, bmi1: 23.802623412141742, bmi2: -71.184947692087007, fh_cvd: 0.99467807940435127, sbp: 0.034131842338615485, town: -1.0301180802035639 },
        male: { b_AF: 3.4896675530623207, b_corticosteroids: 1.1708133653489108, b_migraine: 2.3491159871402441, b_renal: -0.50656716327223694, b_treatedhyp: 6.5114581098532671, b_type1: 5.3379864878006531, b_type2: 3.6461817406221311, bmi1: 31.004952956033886, bmi2: -111.29157184391643, fh_cvd: 2.7808628508531887, sbp: 0.018858524469865853, town: -0.10075548700637310 } },
      a2: { female: { b_AF: -0.076182651011162505, b_corticosteroids: -0.12005364946742472, b_migraine: -0.065586917898699859, b_renal: -0.22688873086442507, b_sle: 0.077347949679016273, b_treatedhyp: 0.00096857823588174436, b_type1: -0.28724064624488949, b_type2: -0.097112252590695489, bmi1: 0.52369958933664429, bmi2: 0.045744190122323759, fh_cvd: -0.076885051698423038, sbp: -0.0015082501423272358, town: -0.031593414674962329 },
        male: { b_AF: -0.00034995608340636049, b_corticosteroids: -0.00024960450952971660, b_migraine: 0.00019896446041478631, b_renal: -0.0018325930166498813, b_treatedhyp: 0.00063838053104165013, b_type1: 0.00064097808087528970, b_type2: -0.00024695695588868315, bmi1: 0.0050380102356322029, bmi2: -0.013074483002524319, fh_cvd: -0.00024791809907396037, sbp: -0.000012718741915884570, town: -0.000093299642323272888 } },
    };
  }
  function qrisk3(p) {
    if (p.age < 25 || p.age > 84) return NaN;
    const sex = p.female ? "female" : "male", m = Q.main[sex], c = Q.center[sex];
    let age1 = p.female ? Math.pow(p.age / 10, -2) : Math.pow(p.age / 10, -1);
    let age2 = p.female ? (p.age / 10) : Math.pow(p.age / 10, 3);
    let bmi1 = Math.pow(p.bmi / 10, -2), bmi2 = Math.pow(p.bmi / 10, -2) * log(p.bmi / 10);
    age1 -= c.age1; age2 -= c.age2; bmi1 -= c.bmi1; bmi2 -= c.bmi2;
    const rati_c = p.tc_hdl_ratio - c.rati, sbp_c = p.sbp - c.sbp, town_c = (p.town || 0) - c.town;
    const sbps5_c = ((p.sbps5 != null) ? p.sbps5 : 0) - c.sbps5; // SD of SBP; ClinRisk convention: unknown -> raw 0, THEN centre
    const smk = (p.smoke_cat != null) ? p.smoke_cat : (p.smoker ? 2 : 0); // current smoker -> "light" (documented mapping)
    let a = Q.ieth[sex][p.ethrisk || 1] + Q.ismoke[sex][smk];
    a += age1 * m.age1 + age2 * m.age2 + bmi1 * m.bmi1 + bmi2 * m.bmi2 + rati_c * m.rati + sbp_c * m.sbp + sbps5_c * m.sbps5 + town_c * m.town;
    const bools = { b_AF: p.af, b_corticosteroids: false, b_migraine: false, b_ra: false, b_renal: p.egfr < 60, b_sle: false, b_treatedhyp: p.on_bp_treatment, b_type1: (p.b_type1 != null ? p.b_type1 : true), b_type2: (p.b_type2 || false), fh_cvd: p.family_history_cvd };
    for (const k in bools) if (bools[k] && m[k] != null) a += m[k];
    if (smk > 0) a += age1 * Q.smkA1[sex][smk] + age2 * Q.smkA2[sex][smk];
    a += age1 * bmi1 * Q.a1[sex].bmi1 + age2 * bmi1 * Q.a2[sex].bmi1 + age1 * bmi2 * Q.a1[sex].bmi2 + age2 * bmi2 * Q.a2[sex].bmi2;
    a += age1 * sbp_c * Q.a1[sex].sbp + age2 * sbp_c * Q.a2[sex].sbp + age1 * town_c * Q.a1[sex].town + age2 * town_c * Q.a2[sex].town;
    for (const k in bools) if (bools[k] && Q.a1[sex][k] != null) a += age1 * Q.a1[sex][k] + age2 * Q.a2[sex][k];
    return (1 - Math.pow(Q.S0[sex], exp(a))) * 100;
  }

  // ----------------------------------------------------------------- AHA PREVENT (2024) total CVD 10y
  const PREVENT = {
    female: { c: -3.307728, age: 0.7939329, nonhdl: 0.0305239, hdl: -0.1606857, sbp_lo: -0.2394003, sbp_hi: 0.3600781, dm: 0.8667604, smk: 0.5360739, egfr_lo: 0.6045917, egfr_hi: 0.0433769, bptx: 0.3151672, statin: -0.1477655, bptx_sbphi: -0.0663612, statin_nonhdl: 0.1197879, age_nonhdl: -0.0819715, age_hdl: 0.0306769, age_sbphi: -0.0946348, age_dm: -0.27057, age_smk: -0.078715, age_egfrlo: -0.1637806 },
    male: { c: -3.031168, age: 0.7688528, nonhdl: 0.0736174, hdl: -0.0954431, sbp_lo: -0.4347345, sbp_hi: 0.3362658, dm: 0.7692857, smk: 0.4386871, egfr_lo: 0.5378979, egfr_hi: 0.0164827, bptx: 0.288879, statin: -0.1337349, bptx_sbphi: -0.0475924, statin_nonhdl: 0.150273, age_nonhdl: -0.0517874, age_hdl: 0.0191169, age_sbphi: -0.1049477, age_dm: -0.2251948, age_smk: -0.0895067, age_egfrlo: -0.1543702 },
  };
  function prevent(p) {
    if (p.age < 30 || p.age > 79) return NaN;
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
    if (p.age < 30 || p.age > 74) return NaN;
    const b = FRS[p.female ? "female" : "male"];
    const lp = b.ln_age * log(p.age) + b.ln_tc * log(p.total_chol * MGDL) + b.ln_hdl * log(p.hdl * MGDL)
      + (p.on_bp_treatment ? b.ln_sbp_t : b.ln_sbp_u) * log(p.sbp) + b.smk * (p.smoker ? 1 : 0) + b.dm * ((p.diabetes === false) ? 0 : 1);
    return 100 * (1 - Math.pow(b.S0, exp(lp - b.mean)));
  }

  // ----------------------------------------------------------------- UKPDS Risk Engine (CHD+stroke)
  function ukpdsCHD(age, female, smoker, hba1c_pct, sbp, tc_hdl, duration, t) {
    const q = 0.0112 * Math.pow(1.059, age - 55) * Math.pow(0.525, female ? 1 : 0) * Math.pow(1.350, smoker ? 1 : 0)
      * Math.pow(1.183, hba1c_pct - 6.72) * Math.pow(1.088, (sbp - 135.7) / 10) * Math.pow(3.845, log(tc_hdl) - 1.59);
    const d = 1.078;
    return 1 - exp(-q * Math.pow(d, duration) * (1 - Math.pow(d, t)) / (1 - d));
  }
  function ukpdsStroke(age, female, smoker, af, sbp, tc_hdl, duration, t) {
    const q = 0.00186 * Math.pow(1.092, age - 55) * Math.pow(0.700, female ? 1 : 0) * Math.pow(1.547, smoker ? 1 : 0)
      * Math.pow(8.554, af ? 1 : 0) * Math.pow(1.122, (sbp - 135.5) / 10) * Math.pow(1.138, log(tc_hdl) - 1.59);
    const d = 1.145;
    return 1 - exp(-q * Math.pow(d, duration) * (1 - Math.pow(d, t)) / (1 - d));
  }
  function ukpds(p) {
    const chd = ukpdsCHD(p.age, p.female, p.smoker, p.hba1c_pct, p.sbp, p.tc_hdl_ratio, p.duration, 10);
    const str = ukpdsStroke(p.age, p.female, p.smoker, p.af, p.sbp, p.tc_hdl_ratio, p.duration, 10);
    return 100 * (1 - (1 - chd) * (1 - str));
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

  // ----------------------------------------------------------------- Scottish-Swedish (McGurnaghan 2021), final model + cal
  const SS = { intercept: -4.03403744, age_entry: -0.03356271, age: 0.32483759, age2: -0.00389356, age3: 1.993e-05,
    female: -0.91153788, duration: 0.0201993, hba1c: 0.01071311, mean_hba1c: 0.02712284, log_bmi: -1.9247447,
    height: -2.84393889, weight: 0.00802065, sbp: 0.0041725, log_tchdl: 0.49545924, log_egfr: -0.34828245,
    alb_micro: 0.34128044, alb_macro: 0.91835596, retino_nonref: 0.09832872, retino_ref: 0.40705123, smoke_ever: 0.34002647,
    treated_htn: 0.30504081, treated_dyslip: 0.14012891, af: 0.61882651, female_log_tchdl: 0.39282042, age_weight: 0.00023665, female_hba1c: 0.00335224, age_mean_hba1c: -0.00028851 };
  const SS_DEP = { 1: 0, 2: -0.11366821, 3: -0.28641292, 4: -0.38497544, 5: -0.55777639 };
  const SS_HEIGHT = { male: 1.75, female: 1.62 };
  const SS_CAL = 1.32; // calibration constant fit to the deployed Shiny tool (publication rounds cubic/interaction coeffs to 3 d.p.)
  function scottishSwedish(p, years) {
    const sex = p.female ? "female" : "male", h = p.height_m || SS_HEIGHT[sex], weight = p.weight_kg || p.bmi * h * h;
    const a1cMmol = hba1cPctToMmol(p.hba1c_pct), meanA1c = a1cMmol;
    const dq = p.deprivation_quintile || 3;
    let fixed = SS.intercept + SS.age_entry * p.age + SS.female * (p.female ? 1 : 0) + SS.duration * p.duration
      + SS.hba1c * a1cMmol + SS.mean_hba1c * meanA1c + SS.log_bmi * log(p.bmi) + SS.height * h + SS.weight * weight
      + SS.sbp * p.sbp + SS.log_tchdl * log(p.tc_hdl_ratio) + SS.log_egfr * log(p.egfr)
      + SS.alb_micro * (p.albuminuria === "micro" ? 1 : 0) + SS.alb_macro * (p.albuminuria === "macro" ? 1 : 0)
      + SS.smoke_ever * (p.smoker ? 1 : 0) + SS.treated_htn * (p.on_bp_treatment ? 1 : 0) + SS.treated_dyslip * (p.on_statin ? 1 : 0)
      + SS.af * (p.af ? 1 : 0) + SS.female_log_tchdl * (p.female ? 1 : 0) * log(p.tc_hdl_ratio)
      + (p.retinopathy === "ref" ? SS.retino_ref : ((p.retinopathy === "nonref" || p.retinopathy === true) ? SS.retino_nonref : 0))
      + SS_DEP[dq] + SS.female_hba1c * (p.female ? 1 : 0) * a1cMmol;
    let cum = 0; const yrs = years || 10;
    for (let t = 0; t < yrs; t++) {
      const ca = p.age + t;
      const lp = fixed + SS.age * ca + SS.age2 * ca * ca + SS.age3 * ca * ca * ca + SS.age_weight * ca * weight + SS.age_mean_hba1c * ca * meanA1c;
      cum += exp(lp);
    }
    return 100 * (1 - exp(-cum * SS_CAL));
  }

  // ----------------------------------------------------------------- model registry
  // category: T1D | T2D | general ; validated: true = reference/live-tool
  // implementation check, not external validation in a T1D outcomes cohort.
  const MODELS = {
    "Steno-CVD":        { category: "T1D", horizon: "10y", validated: true, fn: (p) => steno(p, 10, "cvd"), note: "Composite incl. heart failure & PAD. Web-validated to the decimal." },
    "Steno-IHD/stroke": { category: "T1D", horizon: "10y", validated: false, fn: (p) => steno(p, 10, "ihd_stroke"), note: "Secondary IHD-or-stroke endpoint from the Steno paper's secondary analysis; not exposed by the public web tool, coefficients not yet re-verified against the supplement." },
    "Scottish-Swedish": { category: "T1D", horizon: "10y", validated: true, fn: (p) => scottishSwedish(p, 10), note: "Final-model coefficients incl. age-at-entry; calibrated to the deployed tool (×1.32). Deprivation set to quintile 3." },
    "Cederholm (5y)":   { category: "T1D", horizon: "5y",  validated: true, fn: (p) => cederholm(p), note: "5-year horizon (not 10y) — not directly comparable; shown for completeness." },
    "SCORE2-Diabetes":  { category: "T2D", horizon: "10y", validated: true, fn: (p) => score2diabetes(p), note: "Derived in type-2 diabetes; not validated in T1D." },
    "SCORE2":           { category: "general", horizon: "10y", validated: true, fn: (p) => score2(p), note: "General population; SCORE2 has NO diabetes term (use SCORE2-Diabetes for that); valid age 40–69." },
    "QRISK3":           { category: "general", horizon: "10y", validated: true, fn: (p) => qrisk3(p), note: "Has a dedicated T1D term; UK-calibrated; valid age 25–84." },
    "PCE (ACC/AHA)":    { category: "general", horizon: "10y", validated: true, fn: (p) => pce(p), note: "Hard ASCVD; diabetes as binary (no T1D/T2D); valid age 40–79." },
    "AHA PREVENT":      { category: "general", horizon: "10y", validated: true, fn: (p) => prevent(p), note: "Total CVD incl. heart failure; valid age 30–79." },
    "Framingham":       { category: "general", horizon: "10y", validated: true, fn: (p) => framingham(p), note: "Broad CVD composite; valid age 30–74." },
    "UKPDS":            { category: "T2D", horizon: "10y", validated: true, fn: (p) => ukpds(p), note: "T2D engine; duration term extrapolates pathologically to long T1D durations — interpret with caution." },
    "ADVANCE*":         { category: "T2D", horizon: "10y*", validated: true, fn: (p) => advance(p, 10), note: "Native 4-year; 10-year is an extrapolation." },
  };

  // risk-category banding (NICE/Steno 10-yr CVD): low <10, moderate 10–20, high >=20
  function band(pct) { return pct < 10 ? 0 : (pct < 20 ? 1 : 2); }
  const BAND_LABEL = ["low (<10%)", "moderate (10–20%)", "high (≥20%)"];

  const API = { hba1cPctToMmol, hba1cMmolToPct, MODELS, band, BAND_LABEL,
    steno, score2diabetes, score2, pce, qrisk3, prevent, framingham, ukpds, ukpdsStroke, advance, cederholm, scottishSwedish };
  if (typeof module !== "undefined" && module.exports) module.exports = API;
  else root.T1DCVD = API;
})(typeof window !== "undefined" ? window : globalThis);
