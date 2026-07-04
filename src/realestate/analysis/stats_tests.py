"""Statistical hypothesis testing.

Two complementary tests are reported for every comparison: a Welch t-test
(parametric, unequal variance) and the Mann-Whitney U test (non-parametric, no
normality assumption). Cohen's d is reported as an effect size so significance
is never read in isolation.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd
from scipy import stats

from .market import transaction_summary


@dataclass
class TestResult:
    comparison: str
    n_a: int
    n_b: int
    mean_a: float
    mean_b: float
    t_stat: float
    t_pvalue: float
    mannwhitney_u: float
    mw_pvalue: float
    cohens_d: float
    significant_5pct: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return float("nan")
    pooled = np.sqrt(((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2) / (na + nb - 2))
    return float((a.mean() - b.mean()) / pooled) if pooled else float("nan")


def compare_distributions(a, b, label: str) -> TestResult:
    a = np.asarray(pd.Series(a).dropna(), dtype=float)
    b = np.asarray(pd.Series(b).dropna(), dtype=float)
    t_stat, t_p = stats.ttest_ind(a, b, equal_var=False)
    u, mw_p = stats.mannwhitneyu(a, b, alternative="two-sided")
    return TestResult(
        comparison=label, n_a=len(a), n_b=len(b),
        mean_a=float(a.mean()), mean_b=float(b.mean()),
        t_stat=float(t_stat), t_pvalue=float(t_p),
        mannwhitney_u=float(u), mw_pvalue=float(mw_p),
        cohens_d=_cohens_d(a, b),
        significant_5pct=bool(min(t_p, mw_p) < 0.05),
    )


def compare_property_type_prices(tx: pd.DataFrame, type_a: str, type_b: str,
                                 group: str = "Sales") -> TestResult:
    """Test whether the per-quarter average sale value differs between two
    property types."""
    s = transaction_summary(tx)
    s = s[s["transaction_group"] == group]
    a = s[s["property_type"] == type_a]["avg_value_per_txn"]
    b = s[s["property_type"] == type_b]["avg_value_per_txn"]
    return compare_distributions(a, b, f"{type_a} vs {type_b} avg sale value ({group})")


def compare_offplan_vs_ready_completion(projects: pd.DataFrame) -> TestResult:
    """Test whether completion percentages differ between off-plan and ready
    projects."""
    a = projects[projects["is_offplan"]]["percent_completed"]
    b = projects[projects["is_ready"]]["percent_completed"]
    return compare_distributions(a, b, "Off-plan vs ready completion %")
