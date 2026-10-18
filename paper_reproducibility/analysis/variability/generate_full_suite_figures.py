from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
VAR = ROOT / "07_variability_analysis"
OUT = ROOT / "11_figures"
MODE_ORDER = ["Local Bulk", "Controlled Local Parallel"]
MODEL_ORDER = ["Llama 3.2 3B", "GPT-OSS 20B", "Qwen3-Coder 30B A3B"]
SUITE_LABEL = {"FULLREQ": "Requirements full suite", "FULLSRC": "Source-code full suite"}
COLORS = {"Local Bulk": "#2B6CB0", "Controlled Local Parallel": "#DD6B20"}


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def grouped_metric(rows: list[dict[str, str]], metric: str, sd: str, ylabel: str, stem: str) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.25), sharey=True)
    x = np.arange(len(MODEL_ORDER))
    width = 0.34
    for ax, suite in zip(axes, ("FULLREQ", "FULLSRC")):
        for j, mode in enumerate(MODE_ORDER):
            vals, errs = [], []
            for model in MODEL_ORDER:
                row = next(r for r in rows if r["suite_id"] == suite and r["model_display"] == model and r["mode"] == mode)
                vals.append(float(row[metric]))
                errs.append(float(row[sd]))
            ax.bar(x + (j - 0.5) * width, vals, width, yerr=errs, capsize=3,
                   label=mode, color=COLORS[mode], edgecolor="black", linewidth=0.5)
        ax.set_title(SUITE_LABEL[suite], fontsize=10)
        ax.set_xticks(x, ["Llama 3.2\n3B", "GPT-OSS\n20B", "Qwen3-Coder\n30B A3B"], fontsize=8.5)
        ax.grid(axis="y", alpha=0.25, linewidth=0.6)
        ax.set_axisbelow(True)
    axes[0].set_ylabel(ylabel, fontsize=9.5)
    axes[0].legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    save(fig, stem)


def stability_heatmap(rows: list[dict[str, str]]) -> None:
    labels = []
    values = []
    for suite in ("FULLREQ", "FULLSRC"):
        for model in MODEL_ORDER:
            labels.append(f"{SUITE_LABEL[suite]}\n{model}")
            values.append([
                100 * float(next(r for r in rows if r["suite_id"] == suite and r["model_display"] == model and r["mode"] == mode)["mean_modal_agreement"])
                for mode in MODE_ORDER
            ])
    matrix = np.array(values)
    fig, ax = plt.subplots(figsize=(6.4, 4.8))
    image = ax.imshow(matrix, cmap="YlGnBu", vmin=70, vmax=100, aspect="auto")
    ax.set_xticks(range(2), ["Local Bulk", "Controlled Local Parallel"], fontsize=9)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            color = "white" if matrix[i, j] > 91 else "black"
            ax.text(j, i, f"{matrix[i, j]:.1f}%", ha="center", va="center", fontsize=9, color=color)
    cbar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.03)
    cbar.set_label("Mean modal agreement (%)", fontsize=9)
    ax.set_title("Full-suite repeated-decision stability (five repeats)", fontsize=10)
    fig.tight_layout()
    save(fig, "full_suite_decision_stability")


def main() -> None:
    variability = read(VAR / "variability_statistics.csv")
    stability = read(VAR / "decision_stability_summary.csv")
    grouped_metric(variability, "trr_mean", "trr_sample_sd", "Test Redundancy Ratio (mean ± sample SD)", "full_suite_trr_variability")
    grouped_metric(variability, "artifact_scoped_scp_mean", "artifact_scoped_scp_sample_sd", "Artifact-scoped SCP (mean ± sample SD)", "full_suite_scoped_scp")
    stability_heatmap(stability)
    print("Created three vector PDF figures and 300-dpi previews")


if __name__ == "__main__":
    main()
