#!/usr/bin/env python3
"""
test_validation.py — Unit tests for Phase 2.7 validation scripts.

Tests core computation functions from:
  - tools/validate_flat_plate.py
  - tools/validate_bfs.py

Run: python3 -m pytest test/unit/test_validation.py -v
"""

import sys
import os
import numpy as np

# Add tools/ to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'tools'))

# Import from flat plate validation script
import validate_flat_plate as vfp

# Import from BFS validation script
import validate_bfs as vbfs


# ═══════════════════════════════════════════════════════════════════════════════
#  Cf empirical formula tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCfEmpirical:
    """Tests for compute_cf_empirical()"""

    def test_cf_at_re1e6(self):
        """Cf at Re_x = 1e6 = 0.027/(1e6)^(1/7) ≈ 0.00375"""
        cf = vfp.compute_cf_empirical(1.0e6)
        expected = 0.027 / (1.0e6 ** (1.0 / 7.0))
        assert abs(cf - expected) < 1e-12, f"Cf={cf:.10f}, expected {expected:.10f}"

    def test_cf_decreases_with_re(self):
        """Cf should decrease with increasing Re_x"""
        cf1 = vfp.compute_cf_empirical(1.0e5)
        cf2 = vfp.compute_cf_empirical(1.0e6)
        cf3 = vfp.compute_cf_empirical(1.0e7)
        assert cf1 > cf2 > cf3, f"Cf should decrease: {cf1:.6f} > {cf2:.6f} > {cf3:.6f}"

    def test_cf_1_7_power_law(self):
        """Cf should follow 0.027 / Re_x^(1/7)"""
        re_x = np.array([1e5, 1e6, 1e7])
        cf = vfp.compute_cf_empirical(re_x)
        expected = 0.027 / (re_x ** (1.0 / 7.0))
        np.testing.assert_allclose(cf, expected, rtol=1e-12)

    def test_cf_clips_low_re(self):
        """Small Re_x should be clipped to avoid singularity"""
        cf = vfp.compute_cf_empirical(100.0)
        assert np.isfinite(cf) and cf > 0

    def test_cf_array_input(self):
        """Should work with numpy arrays"""
        re_x = np.array([1e5, 1e6, 1e7])
        cf = vfp.compute_cf_empirical(re_x)
        assert cf.shape == (3,)
        assert np.all(np.isfinite(cf))


# ═══════════════════════════════════════════════════════════════════════════════
#  Helper computation tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHelpers:
    """Tests for Re_x, y+, u+, Cf_from_tau computations"""

    def test_re_x(self):
        """Re_x = U * x / nu"""
        re_x = vfp.compute_re_x(1.5, 10.0, 1.5e-5)
        expected = 1.0e6
        assert abs(re_x - expected) / expected < 0.01

    def test_re_x_array(self):
        """Re_x should work element-wise on arrays"""
        x = np.array([0.5, 1.0, 1.5])
        re_x = vfp.compute_re_x(x, 10.0, 1.5e-5)
        assert re_x.shape == (3,)
        assert np.all(re_x > 0)

    def test_y_plus(self):
        """y+ = y * u_tau / nu"""
        yp = vfp.compute_y_plus(0.01, 0.1, 1.5e-5)
        expected = 0.01 * 0.1 / 1.5e-5  # ~66.7
        assert abs(yp - expected) / expected < 0.01

    def test_u_plus(self):
        """u+ = u_par / u_tau"""
        up = vfp.compute_u_plus(2.0, 0.1)
        assert abs(up - 20.0) < 0.01

    def test_u_plus_zero_u_tau(self):
        """u+ should handle u_tau=0 gracefully"""
        up = vfp.compute_u_plus(2.0, 0.0)
        assert np.isfinite(up)  # Should not divide by zero

    def test_cf_from_tau(self):
        """Cf = tau_w / (0.5 * rho * U^2)"""
        cf = vfp.compute_cf_from_tau(0.012, 1.225, 10.0)
        denom = 0.5 * 1.225 * 100.0
        expected = 0.012 / denom
        assert abs(cf - expected) < 1e-10

    def test_cf_bfs(self):
        """BFS Cf computation matches expected formula"""
        cf = vbfs.compute_cf(0.5, 1.225, 44.2)
        denom = 0.5 * 1.225 * 44.2 * 44.2
        expected = 0.5 / denom
        assert abs(cf - expected) < 1e-12

    def test_cp_bfs(self):
        """BFS Cp computation"""
        cp = vbfs.compute_cp(101400, 101325, 1.225, 44.2)
        denom = 0.5 * 1.225 * 44.2 * 44.2
        expected = 75.0 / denom
        assert abs(cp - expected) < 1e-12


