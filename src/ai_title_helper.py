import os
import logging
import anthropic

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def generate_activity_title(activity_data, weather_data):
    """
    Generate a creative activity title using the Claude API.

    Args:
        activity_data: dict with keys - name, type, distance, elevation_gain,
                       elapsed_time_minutes, start_time, geo_location
        weather_data:  dict with keys - temperature (°F), elevation (ft)

    Returns:
        str: Generated activity title (60 chars or fewer)
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    sport_type      = activity_data.get("sport_type") or activity_data.get("type", "Activity")
    distance_km     = activity_data.get("distance", 0)
    elevation_m     = activity_data.get("elevation_gain", 0)
    elev_high_m     = activity_data.get("elev_high")
    elev_low_m      = activity_data.get("elev_low")
    moving_min      = activity_data.get("moving_time_minutes", activity_data.get("elapsed_time_minutes", 0))
    avg_speed_kmh   = activity_data.get("avg_speed_kmh", 0)
    max_speed_kmh   = activity_data.get("max_speed_kmh", 0)
    calories        = activity_data.get("calories")
    pr_count        = activity_data.get("pr_count", 0)
    suffer_score    = activity_data.get("suffer_score")
    avg_watts       = activity_data.get("avg_watts")
    avg_cadence     = activity_data.get("avg_cadence")
    start_time      = activity_data.get("start_time", "")
    temperature_f   = round(weather_data.get("temperature", 0))
    elevation_ft    = round(weather_data.get("elevation", 0))

    # Build optional detail lines so the prompt stays clean when fields are absent
    optional_lines = []
    if avg_speed_kmh:
        optional_lines.append(f"- Average speed: {avg_speed_kmh:.1f} km/h (max {max_speed_kmh:.1f} km/h)")
    if avg_watts:
        optional_lines.append(f"- Average power: {avg_watts:.0f} W")
    if avg_cadence:
        optional_lines.append(f"- Average cadence: {avg_cadence:.0f} rpm")
    if calories:
        optional_lines.append(f"- Calories burned: {calories:.0f}")
    if pr_count:
        optional_lines.append(f"- PRs set: {pr_count}")
    if suffer_score:
        optional_lines.append(f"- Suffer score: {suffer_score}")
    if elev_high_m is not None and elev_low_m is not None:
        optional_lines.append(f"- Elevation range: {elev_low_m:.0f} m – {elev_high_m:.0f} m")

    optional_section = "\n".join(optional_lines)

    prompt = f"""Generate a single fun, creative, and descriptive title for this {sport_type}.

Activity details:
- Sport type: {sport_type}
- Distance: {distance_km:.1f} km
- Moving time: {moving_min:.0f} minutes
- Elevation gain: {elevation_m:.0f} m
- Weather: {temperature_f}°F at {elevation_ft} ft elevation
- Start time: {start_time}
{optional_section}

Rules:
- Return ONLY the title, no quotes, no explanation
- Maximum 60 characters
- Make it specific to the conditions (weather, distance, effort, any PRs)
- Be creative — avoid generic titles like "Morning Run" or "Afternoon Ride"

Title:"""

    logger.info("Calling Claude API to generate activity title")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=64,
        messages=[{"role": "user", "content": prompt}]
    )

    title = message.content[0].text.strip()
    logger.info(f"Generated title: {title}")
    return title
