def format_instagram_caption(
    text: str, hashtags: list[str] | None = None, max_length: int = 2200
) -> str:
    caption = text.strip()

    if hashtags:
        tags_str = " ".join(f"#{tag.lstrip('#')}" for tag in hashtags[:30])
        separator = "\n.\n.\n.\n"
        available = max_length - len(separator) - len(tags_str)
        if len(caption) > available:
            caption = caption[:available - 3] + "..."
        caption = f"{caption}{separator}{tags_str}"
    else:
        if len(caption) > max_length:
            caption = caption[: max_length - 3] + "..."

    return caption


def format_youtube_description(
    text: str,
    links: list[dict] | None = None,
    tags: list[str] | None = None,
    max_length: int = 5000,
) -> str:
    parts = [text.strip()]

    if links:
        parts.append("\n--- Links ---")
        for link in links:
            parts.append(f"{link.get('label', 'Link')}: {link.get('url', '')}")

    if tags:
        total_chars = 0
        valid_tags = []
        for tag in tags:
            if total_chars + len(tag) + 1 <= 500:
                valid_tags.append(tag)
                total_chars += len(tag) + 1
        parts.append("\n--- Tags ---")
        parts.append(", ".join(valid_tags))

    description = "\n".join(parts)
    if len(description) > max_length:
        description = description[: max_length - 3] + "..."

    return description


def format_youtube_title(text: str, max_length: int = 100) -> str:
    title = text.strip()
    if len(title) > max_length:
        title = title[: max_length - 3] + "..."
    return title


REPURPOSE_TEMPLATES = {
    ("instagram", "youtube"): """Adapt this Instagram post for YouTube:
- Expand the caption into a detailed video description (500-1000 words)
- Generate an engaging, hook-driven video title (max 100 chars)
- Convert hashtags to YouTube tags
- Suggest video chapter timestamps format
- Add a CTA to subscribe""",
    ("youtube", "instagram"): """Adapt this YouTube content for Instagram:
- Condense the description into a punchy caption (max 2200 chars)
- Start with a strong hook in the first line
- Use emojis strategically
- Convert tags to Instagram hashtags (max 30)
- Suggest carousel slide ideas from key points
- Add a CTA to watch the full video""",
}