# ═══════════════════════════════════════════════════════════════════════════════
#  Log-law regression tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestLogLawRegression:
    """Tests for log_law_regression()"""

    KAPPA = 0.41
    B = 5.0

    def test_perfect_log_law(self):
        """Regression on noise-free log-law data should recover kappa and B"""
        y_plus = np.logspace(np.log10(30), np.log10(300), 50)
        u_plus_true = np.log(y_plus) / self.KAPPA + self.B

        reg = vfp.log_law_regression(y_plus, u_plus_true)

        assert abs(reg['kappa'] - self.KAPPA) < 0.005, \
            f"kappa={reg['kappa']:.4f}, expected {self.KAPPA}"
        assert abs(reg['intercept'] - self.B) < 0.1, \
            f"B={reg['intercept']:.3f}, expected {self.B}"
        assert reg['r_squared'] > 0.999, f"R²={reg['r_squared']:.4f}"

    def test_noisy_log_law(self):
        """Regression with noise should give reasonable results"""
        np.random.seed(123)
        y_plus = np.logspace(np.log10(30), np.log10(300), 60)
        u_plus_true = np.log(y_plus) / self.KAPPA + self.B
        u_plus_noisy = u_plus_true + np.random.normal(0, 0.3, len(y_plus))

        reg = vfp.log_law_regression(y_plus, u_plus_noisy)

        assert abs(reg['kappa'] - self.KAPPA) < 0.05, \
            f"kappa={reg['kappa']:.4f} too far from {self.KAPPA}"
        assert abs(reg['intercept'] - self.B) < 0.5
        assert reg['r_squared'] > 0.9

    def test_insufficient_points(self):
        """Less than 5 points in log region should return error"""
        y_plus = np.array([30.0, 35.0, 40.0, 45.0])
        u_plus = np.array([15.0, 16.0, 17.0, 18.0])

        reg = vfp.log_law_regression(y_plus, u_plus)

        assert np.isnan(reg['kappa'])
        assert 'error' in reg
        assert reg['n_points'] < 5

    def test_filter_yplus_range(self):
        """Only points in [yplus_min, yplus_max] should be used"""
        np.random.seed(42)
        y_plus = np.concatenate([
            np.logspace(0, 1.4, 20),     # y+ < 30
            np.logspace(1.5, 2.5, 40),   # 30 < y+ < 300
            np.logspace(2.6, 3.5, 20),   # y+ > 300
        ])
        u_plus = np.log(y_plus) / self.KAPPA + self.B + np.random.normal(0, 0.2, len(y_plus))

        reg = vfp.log_law_regression(y_plus, u_plus)

        # Should use ~40 points (the middle group)
        assert reg['n_points'] >= 30
        assert reg['n_points'] <= 50
        assert abs(reg['kappa'] - self.KAPPA) < 0.05

    def test_slope_and_intercept_relationship(self):
        """slope = 1/kappa, intercept = B"""
        y_plus = np.logspace(2, 2.5, 30)
        u_plus = np.log(y_plus) / self.KAPPA + self.B

        reg = vfp.log_law_regression(y_plus, u_plus)

        assert abs(reg['slope'] * reg['kappa'] - 1.0) < 0.01


# ═══════════════════════════════════════════════════════════════════════════════
#  Reattachment length tests (BFS)
# ═══════════════════════════════════════════════════════════════════════════════

