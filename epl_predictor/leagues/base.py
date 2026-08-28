"""Shared league configuration for multi-league predictors."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


@dataclass(frozen=True)
class LeagueConfig:
    """Everything the engine / UI need for one top-flight league."""

    id: str
    name: str
    fd_code: str
    index_url: str
    currency: str
    second_tier_label: str
    fixture_feed_slug: str | None
    matchweek_count: int
    csv_name: dict[str, str]
    last_season_position: dict[str, int]
    promoted: frozenset[str]
    team_context: dict[str, dict]
    name_aliases: dict[str, str] = field(default_factory=dict)
    use_bundled_history: bool = False
    bundled_history_name: str = ""
    season_start: str = "2026-08-15"
    context_as_of: str = "20 Aug 2026"

    @property
    def clubs(self) -> list[str]:
        return list(self.csv_name.keys())

    @property
    def display_name(self) -> dict[str, str]:
        return {csv: display for display, csv in self.csv_name.items()}

    @property
    def history_path(self) -> Path:
        if self.use_bundled_history and self.bundled_history_name:
            return ROOT / self.bundled_history_name
        return DATA_DIR / f"{self.id}_final.csv"

    @property
    def cache_path(self) -> Path:
        return CACHE_DIR / f"{self.id}_model.pkl"

    def to_csv(self, display: str) -> str:
        return self.csv_name[display]

    def to_display(self, csv: str) -> str:
        return self.display_name.get(csv, csv)

    def canon_team(self, name: str) -> str:
        """Map any known alias (fixturedownload / FD short) onto the CSV name."""
        name = str(name).strip()
        if name in self.csv_name.values():
            return name
        if name in self.csv_name:
            return self.csv_name[name]
        return self.name_aliases.get(name, name)


def make_context(
    manager: str,
    *,
    previous_manager: str | None = None,
    manager_since: str = "1 July 2026",
    change_type: str = "none",
    pedigree: str = "established",
    promoted: bool = False,
    net_spend_m: float = 0,
    squad_turnover: float = 0.15,
    key_ins: list[str] | None = None,
    key_outs: list[str] | None = None,
    notes: str = "",
    shocks: list[str] | None = None,
) -> dict:
    """Build a TEAM_CONTEXT row with the same schema as the EPL overlay."""
    return {
        "manager": manager,
        "previous_manager": previous_manager or manager,
        "manager_since": manager_since,
        "change_type": change_type,
        "pedigree": pedigree,
        "promoted": promoted,
        "net_spend_m": net_spend_m,
        "squad_turnover": squad_turnover,
        "key_ins": key_ins or [],
        "key_outs": key_outs or [],
        "notes": notes,
        "shocks": shocks or [],
    }
