def format_number(value):
    """Format numbers using Indonesian separators: 1.234.567,89."""
    value = float(value)

    if value.is_integer():
        return f"{int(value):,}".replace(",", ".")

    return (
        f"{value:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def format_percentage(value, decimals=2):
    """Format percentages with Indonesian decimal separators."""
    value = float(value)
    return f"{value:.{decimals}f}".replace(".", ",") + "%"
