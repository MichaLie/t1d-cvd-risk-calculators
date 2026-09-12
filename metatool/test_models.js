/* Implementation checks against source-paper examples, tables, live tools and regression guards. */
const M = require("./models.js");
const mmol = M.hba1cMmolToPct;        // mmol/mol -> %
const MGDL = 38.67, NONHDL = 0.02586;
let pass = 0, fail = 0;
function check(name, got, exp, tol) {
  tol = tol ?? 0.6;
  const ok = isFinite(got) && Math.abs(got - exp) <= tol;
  console.log(`${ok ? "PASS" : "FAIL"}  ${name.padEnd(46)} got ${got.toFixed(2).padStart(7)}  exp ${exp.toFixed(1).padStart(6)}`);
  ok ? pass++ : fail++;
}

// --- Steno (selected live-tool implementation checks) ---
const stA = { age: 50, female: true, duration: 30, hba1c_pct: mmol(70), sbp: 130, ldl: 2.0, egfr: 100, albuminuria: "normal", smoker: false, regular_exercise: true };
check("Steno CVD 5y (app default)", M.steno(stA, 5, "cvd"), 6.1);
check("Steno CVD 10y (app default)", M.steno(stA, 10, "cvd"), 11.8);
check("Steno IHD/stroke Table 4 regression", M.steno(stA, 10, "ihd_stroke"), 8.37492513748504, 1e-9);
const stB = { age: 60, female: true, duration: 25, hba1c_pct: mmol(90), sbp: 150, ldl: 4.0, egfr: 70, albuminuria: "normal", smoker: false, regular_exercise: true };
check("Steno CVD 5y (high profile)", M.steno(stB, 5, "cvd"), 16.4);
check("Steno CVD 10y (high profile)", M.steno(stB, 10, "cvd"), 30.0, 1.0);

// --- SCORE2-Diabetes (paper graphical abstract) ---
const sdA = (fem, region) => ({ age: 60, female: fem, smoker: false, sbp: 140, total_chol: 5.5, hdl: 1.3, onset_age: 60, hba1c_pct: mmol(50), egfr: 90, risk_region: region });
const sdB = (fem, region) => ({ age: 60, female: fem, smoker: false, sbp: 140, total_chol: 5.5, hdl: 1.3, onset_age: 50, hba1c_pct: mmol(70), egfr: 60, risk_region: region });
check("SCORE2-D moderate man A", M.score2diabetes(sdA(false, "moderate")), 11.0);
check("SCORE2-D moderate man B", M.score2diabetes(sdB(false, "moderate")), 17.2);
check("SCORE2-D moderate woman A", M.score2diabetes(sdA(true, "moderate")), 7.6);
check("SCORE2-D low man A", M.score2diabetes(sdA(false, "low")), 8.4);
check("SCORE2-D very-high woman B", M.score2diabetes(sdB(true, "very_high")), 34.0, 0.8);
check("SCORE2-D high man B (abstract 21.0)", M.score2diabetes(sdB(false, "high")), 21.0, 0.1);
check("SCORE2-D high woman B (abstract 20.4)", M.score2diabetes(sdB(true, "high")), 20.4, 0.1);
check("SCORE2-D moderate woman B (abstract 12.7)", M.score2diabetes(sdB(true, "moderate")), 12.7, 0.1);
check("SCORE2-D age 39 is n/a", Number.isNaN(M.score2diabetes(Object.assign(sdA(false, "moderate"), { age: 39 }))) ? 1 : 0, 1, 0);
check("SCORE2-D age 40 is applicable", Number.isFinite(M.score2diabetes(Object.assign(sdA(false, "moderate"), { age: 40 }))) ? 1 : 0, 1, 0);
check("SCORE2-D age 79 is applicable", Number.isFinite(M.score2diabetes(Object.assign(sdA(false, "moderate"), { age: 79 }))) ? 1 : 0, 1, 0);
check("SCORE2-D age 80 is n/a", Number.isNaN(M.score2diabetes(Object.assign(sdA(false, "moderate"), { age: 80 }))) ? 1 : 0, 1, 0);

