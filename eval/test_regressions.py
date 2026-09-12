"""Regression tests for input boundaries, equations and agreement statistics (stdlib unittest)."""
import math
import unittest
import numpy as np
from eval.harness.patient import Patient
from eval.harness.models import REGISTRY
from eval.harness.discordance import cohen_kappa
from eval.model_assertions import assert_close
from eval.models.ukpds import ukpds_chd, ukpds_stroke
from eval.models.score2_diabetes import score2_diabetes_risk

class RegressionTests(unittest.TestCase):
    def test_fractional_age_boundaries(self):
        for name, lo, stop in [('SCORE2',40,70),('SCORE2-Diabetes',40,80),('PCE',40,80),('PREVENT',30,80),('QRISK3',25,85),('Framingham',30,75)]:
            with self.subTest(model=name):
                f=lambda age: REGISTRY[name][2](Patient(age=age,female=False,duration=10))
                self.assertTrue(math.isnan(f(lo-.001)))
                self.assertTrue(math.isfinite(f(lo)))
                self.assertTrue(math.isfinite(f(stop-.001)))
                self.assertTrue(math.isnan(f(stop)))

    def test_ukpds_paper_examples(self):
        # UKPDS 56 p674 example: newly diagnosed White man, 45, HbA1c 7.5%, SBP160, ratio4.9.
        got=ukpds_chd(age_at_diagnosis=45,female=False,smoker=False,hba1c_pct=7.5,sbp=160,tc_hdl=4.9,duration=0,t=20)
        self.assertAlmostEqual(got,33,delta=.5)
        for smoke,expected in [(False,6.9),(True,10.5)]:
            got=ukpds_stroke(age_at_diagnosis=55,female=False,smoker=smoke,af=False,sbp=147,tc_hdl=5.65/1.11,duration=12,t=5)
            self.assertAlmostEqual(got,expected,delta=.05)

    def test_kappa_hand_calculated(self):
        # O has diagonal 1/3; E diagonal 1/3; off-diagonal observed distance 2/3,
        # expected distance 8/9 => linear kappa = 1/4.
        self.assertAlmostEqual(cohen_kappa([0,1,2],[0,2,1],'linear',3),.25)
        self.assertAlmostEqual(cohen_kappa([0,1,2],[0,2,1],None,3),0)
        self.assertTrue(math.isnan(cohen_kappa([2,2],[2,2],'linear',3)))
        self.assertTrue(math.isnan(cohen_kappa([],[])))
        for a,b,w in [([0],[0,1],None),([-1],[0],None),([.5],[0],None),([0],[0],'typo')]:
            with self.assertRaises(ValueError):cohen_kappa(a,b,w)

    def test_reference_assertion_rejects_nan(self):
        with self.assertRaises(AssertionError):assert_close('NaN',float('nan'),1,.1)

    def test_score2_extreme_finite_input(self):
        # Previously the rounded uncalibrated probability reached one and log(0) raised.
        got=score2_diabetes_risk(female=True,age=40,smoker=True,sbp=260,total_chol=20,hdl=.2,age_at_diagnosis=0,hba1c_mmol=195,egfr=2,region='very_high')
        self.assertTrue(math.isfinite(got))
        self.assertTrue(0<=got<=100)

if __name__=='__main__':unittest.main()
