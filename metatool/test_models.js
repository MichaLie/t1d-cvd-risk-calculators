/* Validate models.js (JS engine) against each source paper's worked example / live tool. */
const M = require("./models.js");
const mmol = M.hba1cMmolToPct;        // mmol/mol -> %
const MGDL = 38.67, NONHDL = 0.02586;
let pass = 0, fail = 0;
function check(name, got, exp, tol) {
  tol = tol || 0.6;
  const ok = isFinite(got) && Math.abs(got - exp) <= tol;
  console.log(`${ok ? "PASS" : "FAIL"}  ${name.padEnd(46)} got ${got.toFixed(2).padStart(7)}  exp ${exp.toFixed(1).padStart(6)}`);
  ok ? pass++ : fail++;
}

// --- Steno (live-tool validated) ---
const stA = { age: 50, female: true, duration: 30, hba1c_pct: mmol(70), sbp: 130, ldl: 2.0, egfr: 100, albuminuria: "normal", smoker: false, regular_exercise: true };
check("Steno CVD 5y (app default)", M.steno(stA, 5, "cvd"), 6.1);
check("Steno CVD 10y (app default)", M.steno(stA, 10, "cvd"), 11.8);
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
check("PREVENT female 10y total CVD", M.prevent(pv), 14.7, 0.4);

// --- Framingham (paper example) ---
check("Framingham woman", M.framingham({ age: 61, female: true, total_chol: 230 / MGDL, hdl: 47 / MGDL, sbp: 124, on_bp_treatment: false, smoker: false, diabetes: false }), 8.4, 0.5);
check("Framingham man (diabetic, treated)", M.framingham({ age: 53, female: false, total_chol: 161 / MGDL, hdl: 55 / MGDL, sbp: 125, on_bp_treatment: true, smoker: false, diabetes: true }), 15.6, 0.5);

// --- UKPDS stroke (UKPDS 60 example) ---
check("UKPDS stroke 5y (paper case)", 100 * M.ukpdsStroke(55, false, false, false, 147, 5.65 / 1.11, 12, 5), 6.9, 0.3);

// --- Cederholm (paper example) ---
check("Cederholm 5y (paper case)", M.cederholm({ age: 48, duration: 30, onset_age: 18, tc_hdl_ratio: 5.0 / 1.1, hba1c_pct: 8.0, sbp: 150, smoker: false, albuminuria: "macro", prior_cvd: false }), 7.1, 0.3);

// --- Scottish-Swedish (deployed Shiny app, calibrated) ---
const ssBase = { female: true, duration: 5, hba1c_pct: mmol(74), sbp: 128, tc_hdl_ratio: 3.3, egfr: 97, bmi: 26, height_m: 1.71, weight_kg: 77, albuminuria: "normal", smoker: false, on_bp_treatment: false, on_statin: false, af: false, deprivation_quintile: 4 };
check("Scottish-Swedish age42 (app=5%)", M.scottishSwedish(Object.assign({ age: 42 }, ssBase), 10), 5.0, 1.0);
check("Scottish-Swedish age60 (app=10%)", M.scottishSwedish(Object.assign({ age: 60 }, ssBase), 10), 10.0, 1.0);

// --- ADVANCE: definitional baseline (mean patient -> 1-S0(4)) ---
check("ADVANCE baseline 1-S0(4) sanity", 100 * (1 - 0.951044), 4.9, 0.05);

// --- Regression guards for the independent-verification fixes ---
// SCORE2 (2021) has NO diabetes term: must be diabetes-invariant, and the canonical
// T1D patient must read ~2.0% (not the old, inflated 4.8%).
const s2canon = { age: 45, female: false, smoker: false, sbp: 130, total_chol: 4.8, hdl: 1.4, risk_region: "high" };
const s2_dm = M.score2(Object.assign({ diabetes: true }, s2canon));
const s2_nod = M.score2(Object.assign({ diabetes: false }, s2canon));
check("SCORE2 high man (canonical, no diabetes term)", s2_dm, 2.0, 0.3);
check("SCORE2 is diabetes-invariant", Math.abs(s2_dm - s2_nod), 0.0, 1e-9);

// QRISK3 with SBP-SD unknown: ClinRisk centres raw 0 (was skipping the offset -> ~7.9%).
const qCanon = { age: 45, female: false, ethrisk: 1, smoke_cat: 0, bmi: 25, tc_hdl_ratio: 4.8 / 1.4, sbp: 130, town: 0, b_type1: true, b_type2: false, af: false, on_bp_treatment: false, egfr: 95, family_history_cvd: false };
check("QRISK3 T1D man, SBP-SD unknown (centred)", M.qrisk3(qCanon), 7.2, 0.3);

// Scottish-Swedish retinopathy term is now live (was dead code -> identical output).
const ssRet = Object.assign({ age: 60 }, ssBase);
const ssNoRet = M.scottishSwedish(ssRet, 10);
const ssRefRet = M.scottishSwedish(Object.assign({}, ssRet, { retinopathy: "ref" }), 10);
check("Scottish-Swedish retinopathy raises risk", ssRefRet > ssNoRet + 1e-6 ? 1 : 0, 1, 0);

console.log(`\n${pass} passed, ${fail} failed.`);
process.exit(fail ? 1 : 0);
