import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap


FACTION_COLORS = {
    "Castle": "#4F6F8F",      # steel blue-gray
    "Rampart": "#1B8E3E",     # vivid forest green
    "Tower": "#0077B6",       # clean saturated blue
    "Inferno": "#C62828",     # red
    "Necropolis": "#1F1F1F",  # near black
    "Dungeon": "#6D3B1F",     # dark brown
    "Stronghold": "#A45718",  # warm rust-brown
    "Fortress": "#5B7F24",    # swamp olive green
    "Conflux": "#F57C00",     # orange
    "Cove": "#B83280",        # magenta/pink-purple
    "Factory": "#C28A13",     # sand/gold-brown
    "Bulwark": "#00A6D6",     # saturated ice cyan
    "Neutral": "#6E6E6E",     # gray
    "Cathedral": "#8E6D00",   # dark gold
}


def _build_matrix(results: list[dict], stack_ids: list[str]):
    stack2index = {stack_id: index for index, stack_id in enumerate(stack_ids)}
    matrix = np.full((len(stack_ids), len(stack_ids)), np.nan)

    for result in results:
        ids = [key for key in result if key in stack2index]
        if len(ids) != 2:
            continue

        stack1_id, stack2_id = ids
        row = stack2index[stack1_id]
        col = stack2index[stack2_id]
        matrix[row][col] = result[stack1_id]

    return matrix


def _apply_unit_name_colors(ax, homes: list[str]):
    for label, home in zip(ax.get_xticklabels(), homes):
        label.set_color(FACTION_COLORS.get(home, FACTION_COLORS["Neutral"]))
        label.set_fontweight("bold")

    for label, home in zip(ax.get_yticklabels(), homes):
        label.set_color(FACTION_COLORS.get(home, FACTION_COLORS["Neutral"]))
        label.set_fontweight("bold")


def draw_round_robin_results(json_path: str | Path, output_path: str | Path | None = None, show: bool = True):
    with Path(json_path).open("r", encoding="utf-8") as file:
        data = json.load(file)

    stack_ids = list(data["stacks"])
    units = [
        f"{data['stacks'][stack_id]['name']} ({data['stacks'][stack_id]['count']})"
        for stack_id in stack_ids
    ]
    homes = [data["stacks"][stack_id].get("home", "Neutral") for stack_id in stack_ids]
    matrix = _build_matrix(data["results"], stack_ids)
    n_runs = data["settings"]["n_runs"]

    fig, ax = plt.subplots(figsize=(max(8, len(units) * 0.8), max(6, len(units) * 0.7)))

    cmap = LinearSegmentedColormap.from_list("match_results", ["#d99a9a", "#f2eddc", "#98c993"])
    cmap.set_bad("#f4f4f4")

    ax.imshow(np.ma.masked_invalid(matrix), cmap=cmap, vmin=0, vmax=n_runs)

    ax.set_xticks(range(len(units)), labels=units, rotation=90, ha="center")
    ax.set_yticks(range(len(units)), labels=units)
    ax.set_xlabel("Defender")
    ax.set_ylabel("Attacker")

    _apply_unit_name_colors(ax, homes)

    ax.set_xticks(np.arange(len(units) + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(units) + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="#363636", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)

    for row in range(len(units)):
        for col in range(len(units)):
            if np.isnan(matrix[row][col]):
                continue
            ax.text(col, row, int(matrix[row][col]), ha="center", va="center", color="#222222", fontsize=12)

    fig.tight_layout()

    if output_path is not None:
        fig.savefig(output_path, dpi=150)

    if show:
        plt.show()

    return fig, ax