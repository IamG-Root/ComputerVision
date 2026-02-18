import curses

CONFIG_FILE = "module/config.py"

PARAMS = [
    "CAMERA_H",
    "CAMERA_PITCH_DEG",
    "CAMERA_POS_X",
    "CAMERA_POS_Z",
    "ORIENTATION",
    "MODULE_NAME",
    "BROKER_IP_ADDRESS",
]


def load_config():
    config = {}
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            for key in PARAMS:
                if line.startswith(key):
                    config[key] = line.split("=")[1].strip()
    return config


def save_config(config):
    with open(CONFIG_FILE, "r") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        replaced = False
        for key in config:
            if line.startswith(key):
                new_lines.append(f"{key} = {config[key]}\n")
                replaced = True
                break
        if not replaced:
            new_lines.append(line)

    with open(CONFIG_FILE, "w") as f:
        f.writelines(new_lines)


def main(stdscr):
    curses.curs_set(0)
    config = load_config()
    selected = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "=== CONFIGURATION WIZARD (ENTER to edit, Q exit) ===")

        for i, key in enumerate(PARAMS):
            value = config.get(key, "")
            if i == selected:
                stdscr.addstr(i + 2, 0, f"> {key} = {value}", curses.A_REVERSE)
            else:
                stdscr.addstr(i + 2, 0, f"  {key} = {value}")

        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected = (selected - 1) % len(PARAMS)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(PARAMS)
        elif key == ord("\n"):
            curses.echo()
            stdscr.addstr(len(PARAMS) + 4, 0, "Nuovo valore: ")
            new_value = stdscr.getstr().decode()
            curses.noecho()

            if new_value:
                if not new_value.startswith('"') and not new_value.replace('.', '', 1).isdigit():
                    new_value = f'"{new_value}"'
                config[PARAMS[selected]] = new_value
                save_config(config)

        elif key in [ord("q"), ord("Q")]:
            break


if __name__ == "__main__":
    curses.wrapper(main)