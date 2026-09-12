/*
 * Cross-implementation parity check: runs the JavaScript engine (models.js) on the
 * seeded synthetic cohort exported by the Python pipeline (eval/out/synthetic_cohort.csv)
 * using the SAME adapter choices as eval/harness/models.py, and compares every
 * 10-year endpoint against eval/out/cohort_risks.csv (the values the manuscript uses).
 *
 * Purpose: check whether the browser tool and the published analysis are the same
 * model, not two ports that drifted apart.
 *
 *   node metatool/parity_check.js            # from the repository root
 *
 * Exit code 0 when every finite value agrees to within TOL percentage points and
 * the NaN (out-of-age-range) pattern is identical; 1 otherwise.
 */
const fs = require("fs");
const path = require("path");
const M = require("./models.js");

const ROOT = path.resolve(__dirname, "..");
const COHORT = path.join(ROOT, "eval", "out", "synthetic_cohort.csv");
const RISKS = path.join(ROOT, "eval", "out", "cohort_risks.csv");
const TOL = 1e-6; // percentage points; JS vs Python float arithmetic differs at ~1e-12

function readCsv(file) {
  const lines = fs.readFileSync(file, "utf8").trim().split(/\r?\n/);
  const header = lines[0].split(",");
  if(lines.length<2 || new Set(header).size!==header.length) throw Error("Empty or duplicate-header CSV: "+file);
  return lines.slice(1).map((l) => {
    const cells = l.split(",");
    const row = {};
    header.forEach((h, i) => (row[h] = cells[i]));
    return row;
  });
}

// Python registry name -> JS registry name
const NAME_MAP = {
  "Steno-CVD": "Steno-CVD",
  "Steno-IHDstroke": "Steno-IHD/stroke",
  "SCORE2-Diabetes": "SCORE2-Diabetes",
  "SCORE2": "SCORE2",
  "PCE": "PCE (ACC/AHA)",
  "QRISK3": "QRISK3",
  "PREVENT": "AHA PREVENT",
  "UKPDS-CVD": "UKPDS",
  "Framingham": "Framingham",
  "ADVANCE*": "ADVANCE*",
};
const ETHRISK = { white: 1, south_asian: 2, black: 7, other: 9 };

// Same field mapping as eval/harness/models.py adapters (and index.html patient()).
function toPatient(r) {
  const tc = +r.total_cholesterol_mmol_l, hdl = +r.hdl_cholesterol_mmol_l;
  return {
    age: +r.age_years, female: r.female === "1", ethnicity: r.ethnicity,
    duration: +r.diabetes_duration_years, onset_age: +r.age_at_diagnosis_years,
    hba1c_pct: +r.hba1c_percent, sbp: +r.sbp_mmhg, dbp: +r.dbp_mmhg,
    total_chol: tc, hdl: hdl, ldl: +r.ldl_cholesterol_mmol_l, tc_hdl_ratio: tc / hdl,
    egfr: +r.egfr_ml_min_1_73m2, albuminuria: r.albuminuria, bmi: +r.bmi_kg_m2,
    smoker: r.current_smoker === "1", regular_exercise: r.regular_exercise === "1",
    on_bp_treatment: r.bp_treatment === "1", on_statin: r.statin_treatment === "1",
    af: r.atrial_fibrillation === "1", retinopathy: r.retinopathy === "1",
    prior_cvd: r.prior_cvd === "1", family_history_cvd: r.family_history_cvd === "1",
    risk_region: r.score2_risk_region, diabetes: true, ethrisk: ETHRISK[r.ethnicity] || 1,
  };
}

const cohort = readCsv(COHORT);
const risks = readCsv(RISKS);
if (cohort.length !== 10000 || cohort.length !== risks.length) {
  console.error(`row count mismatch: cohort ${cohort.length} vs risks ${risks.length}`);
  process.exit(1);
}

const stats = {};
let failures = 0;
for (const py of Object.keys(NAME_MAP)) stats[py] = { n: 0, maxAbs: 0, nanMismatch: 0 };

cohort.forEach((row, i) => {
  const p = toPatient(row);
  const ref = risks[i];
  if (ref.synthetic_id !== row.synthetic_id) { console.error("id misalignment at row", i); process.exit(1); }
  for (const [py, js] of Object.entries(NAME_MAP)) {
    const got = M.MODELS[js].fn(p);
    if(!Object.hasOwn(ref,py)) throw Error("Missing expected endpoint column: "+py);
    const expRaw = ref[py];
    const exp = expRaw === "" ? NaN : +expRaw;
    const s = stats[py];
    if (Number.isNaN(exp) || !Number.isFinite(got)) {
      if (Number.isNaN(exp) !== !Number.isFinite(got)) { s.nanMismatch++; failures++; }
      continue;
    }
    s.n++;
    const d = Math.abs(got - exp);
    if (d > s.maxAbs) s.maxAbs = d;
    if (d > TOL) failures++;
  }
});

console.log(`parity check: ${cohort.length} synthetic profiles x ${Object.keys(NAME_MAP).length} endpoints (tolerance ${TOL} pp)\n`);
console.log(`${"endpoint (python -> js)".padEnd(38)} ${"n finite".padStart(9)} ${"max |diff| pp".padStart(14)} ${"NaN mismatch".padStart(13)}`);
for (const [py, js] of Object.entries(NAME_MAP)) {
  const s = stats[py];
  console.log(`${(py + " -> " + js).padEnd(38)} ${String(s.n).padStart(9)} ${s.maxAbs.toExponential(2).padStart(14)} ${String(s.nanMismatch).padStart(13)}`);
}
console.log(`\n${failures === 0 ? "PARITY OK" : "PARITY FAILED"}: ${failures} discrepancies`);
process.exit(failures ? 1 : 0);
