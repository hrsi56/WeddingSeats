# utils.py

tables_config = {
    "A": 12, "B": 12, "C": 12, "D": 12,
    "E": 12, "F": 12, "G": 12, "H": 12,
    "I": 12, "J": 12, "K": 12, "L": 12,
    "M": 12, "N": 12, "O": 12, "P": 12,
    "Q": 12, "R": 12, "S": 12, "T": 12,
    "U": 12, "V": 12, "W": 12, "X": 12
}

def generate_seating_html(table_id, num_seats):
    buttons = ""
    for i in range(1, num_seats + 1):
        seat_id = f"{table_id}{i}"
        buttons += f'''
            <button id="{seat_id}" onclick="toggleSeat('{seat_id}')" 
            style="margin:4px;padding:10px 14px;border-radius:6px;
                   border:1px solid #ccc;cursor:pointer;">
                {seat_id}
            </button>
        '''
    script = """
    <script>
    function toggleSeat(id) {
        const el = document.getElementById(id);
        if (el.style.backgroundColor === "lightgreen") {
            el.style.backgroundColor = "";
        } else {
            el.style.backgroundColor = "lightgreen";
        }
    }
    </script>
    """
    return f"""
    <div style='margin:10px;padding:10px;border:1px solid #ddd;
                border-radius:8px;text-align:center;'>
        שולחן {table_id}<br>{buttons}
    </div>
    {script}
    """