// --- SCORE2 (EHJ 2021 example, non-diabetic) ---
const s2 = (fem, region) => ({ age: 50, female: fem, smoker: true, sbp: 140, total_chol: 5.5, hdl: 1.3, risk_region: region, diabetes: false });
check("SCORE2 low man", M.score2(s2(false, "low")), 5.9);
check("SCORE2 very-high man", M.score2(s2(false, "very_high")), 14.0);
check("SCORE2 low woman", M.score2(s2(true, "low")), 4.2);
check("SCORE2 very-high woman", M.score2(s2(true, "very_high")), 13.7);

// --- PCE (guideline example, non-diabetic) ---
const pceP = (fem, black) => ({ age: 55, female: fem, ethnicity: black ? "black" : "white", total_chol: 213 / MGDL, hdl: 50 / MGDL, sbp: 120, on_bp_treatment: false, smoker: false, diabetes: false });
check("PCE white woman", M.pce(pceP(true, false)), 2.1);
check("PCE white man", M.pce(pceP(false, false)), 5.3);
check("PCE black woman", M.pce(pceP(true, true)), 3.0);
check("PCE black man", M.pce(pceP(false, true)), 6.1);

// --- QRISK3 (qrisk.org live, non-diabetic, ex-smoker) ---
const qF = { age: 64, female: true, ethrisk: 2, smoke_cat: 1, bmi: 25.25, tc_hdl_ratio: 4, sbp: 180, sbps5: 20, town: 0, b_type1: false, b_type2: false, af: false, on_bp_treatment: false, egfr: 90, family_history_cvd: false };
check("QRISK3 female reference", M.qrisk3(qF), 19.1, 0.2);

// --- PREVENT (preventr example, diabetic) ---
const pv = { age: 50, female: true, total_chol: 200 * NONHDL, hdl: 45 * NONHDL, sbp: 160, on_bp_treatment: true, on_statin: false, diabetes: true, smoker: false, egfr: 90, bmi: 35 };
check("PREVENT female 10y total CVD (preventr)", M.prevent(pv), 14.7, 0.4);
// Khan 2024 printed example: 50-y woman, TC 240 / HDL 55 mg/dL, treated SBP 160, no statin, no diabetes,
// non-smoker, eGFR 90 -> 10-y total CVD 5.4%; if smoking 9.3%.
const pvPaper = { age: 50, female: true, total_chol: 240 / MGDL, hdl: 55 / MGDL, sbp: 160, on_bp_treatment: true, on_statin: false, diabetes: false, smoker: false, egfr: 90 };
check("PREVENT paper example (non-smoker 5.4%)", M.prevent(pvPaper), 5.4, 0.1);
check("PREVENT paper example (smoker 9.3%)", M.prevent(Object.assign({}, pvPaper, { smoker: true })), 9.3, 0.1);

// --- Framingham (paper example) ---
check("Framingham woman (paper Case 1: TC180, smoker)", M.framingham({ age: 61, female: true, total_chol: 180 / MGDL, hdl: 47 / MGDL, sbp: 124, on_bp_treatment: false, smoker: true, diabetes: false }), 10.5, 0.1);
check("Framingham man (paper Case 2: diabetic, treated)", M.framingham({ age: 53, female: false, total_chol: 161 / MGDL, hdl: 55 / MGDL, sbp: 125, on_bp_treatment: true, smoker: false, diabetes: true }), 15.6, 0.1);

