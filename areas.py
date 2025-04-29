# areas.py

# הגדרת האזורים והמיקומים
areas = {
    'A': {'rows': (0, 2), 'cols': (0, 3)},  # שורות 0-2, עמודות 0-3
    'B': {'rows': (0, 1), 'cols': (4, 7)},  # שורות 0-1, עמודות 4-7
    'C': {'rows': (3, 5), 'cols': (0, 2)},  # שורות 3-5, עמודות 0-2
    'D': {'rows': (3, 5), 'cols': (3, 7)}   # שורות 3-5, עמודות 3-7
}

# חישוב כמה שורות ועמודות צריך
def calculate_size_from_areas(areas):
    max_row = 0
    max_col = 0
    for bounds in areas.values():
        r_end = bounds['rows'][1]
        c_end = bounds['cols'][1]
        if r_end > max_row:
            max_row = r_end
        if c_end > max_col:
            max_col = c_end
    return max_row + 1, max_col + 1  # צריך להוסיף 1 כי מתחילים מ-0

# יצירת מפת אזורים (2D list של אזורים)
def generate_area_map(rows, cols, areas):
    area_map = [['' for _ in range(cols)] for _ in range(rows)]
    for area, bounds in areas.items():
        r_start, r_end = bounds['rows']
        c_start, c_end = bounds['cols']
        for r in range(r_start, r_end + 1):
            for c in range(c_start, c_end + 1):
                area_map[r][c] = area
    return area_map

# פונקציה שמכינה הכל יחד
def prepare_area_map():
    rows, cols = calculate_size_from_areas(areas)
    area_map = generate_area_map(rows, cols, areas)
    return area_map, rows, cols
