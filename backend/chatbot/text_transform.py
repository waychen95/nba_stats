import json
import math
import pandas as pd
import numpy as np

PLAYERS_CSV = "../export/merged_players.csv"
TEAMS_CSV = "../export/teams.csv"
STATS_CSV = "../export/merged_stats.csv"

OUT_JSONL = "docs.jsonl"

BIO_MAX_CHARS = 500

def clean(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    s = str(x).strip()
    if s.lower() == "nan":
        return ""
    return s

def to_float(x, default=0.0) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, float) and math.isnan(x):
            return default
        s = str(x).strip()
        if s.lower() == "nan" or s == "":
            return default
        return float(s)
    except Exception:
        return default


def safe_div(numer: float, denom: float) -> float | None:
    if denom <= 0:
        return None
    return numer / denom


def fmt_pct(ratio: float | None) -> str:
    if ratio is None:
        return ""
    return f"{ratio * 100:.1f}%"


def to_int(x, default=0) -> int:
    try:
        return int(float(x))
    except Exception:
        return default


def short_text(s: str, max_chars: int) -> str:
    s = clean(s)
    if not s:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars].rsplit(" ", 1)[0] + "..."


def fmt_height(feet, inches) -> str:
    f = clean(feet)
    i = clean(inches)
    if not f and not i:
        return ""
    if not f:
        return f"0'{i}"
    if not i:
        return f"{f}'0"
    return f"{f}'{i}"