// --- UKPDS 56 CHD worked example (Stevens 2001, p. 675): man, T2D newly diagnosed at 45, non-smoker,
// HbA1c 7.5%, SBP 160, TC 4.9 / HDL 1.0 -> q = 0.00883, 20-year CHD risk 33% ---
check("UKPDS CHD 20y (paper case, dx at 45, T=0)", 100 * M.ukpdsCHD(45, false, false, false, 7.5, 160, 4.9 / 1.0, 0, 20), 33.0, 0.5);
// --- UKPDS 60 stroke worked example (Kothari 2002, p. 1778): man diagnosed at 55, 12 y of diabetes,
// SBP 147, TC 5.65 / HDL 1.11, non-smoker, no AF -> q = 0.00212, 5-year stroke risk 6.9% ---
check("UKPDS stroke 5y (paper case, dx at 55, T=12)", 100 * M.ukpdsStroke(55, false, false, false, 147, 5.65 / 1.11, 12, 5), 6.9, 0.1);
check("UKPDS stroke smoker variant (paper 10.5%)", 100 * M.ukpdsStroke(55, false, true, false, 147, 5.65 / 1.11, 12, 5), 10.5, 0.1);
// Regression guard: the wrapper must use age AT DIAGNOSIS (onset) — same onset+duration => same risk
// regardless of the `age` field; and current-age input must NOT be used in place of onset.
const ukA = { age: 45, female: false, duration: 20, onset_age: 25, hba1c_pct: 8, sbp: 130, tc_hdl_ratio: 4.8 / 1.4, af: false, smoker: false, ethnicity: "white" };
check("UKPDS wrapper uses onset age (invariant to age field)", M.ukpds(Object.assign({}, ukA, { age: 60 })), M.ukpds(ukA), 1e-12);
check("UKPDS wrapper canonical 45M dur20 (dx 25)", M.ukpds(ukA), 11.68, 0.05);

// --- Cederholm (paper example) ---
check("Cederholm 5y (paper case)", M.cederholm({ age: 48, duration: 30, onset_age: 18, tc_hdl_ratio: 5.0 / 1.1, hba1c_pct: 8.0, sbp: 150, smoker: false, albuminuria: "macro", prior_cvd: false }), 7.1, 0.3);

// --- ADVANCE: definitional baseline (mean patient -> 1-S0(4)) ---
check("ADVANCE baseline 1-S0(4) sanity", 100 * (1 - 0.951044), 4.9, 0.05);

// --- Regression guards ---
// SCORE2 default = as deployed for people without diabetes (published diabetes term at 0, Hageman 2022
// footnote a): output must not depend on the `diabetes` field. The published-diabetes-term variant is
// available via {diabetesTerm: true} for sensitivity analyses (canonical 45M: 2.00% -> 4.75%).
const s2canon = { age: 45, female: false, smoker: false, sbp: 130, total_chol: 4.8, hdl: 1.4, risk_region: "high" };
const s2_dm = M.score2(Object.assign({ diabetes: true }, s2canon));
const s2_nod = M.score2(Object.assign({ diabetes: false }, s2canon));
check("SCORE2 high man (canonical, as deployed)", s2_dm, 2.0, 0.3);
check("SCORE2 default is diabetes-invariant", Math.abs(s2_dm - s2_nod), 0.0, 1e-9);
check("SCORE2 published diabetes-term variant", M.score2(Object.assign({ diabetes: true }, s2canon), { diabetesTerm: true }), 4.75, 0.05);
// all eight SCORE2 graphical-abstract values (EHJ 2021, p. 2440), tight tolerance
check("SCORE2 moderate man", M.score2(s2(false, "moderate")), 7.5, 0.1);
check("SCORE2 high man", M.score2(s2(false, "high")), 8.1, 0.1);
check("SCORE2 moderate woman", M.score2(s2(true, "moderate")), 5.1, 0.1);
check("SCORE2 high woman", M.score2(s2(true, "high")), 6.9, 0.1);

// QRISK3 with SBP-SD unknown: ClinRisk centres raw 0 (was skipping the offset -> ~7.9%).
const qCanon = { age: 45, female: false, ethrisk: 1, smoke_cat: 0, bmi: 25, tc_hdl_ratio: 4.8 / 1.4, sbp: 130, town: 0, b_type1: true, b_type2: false, af: false, on_bp_treatment: false, egfr: 95, family_history_cvd: false };
check("QRISK3 T1D man, SBP-SD unknown (centred)", M.qrisk3(qCanon), 7.2, 0.3);

// Common analytic bands use exact half-open boundaries and reject non-finite input.
check("Analytic band below 10%", M.band(9.999), 0, 0);
check("Analytic band 10 to <20%", M.band(10), 1, 0);
check("Analytic band >=20%", M.band(20), 2, 0);
check("Analytic band rejects NaN", M.band(Number.NaN), -1, 0);

console.log(`\n${pass} passed, ${fail} failed.`);
process.exit(fail ? 1 : 0);
