from pathlib import Path

import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).resolve().parents[1] / "07_figures"
OUT.mkdir(parents=True, exist_ok=True)

ROWS = [
    "LLaMa3.2-3B\n(T=169)", "Gemini2.5-Pro\n(T=152)",
    "Gemini2.5-Flash\n(T=139)", "GPT-OSS-20B\n(T=137)",
    "LLaMa3.3-70B\n(T=177)", "Qwen3-Coder-30B\n(T=177)",
    "Codestral-22B\n(T=123)",
]
COLS = ["LLaMa3.2-3B", "GPT-OSS-20B", "LLaMa3.3-70B", "Qwen3-Coder-30B", "Codestral-22B"]
CMAP = colors.LinearSegmentedColormap.from_list("accessible_powder", ["#F4F1F0", "#D8D3D0", "#BFD7EA", "#6F98B5"])


def heatmap(filename, data, title, colorbar, fmt, vmin, vmax, white_threshold):
    values = np.asarray(data, dtype=float)
    fig, ax = plt.subplots(figsize=(12.0, 8.0))
    image = ax.imshow(values, cmap=CMAP, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(len(COLS)), labels=COLS, fontsize=13)
    ax.set_yticks(np.arange(len(ROWS)), labels=ROWS, fontsize=13)
    plt.setp(ax.get_xticklabels(), rotation=28, ha="right", rotation_mode="anchor")
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, format(values[i, j], fmt), ha="center", va="center",
                    fontsize=13, color="white" if values[i, j] >= white_threshold else "black",
                    fontweight="semibold")
    ax.set_xticks(np.arange(-0.5, len(COLS), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ROWS), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="minor", bottom=False, left=False)
    bar = fig.colorbar(image, ax=ax, fraction=0.045, pad=0.03)
    bar.set_label(colorbar, fontsize=13)
    bar.ax.tick_params(labelsize=12)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=16)
    ax.set_xlabel("Optimizer Model", fontsize=14)
    ax.set_ylabel("Source Model", fontsize=14)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / filename, format="pdf", bbox_inches="tight")
    plt.close(fig)


heatmap(
    "figure10_trr_readable.pdf",
    np.asarray([
        [0.0828, 0.3846, 0.3787, 0.5325, 0.4313], [0.0197, 0.4408, 0.2565, 0.4210, 0.2697],
        [0.0071, 0.3381, 0.1727, 0.4173, 0.2237], [0.0511, 0.4160, 0.2846, 0.5182, 0.3577],
        [0.0000, 0.3333, 0.2259, 0.4068, 0.3051], [0.0282, 0.5870, 0.4971, 0.6836, 0.5531],
        [0.0081, 0.3333, 0.2276, 0.4390, 0.3008],
    ]) * 100,
    "TRR Across Source-Optimizer Model Pairs", "Test Redundancy Ratio (%)", ".1f", 0, 70, 50,
)

heatmap(
    "figure11_cd_readable.pdf",
    [
        [0.89, 0.57, 0.62, 0.46, 0.55], [0.99, 0.46, 0.67, 0.59, 0.70],
        [0.997, 0.68, 0.82, 0.59, 0.76], [0.91, 0.51, 0.63, 0.49, 0.65],
        [1.00, 0.54, 0.74, 0.45, 0.63], [0.98, 0.30, 0.39, 0.19, 0.33],
        [0.99, 0.59, 0.79, 0.52, 0.63],
    ],
    "Comparison Density Across Source-Optimizer Model Pairs", "Comparison Density", ".2f", 0, 1, 0.75,
)

heatmap(
    "figure12_scp_readable.pdf",
    [
        [100, 100, 100, 87.50, 100], [100, 100, 100, 100, 100],
        [92.86, 92.86, 100, 100, 100], [100, 91.67, 100, 91.67, 100],
        [100, 100, 100, 100, 100], [100, 100, 87.50, 100, 100],
        [100, 100, 100, 100, 100],
    ],
    "Legacy Raw-ID SCP Across Source-Optimizer Model Pairs", "Legacy SCP (%)", ".2f", 85, 100, 99,
)

print(f"Wrote three vector figures to {OUT}")