def convert_to_native_types(obj):
    """Convert numpy/pandas types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, (np.integer, pd.Int64Dtype)):
        return int(obj)
    elif isinstance(obj, (np.floating, pd.Float64Dtype)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj


def build_team_docs(teams: pd.DataFrame) -> list[dict]:
    docs = []
    for _, t in teams.iterrows():
        team_id = to_int(t.get("id"))
        abbr = clean(t.get("name")).upper()
        full_name = clean(t.get("full_name")).title()
        city = clean(t.get("city"))
        conf = clean(t.get("conference"))
        coach = clean(t.get("head_coach"))
        url = clean(t.get("url"))
        image_url = clean(t.get("logo_url"))

        # Create a richer main team document
        text_parts = []
        
        # Start with multiple name variations for better matching
        if city or full_name or abbr:
            full_team = f"{city} {full_name}".strip()
            text_parts.append(f"{full_team} ({abbr})")
            text_parts.append(f"The {full_team} are an NBA team")
            if abbr:
                text_parts.append(f"Team abbreviation: {abbr}")
        
        if conf:
            text_parts.append(f"Conference: {conf}")
            text_parts.append(f"The team plays in the {conf} conference")
        
        if coach:
            text_parts.append(f"Head coach: {coach}")
            text_parts.append(f"{coach} is the head coach of the {full_team}")
        
        if city:
            text_parts.append(f"Located in {city}")
            
        if url:
            text_parts.append(f"Official website: {url}")
        
        if image_url:
            text_parts.append(f"Team logo: {image_url}")

        text = ". ".join([p for p in text_parts if p]).strip() + "."

        # Main team info document
        docs.append({
            "id": f"team:{team_id}",
            "text": text,
            "meta": {
                "doc_type": "team",
                "team_id": team_id,
                "team_abbr": abbr,
                "team_name": f"{city} {full_name}".strip(),
                "team_url": url,
                "team_image_url": image_url
            }
        })
        
        # Create a separate coaching document for better coach queries
        if coach:
            coach_text = f"The head coach of the {city} {full_name} ({abbr}) is {coach}. {coach} coaches the {abbr}."
            docs.append({
                "id": f"team_coach:{team_id}",
                "text": coach_text,
                "meta": {
                    "doc_type": "team_coach",
                    "team_id": team_id,
                    "team_abbr": abbr,
                    "team_name": f"{city} {full_name}".strip(),
                    "head_coach": coach,
                    "team_url": url,
                    "team_image_url": image_url
                }
            })

    return docs


def build_player_docs(players: pd.DataFrame, stats: pd.DataFrame, teams: pd.DataFrame) -> list[dict]:
    docs = []

    team_map = teams.set_index("id")[["name", "full_name", "city"]].to_dict("index")

    for _, p in players.iterrows():
        player_id = to_int(p.get("id"))
        first = clean(p.get("first_name"))
        last = clean(p.get("last_name"))
        full_name = f"{first} {last}".strip()

        position = clean(p.get("position"))
        height = fmt_height(p.get("feet"), p.get("inches"))
        weight = clean(p.get("weight"))
        country = clean(p.get("country"))
        school = clean(p.get("last_attended"))
        active = clean(p.get("active"))
        url = clean(p.get("url"))
        image_url = clean(p.get("image_url"))

        # Current team info may exist in your merged players CSV (name, full_name, city)
        cur_abbr = clean(p.get("name")).upper()
        cur_full = clean(p.get("full_name")).title()
        cur_city = clean(p.get("city"))
        cur_team_text = ""
        if cur_full or cur_abbr or cur_city:
            cur_team_text = f"{cur_city} {cur_full} ({cur_abbr})".strip()

        past_teams = clean(p.get("past_teams"))
        # Optional short bio, avoid huge wall of text
        bio = short_text(p.get("bio"), BIO_MAX_CHARS)

        profile_parts = [f"{full_name}."]
        if position:
            profile_parts.append(f"Position: {position}.")
        if height:
            profile_parts.append(f"Height: {height}.")
        if weight:
            profile_parts.append(f"Weight: {weight} lbs.")
        if country:
            profile_parts.append(f"Country: {country}.")
        if school:
            profile_parts.append(f"School: {school}.")
        if active:
            profile_parts.append(f"Active: {active}.")
        if cur_team_text:
            profile_parts.append(f"Current team: {cur_team_text}.")
        if past_teams:
            profile_parts.append(f"Past teams: {past_teams}.")
        if bio:
            profile_parts.append(f"Bio: {bio}")
        if url:
            profile_parts.append(f"URL: {url}")
        if image_url:
            profile_parts.append(f"Image: {image_url}")

        profile_text = " ".join(profile_parts).strip()

        docs.append({
            "id": f"player_profile:{player_id}",
            "text": profile_text,
            "meta": {
                "doc_type": "player_profile",
                "player_id": player_id,
                "player_name": full_name,
                "player_url": url,
                "player_image_url": image_url
            }
        })

        # Season docs: one per row in stats for this player_id
        ps = stats[stats["player_id"] == player_id]
        for _, s in ps.iterrows():
            season = clean(s.get("year"))
            team_id = to_int(s.get("team_id"))
            team_info = team_map.get(team_id, {})
            team_abbr = clean(team_info.get("name")).upper()
            team_full = clean(team_info.get("full_name")).title()
            team_city = clean(team_info.get("city"))
            team_name = f"{team_city} {team_full}".strip()

            # Keep key stats only, include the ones users usually ask
            season_text = (
                f"{full_name}, {season}, {team_name} ({team_abbr}). "
                f"GP {clean(s.get('gp'))}, MIN {clean(s.get('min'))}, "
                f"PTS {clean(s.get('pts'))}, REB {clean(s.get('reb'))}, AST {clean(s.get('ast'))}, "
                f"FG% {clean(s.get('fg_pct'))}, 3P% {clean(s.get('3p_pct'))}, FT% {clean(s.get('ft_pct'))}, "
                f"STL {clean(s.get('stl'))}, BLK {clean(s.get('blk'))}, TOV {clean(s.get('tov'))}, "
                f"+/- {clean(s.get('plus_minus'))}."
            ).strip()

            docs.append({
                "id": f"player_season:{player_id}:{season}:{team_abbr}",
                "text": season_text,
                "meta": {
                    "doc_type": "player_season",
                    "player_id": player_id,
                    "player_name": full_name,
                    "season": season,
                    "team_id": team_id,
                    "team_abbr": team_abbr,
                    "player_url": url,
                    "player_image_url": image_url
                }
            })

        # Career aggregation doc
        if not ps.empty:
            total_gp = 0.0

            # Weighted per-game sums
            sum_min = 0.0
            sum_pts = 0.0
            sum_reb = 0.0
            sum_ast = 0.0
            sum_tov = 0.0
            sum_stl = 0.0
            sum_blk = 0.0
            sum_pf = 0.0
            sum_plus_minus = 0.0

            # Totals for percentage calculation
            total_fgm = 0.0
            total_fga = 0.0
            total_3pm = 0.0
            total_3pa = 0.0
            total_ftm = 0.0
            total_fta = 0.0

            for _, s in ps.iterrows():
                gp = to_float(s.get("gp"), 0.0)
                if gp <= 0:
                    continue

                total_gp += gp

                # Per-game stats, weighted by games played
                sum_min += to_float(s.get("min"), 0.0) * gp
                sum_pts += to_float(s.get("pts"), 0.0) * gp
                sum_reb += to_float(s.get("reb"), 0.0) * gp
                sum_ast += to_float(s.get("ast"), 0.0) * gp
                sum_tov += to_float(s.get("tov"), 0.0) * gp
                sum_stl += to_float(s.get("stl"), 0.0) * gp
                sum_blk += to_float(s.get("blk"), 0.0) * gp
                sum_pf += to_float(s.get("pf"), 0.0) * gp

                # plus_minus is typically per game in your dataset, weight similarly
                sum_plus_minus += to_float(s.get("plus_minus"), 0.0) * gp

                # Shooting: per-game made/attempts to totals
                total_fgm += to_float(s.get("fgm"), 0.0) * gp
                total_fga += to_float(s.get("fga"), 0.0) * gp
                total_3pm += to_float(s.get("3pm"), 0.0) * gp
                total_3pa += to_float(s.get("3pa"), 0.0) * gp
                total_ftm += to_float(s.get("ftm"), 0.0) * gp
                total_fta += to_float(s.get("fta"), 0.0) * gp

            if total_gp > 0:
                career_mpg = sum_min / total_gp
                career_ppg = sum_pts / total_gp
                career_rpg = sum_reb / total_gp
                career_apg = sum_ast / total_gp
                career_tov = sum_tov / total_gp
                career_stl = sum_stl / total_gp
                career_blk = sum_blk / total_gp
                career_pf = sum_pf / total_gp
                career_pm = sum_plus_minus / total_gp

                fg_pct = safe_div(total_fgm, total_fga)
                tp_pct = safe_div(total_3pm, total_3pa)
                ft_pct = safe_div(total_ftm, total_fta)

                parts = [
                    f"{full_name} career NBA averages.",
                    f"Games: {int(total_gp)}.",
                    f"MPG: {career_mpg:.1f}.",
                    f"PPG: {career_ppg:.1f}.",
                    f"RPG: {career_rpg:.1f}.",
                    f"APG: {career_apg:.1f}.",
                    f"STL: {career_stl:.1f}.",
                    f"BLK: {career_blk:.1f}.",
                    f"TOV: {career_tov:.1f}.",
                    f"PF: {career_pf:.1f}."
                ]

                fg_str = fmt_pct(fg_pct)
                tp_str = fmt_pct(tp_pct)
                ft_str = fmt_pct(ft_pct)

                if fg_str:
                    parts.append(f"FG%: {fg_str}.")
                if tp_str:
                    parts.append(f"3P%: {tp_str}.")
                if ft_str:
                    parts.append(f"FT%: {ft_str}.")

                # Optional, can be noisy but sometimes users ask
                parts.append(f"+/- per game: {career_pm:.1f}.")

                career_text = " ".join(parts).strip()

                docs.append({
                    "id": f"player_career:{player_id}",
                    "text": career_text,
                    "meta": {
                        "doc_type": "player_career",
                        "player_id": player_id,
                        "player_name": full_name,
                        "player_url": url,
                        "player_image_url": image_url
                    }
                })

    return docs

def build_roster_docs(players: pd.DataFrame, stats: pd.DataFrame, teams: pd.DataFrame) -> list[dict]:
    """Build documents for team rosters by season."""
    docs = []
    
    team_map = teams.set_index("id")[["name", "full_name", "city"]].to_dict("index")
    
    # Group stats by team and season
    stats_with_names = stats.merge(
        players[['id', 'first_name', 'last_name', 'position']], 
        left_on='player_id', 
        right_on='id', 
        how='left'
    )
    
    grouped = stats_with_names.groupby(['team_id', 'year'])
    
    for (team_id, season), group in grouped:
        team_info = team_map.get(team_id, {})
        team_abbr = clean(team_info.get("name")).upper()
        team_full = clean(team_info.get("full_name")).title()
        team_city = clean(team_info.get("city"))
        team_name = f"{team_city} {team_full}".strip()
        
        if not team_name or not season:
            continue
        
        # Sort by minutes played to get key players first
        group = group.sort_values('min', ascending=False)
        
        # Build roster text with player names and key stats
        player_lines = []
        for _, row in group.iterrows():
            first = clean(row.get('first_name'))
            last = clean(row.get('last_name'))
            player_name = f"{first} {last}".strip()
            pos = clean(row.get('position'))
            pts = clean(row.get('pts'))
            reb = clean(row.get('reb'))
            ast = clean(row.get('ast'))
            gp = clean(row.get('gp'))
            
            # Create player entry
            player_info = f"{player_name}"
            if pos:
                player_info += f" ({pos})"
            if pts and reb and ast:
                player_info += f": {pts} PPG, {reb} RPG, {ast} APG"
            if gp:
                player_info += f", {gp} GP"
            
            player_lines.append(player_info)
        
        # Create comprehensive roster text
        roster_text = (
            f"{team_name} ({team_abbr}) roster for the {season} season. "
            f"Players: {', '.join([p.split(':')[0].strip() for p in player_lines[:15]])}. "  # Names only for searchability
            f"\n\nDetailed stats:\n" + "\n".join(player_lines[:15])  # Top 15 players with stats
        )
        
        # Also create a simpler version for better embedding
        simple_roster = (
            f"The {team_name} {team_abbr} {season} roster included: "
            f"{', '.join([p.split('(')[0].strip() for p in player_lines])}. "
            f"Team roster for {season} season."
        )
        
        docs.append({
            "id": f"roster:{team_id}:{season}",
            "text": roster_text,
            "meta": {
                "doc_type": "roster",
                "team_id": int(team_id),  # Ensure native int
                "team_abbr": team_abbr,
                "team_name": team_name,
                "season": str(season),  # Ensure native str
                "player_count": len(player_lines)
            }
        })
        
        # Add the simpler version as a separate doc for better retrieval
        docs.append({
            "id": f"roster_simple:{team_id}:{season}",
            "text": simple_roster,
            "meta": {
                "doc_type": "roster_simple",
                "team_id": int(team_id),  # Ensure native int
                "team_abbr": team_abbr,
                "team_name": team_name,
                "season": str(season),  # Ensure native str
                "player_count": len(player_lines)
            }
        })
    
    return docs


def main():
    players = pd.read_csv(PLAYERS_CSV)
    teams = pd.read_csv(TEAMS_CSV)
    stats = pd.read_csv(STATS_CSV)

    docs = []
    docs.extend(build_team_docs(teams))
    docs.extend(build_player_docs(players, stats, teams))
    docs.extend(build_roster_docs(players, stats, teams))

    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for d in docs:
            # Convert numpy/pandas types to native Python types
            d_converted = convert_to_native_types(d)
            f.write(json.dumps(d_converted, ensure_ascii=False) + "\n")

    print(f"Created {OUT_JSONL} with {len(docs)} documents.")
    print("Each line is one doc with {id, text, meta}, this is the file used before embedding.")


if __name__ == "__main__":
    main()