class TestReattachment:
    """Tests for find_reattachment()"""

    def test_simple_zero_crossing(self):
        """Linear Cf crossing zero at x=0.3"""
        x = np.linspace(0, 1.0, 100)
        cf = (x - 0.3) * 0.01
        xr, xrh = vbfs.find_reattachment(x, cf)
        assert abs(xrh - 0.3 / vbfs.H) < 0.001, f"X_R/H={xrh:.3f}"
        assert xr > 0

    def test_no_crossing(self):
        """Cf that never crosses zero should return NaN"""
        x = np.linspace(0, 1.0, 100)
        cf = np.ones_like(x) * 0.001  # always positive
        xr, xrh = vbfs.find_reattachment(x, cf)
        assert np.isnan(xr)
        assert np.isnan(xrh)

    def test_with_nans(self):
        """Should handle NaN values in Cf array"""
        x = np.linspace(0, 1.0, 100)
        cf = (x - 0.3) * 0.01
        cf[20:30] = np.nan  # insert NaNs
        xr, xrh = vbfs.find_reattachment(x, cf)
        assert not np.isnan(xr), "Should find crossing despite NaNs"

    def test_multiple_crossings(self):
        """First negative→positive zero-crossing of sin(10x) is at 2π/10≈0.628"""
        x = np.linspace(0, 1.0, 100)
        cf = np.sin(x * 10) * 0.01  # multiple crossings
        xr, xrh = vbfs.find_reattachment(x, cf)
        assert xr > 0.5 and xr < 0.7, f"First neg→pos crossing at ~0.628, got {xr:.4f}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Recirculation zone tests (BFS)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecirculationZone:
    """Tests for find_recirculation_zone()"""

    def test_simple_recirculation(self):
        """Simple negative Cf region from 0 to 0.3m (7.87H)"""
        x = np.linspace(-0.1, 1.0, 100)
        cf = np.where(x < 0.3, -0.001, 0.001)
        s, e, l, sh, eh, lh = vbfs.find_recirculation_zone(x, cf)
        assert abs(sh) < 0.1, f"Start near step (x/H~0), got {sh:.2f}"
        assert eh > 7.0 and eh < 8.5, f"End ~0.3m={0.3/vbfs.H:.2f}H, got {eh:.2f}"
        assert lh > 0

    def test_no_recirculation(self):
        """No negative Cf should return NaN"""
        x = np.linspace(0, 1.0, 100)
        cf = np.ones_like(x) * 0.001
        s, e, l, sh, eh, lh = vbfs.find_recirculation_zone(x, cf)
        assert np.isnan(lh)

    def test_length_is_positive(self):
        """Recirculation zone length should be positive"""
        x = np.linspace(-0.1, 1.0, 100)
        cf = np.where((x > 0.05) & (x < 0.35), -0.001, 0.001)
        _, _, l, _, _, lh = vbfs.find_recirculation_zone(x, cf)
        assert lh > 0, f"Length should be positive, got {lh:.2f}H"


# ═══════════════════════════════════════════════════════════════════════════════
#  Verdict determination tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestVerdictFlatPlate:
    """Tests for determine_verdict() in validate_flat_plate"""

    def test_pass(self):
        """All metrics within tolerance → PASS"""
        v, n = vfp.determine_verdict(0.05, 0.03, 0.2, 0.95)
        assert v == 'PASS'

    def test_pass_with_notes(self):
        """One metric out of tolerance → PASS WITH NOTES (Cf 16% > 15%)"""
        v, n = vfp.determine_verdict(0.16, 0.05, 0.3, 0.95)
        assert v == 'PASS WITH NOTES'

    def test_fail(self):
        """Multiple metrics out → FAIL"""
        v, n = vfp.determine_verdict(0.30, 0.20, 2.5, 0.5)
        assert v == 'FAIL'

    def test_fail_single_critical(self):
        """Two failures (Cf 20% + R²=0.5) → FAIL"""
        v, n = vfp.determine_verdict(0.20, 0.05, 0.3, 0.5)
        assert 'FAIL' in v

    def test_nan_handling(self):
        """NaN values should be handled gracefully"""
        v, n = vfp.determine_verdict(np.nan, np.nan, np.nan, np.nan)
        assert v in ('PASS', 'PASS WITH NOTES', 'FAIL')

    def test_notes_returned(self):
        """Notes list should always be returned"""
        _, n = vfp.determine_verdict(0.05, 0.03, 0.2, 0.95)
        assert isinstance(n, list)
        assert len(n) > 0


