/* SPDX-License-Identifier: LGPL-3.0-or-later
 * Derived from QRISK3-2017, Copyright 2017 ClinRisk Ltd.
 * Modified 2026: JavaScript port with a restricted comparison-tool adapter,
 * missing-input defaults and continuous-age evaluation.
 * See ../third_party/qrisk3/NOTICE.md and qrisk3-notice.html.
 */
(function(root){
"use strict";
const exp=Math.exp, log=Math.log;
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
    if (p.age < 25 || p.age >= 85) return NaN;
    const sex = p.female ? "female" : "male", m = Q.main[sex], c = Q.center[sex];
    let age1 = p.female ? Math.pow(p.age / 10, -2) : Math.pow(p.age / 10, -1);
    let age2 = p.female ? (p.age / 10) : Math.pow(p.age / 10, 3);
    let bmi1 = Math.pow(p.bmi / 10, -2), bmi2 = Math.pow(p.bmi / 10, -2) * log(p.bmi / 10);
    age1 -= c.age1; age2 -= c.age2; bmi1 -= c.bmi1; bmi2 -= c.bmi2;
    const rati_c = p.tc_hdl_ratio - c.rati, sbp_c = p.sbp - c.sbp, town_c = (p.town || 0) - c.town;
    const sbps5_c = ((p.sbps5 != null) ? p.sbps5 : 0) - c.sbps5; // SD of SBP; adapter assumption: missing SD -> raw 0, then centre
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


if(typeof module!=="undefined" && module.exports) module.exports=qrisk3;
else root.QRISK3=qrisk3;
})(typeof window!=="undefined"?window:globalThis);