class TestVerdictBFS:
    """Tests for determine_verdict_bfs()"""

    def test_perfect_pass(self):
        """All metrics perfect → PASS"""
        v, n = vbfs.determine_verdict_bfs(6.26, 5.0, True)
        assert v == 'PASS'

    def test_marginal_reattachment(self):
        """Reattachment 19.8% out → single failure → PASS WITH NOTES"""
        v, n = vbfs.determine_verdict_bfs(7.5, 5.0, True)
        assert v == 'PASS WITH NOTES'

    def test_short_recirculation(self):
        """Recirculation too short (2.0H < 3.0H) → single failure → PASS WITH NOTES"""
        v, n = vbfs.determine_verdict_bfs(6.26, 2.0, True)
        assert v == 'PASS WITH NOTES'

    def test_nan_reattachment(self):
        """Could not find reattachment → single failure → PASS WITH NOTES"""
        v, n = vbfs.determine_verdict_bfs(np.nan, 5.0, True)
        assert v == 'PASS WITH NOTES'

    def test_multiple_failures(self):
        """Multiple failures → FAIL"""
        v, n = vbfs.determine_verdict_bfs(10.0, 1.0, False)
        assert v == 'FAIL'

    def test_notes_returned(self):
        """Notes list should always be returned"""
        _, n = vbfs.determine_verdict_bfs(6.5, 4.0, True)
        assert isinstance(n, list)
        assert len(n) > 0


# ═══════════════════════════════════════════════════════════════════════════════
#  Integration: synthetic tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSyntheticRun:
    """Ensure --test modes run without crashing"""

    def test_flat_plate_synthetic(self):
        """validate_flat_plate --test should complete without error"""
        # Capture output, just verify no exception
        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            vfp.run_synthetic_test()
        output = stdout.getvalue()
        assert 'complete' in output.lower()

    def test_bfs_synthetic(self):
        """validate_bfs --test should complete without error"""
        import io
        import contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            vbfs.run_synthetic_test()
        output = stdout.getvalue()
        assert 'complete' in output.lower()


# ═══════════════════════════════════════════════════════════════════════════════
#  U_tau computation test (Newton-Raphson for log-law)
# ═══════════════════════════════════════════════════════════════════════════════

class TestUTauComputation:
    """Test the u_tau Newton-Raphson solver used in data extraction"""

    def test_u_tau_convergence(self):
        """Verbose test of the Newton-Raphson loop used in extract_wall_profile"""
        import math
        KAPPA = 0.41
        B = 5.0
        nu = 1.5e-5
        u_wall = 2.0  # m/s
        y_p = 5e-4  # m (first cell center)

        u_tau = u_wall / 25.0
        for _ in range(20):
            yp = y_p * u_tau / nu
            if yp < 1.0:
                u_tau = math.sqrt(nu * u_wall / y_p)
                break
            f = u_tau * (math.log(yp) / KAPPA + B) - u_wall
            df = (math.log(yp) / KAPPA + B) + 1.0 / KAPPA
            delta = f / df if abs(df) > 1e-15 else 0.0
            u_tau -= delta
            if abs(delta) < 1e-8 * abs(u_tau):
                break

        # Verify consistency: u_tau should satisfy log-law
        yp_final = y_p * u_tau / nu
        u_plus_computed = u_wall / u_tau
        u_plus_log = math.log(yp_final) / KAPPA + B
        assert abs(u_plus_computed - u_plus_log) < 0.01, \
            f"u+ computed={u_plus_computed:.3f}, log-law={u_plus_log:.3f}"

    def test_u_tau_reasonable(self):
        """u_tau should be ~5% of u_wall for typical boundary layer"""
        import math
        KAPPA = 0.41
        B = 5.0
        nu = 1.5e-5
        u_wall = 10.0
        y_p = 5e-4

        u_tau = u_wall / 25.0
        for _ in range(20):
            yp = y_p * u_tau / nu
            if yp < 1.0:
                break
            f = u_tau * (math.log(yp) / KAPPA + B) - u_wall
            df = (math.log(yp) / KAPPA + B) + 1.0 / KAPPA
            delta = f / df if abs(df) > 1e-15 else 0.0
            u_tau -= delta
            if abs(delta) < 1e-8 * abs(u_tau):
                break

        # u_tau should be roughly 3-5% of u_inf for flat plate BL
        ratio = u_tau / 10.0
        assert 0.02 < ratio < 0.09, \
            f"u_tau/U_inf ratio {ratio:.4f} outside typical range [0.02, 0.09]"
