#!/usr/bin/env python3
"""
⚛ AML AI Copilot — Quantum Backend Launcher
SEA Quantathon 2026 · QCFinOp Team

Run this launcher to select the backend before starting the system. ✅
Usage: py launcher.py
"""
import os
import sys
import re
import subprocess
from pathlib import Path
from typing import Literal

# ─── ANSI Color Codes ────────────────────────────────────────────────────────
# Enable ANSI on Windows
if os.name == "nt":
    os.system("color")

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    # Foreground
    WHITE   = "\033[97m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    GRAY    = "\033[90m"
    # Background
    BG_DARK   = "\033[40m"
    BG_BLUE   = "\033[44m"
    BG_GREEN  = "\033[42m"


BackendType = Literal["classical", "quandela", "qudora"]

# ─── Backend Definitions ──────────────────────────────────────────────────────
BACKENDS = [
    {
        "key":  "1",
        "id":   "qudora",
        "name": "Qamelion (trapped-ion)",
        "type": "⚛  Quantumn Hardware",
        "sdk":  "qudora-sdk",
        "sdk_import": "qudora_sdk",
        "install_cmd": "qudora-sdk",
        "description": "Trapped-ion quantum emulator from Qudora",
        "note": "Requires QUAPP_API_KEY",
    },
    {
        "key":  "2",
        "id":   "quandela",
        "name": "Perceval (photonic)",
        "type": "⚛  Quantumn Hardware",
        "sdk":  "perceval-quandela",
        "sdk_import": "perceval",
        "install_cmd": "perceval-quandela",
        "description": "Photonic quantum simulator from Quandela",
        "note": "Python 3.9 – 3.11",
    },
    {
        "key":  "3",
        "id":   "classical",
        "name": "Simulated Annealing",
        "type": "💻 Classical CPU",
        "sdk":  None,
        "sdk_import": None,
        "install_cmd": None,
        "description": "Classical optimization — no quantum SDK required",
        "note": "Always available",
    },
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def clr():
    os.system("cls" if os.name == "nt" else "clear")


def check_sdk(backend: dict) -> tuple[bool, str]:
    """Returns (available, status_string)"""
    if backend["sdk_import"] is None:
        return True, f"{C.GREEN}✅ Running {C.RESET}"
    try:
        mod = __import__(backend["sdk_import"])
        ver = getattr(mod, "__version__", None) or getattr(mod, "VERSION", None)
        ver_str = f" v{ver}" if ver else ""
        return True, f"{C.GREEN}✅ Running{ver_str}{C.RESET}"
    except ImportError:
        sdk_name = backend["sdk"]
        return False, f"{C.RED}❌ Need SDK {C.BOLD}{sdk_name}{C.RESET}{C.RED} — not installed{C.RESET}"


# ─── Display ──────────────────────────────────────────────────────────────────

def print_banner():
    w = 72
    print()
    print(f"{C.CYAN}{'═' * w}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}  ⚛  AML AI COPILOT  —  QUANTUM BACKEND SELECTOR{C.RESET}")
    print(f"{C.DIM}  SEA Quantathon 2026 · QCFinOp Team  |  Quapp.cloud Platform{C.RESET}")
    print(f"{C.CYAN}{'═' * w}{C.RESET}")


def print_backend_table(statuses: list[tuple[bool, str]]):
    """Print the backend table similar to the screenshot."""
    w = 72
    print()
    # Header
    print(f"  {C.BOLD}{C.GRAY}{'Backend':<10}  {'Name':<28}  {'Type':<20}  {'Status'}{C.RESET}")
    print(f"  {C.GRAY}{'─' * (w - 4)}{C.RESET}")

    for i, backend in enumerate(BACKENDS):
        is_avail, status_str = statuses[i]

        key_style = (
            f"{C.BG_GREEN}{C.WHITE}" if is_avail else f"{C.GRAY}"
        )
        id_cell   = f"{key_style}{backend['id']:<10}{C.RESET}"
        name_cell = f"{C.WHITE}{backend['name']:<28}{C.RESET}"
        type_cell = f"{C.CYAN}{backend['type']:<20}{C.RESET}"

        print(f"  {id_cell}  {name_cell}  {type_cell}  {status_str}")

    print(f"  {C.GRAY}{'─' * (w - 4)}{C.RESET}")


def print_choice_menu():
    print()
    print(f"  {C.BOLD}Choose the backend you want to use:{C.RESET}")
    for b in BACKENDS:
        sdk_note = f"  {C.DIM}({b['note']}){C.RESET}" if b["note"] else ""
        print(f"  {C.CYAN}[{b['key']}]{C.RESET} {C.BOLD}{b['id']:<12}{C.RESET}  {b['description']}{sdk_note}")
    print()


# ─── Backend Select ───────────────────────────────────────────────────────────

def select_backend(statuses: list[tuple[bool, str]]) -> BackendType:
    """Interactive backend selector. Returns selected backend id."""
    valid_keys = {b["key"]: b for b in BACKENDS}

    while True:
        raw = input(
            f"  Enter your choice (1/2/3) "
            f"[{C.BOLD}3{C.RESET} = classical default]: "
        ).strip()

        if raw == "":
            raw = "3"  # default classical

        if raw not in valid_keys:
            print(f"  {C.RED}❌ Please enter 1, 2 or 3{C.RESET}\n")
            continue

        selected = valid_keys[raw]
        is_avail, _ = statuses[BACKENDS.index(selected)]

        if not is_avail:
            sdk_name = selected["sdk"]
            print(f"\n  {C.YELLOW}⚠️  SDK '{sdk_name}' not installed.{C.RESET}")
            print(f"  {C.BOLD}Install now?{C.RESET} Run the following command:\n")
            print(f"    {C.CYAN}py -m pip install {selected['install_cmd']}{C.RESET}\n")

            install = input(f"  Install now? (y/n) [{C.BOLD}n{C.RESET}]: ").strip().lower()
            if install == "y":
                print(f"\n  {C.CYAN}📦 Installing {sdk_name}...{C.RESET}\n")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", selected["install_cmd"]],
                    capture_output=False,
                )
                if result.returncode == 0:
                    print(f"\n  {C.GREEN}✅ Installation successful!{C.RESET}")
                    return selected["id"]
                else:
                    print(f"\n  {C.RED}❌ Installation failed. Fallback to classical.{C.RESET}")
                    return "classical"
            else:
                print(f"\n  {C.YELLOW}⚠️  Fallback về Classical backend (Simulated Annealing).{C.RESET}")
                return "classical"

        return selected["id"]


# ─── .env Updater ─────────────────────────────────────────────────────────────

def update_env_file(backend_id: BackendType) -> bool:
    """Update QUANTUM_BACKEND in .env file"""
    env_path = Path(".env")

    if not env_path.exists():
        print(f"\n  {C.RED}❌ .env file does not exist!{C.RESET}")
        print(f"  → Create file: {C.BOLD}copy .env.example .env{C.RESET}")
        return False

    content = env_path.read_text(encoding="utf-8")
    pattern = r"^QUANTUM_BACKEND=.*$"
    replacement = f"QUANTUM_BACKEND={backend_id}"

    if re.search(pattern, content, re.MULTILINE):
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        new_content = content + f"\n{replacement}\n"

    env_path.write_text(new_content, encoding="utf-8")
    return True


# ─── Launch Menu ──────────────────────────────────────────────────────────────

def launch_menu(backend_id: BackendType):
    """Choose the application launch mode"""
    print()
    print(f"  {C.BOLD}{'═' * 64}{C.RESET}")
    print(f"  {C.GREEN}✅ Selected backend: {C.BOLD}[{backend_id.upper()}]{C.RESET}")
    print(f"  {C.BOLD}{'═' * 64}{C.RESET}")
    print()
    print(f"  {C.BOLD}Choose the application launch mode:{C.RESET}")
    print(f"  {C.CYAN}[1]{C.RESET} {C.BOLD}Web UI{C.RESET}     — Server + web interface  {C.DIM}http://localhost:7860{C.RESET}")
    print(f"  {C.CYAN}[2]{C.RESET} {C.BOLD}CLI Demo{C.RESET}   — Run quick_start.py to test pipeline")
    print(f"  {C.CYAN}[3]{C.RESET} {C.BOLD}QUBO Sim{C.RESET}   — Run DEMOCORE simulation standalone")
    print(f"  {C.CYAN}[4]{C.RESET} {C.BOLD}Exit{C.RESET}      — Only save backend, do not run anything")
    print()

    choice = input(
        f"  Enter your choice (1/2/3/4) [{C.BOLD}1{C.RESET} = Web UI]: "
    ).strip()

    if choice == "" or choice == "1":
        print(f"\n  {C.CYAN}🚀 Starting Web Server...{C.RESET}")
        print(f"  {C.DIM}→ Open browser at: http://localhost:8000{C.RESET}\n")
        subprocess.run([sys.executable, "server.py"])

    elif choice == "2":
        print(f"\n  {C.CYAN}🧪 Run Quick Start Test...{C.RESET}\n")
        subprocess.run([sys.executable, "quick_start.py"])

    elif choice == "3":
        print(f"\n  {C.CYAN}📊 Starting QUBO Simulation...{C.RESET}\n")
        demo_script = Path("DEMOCORE/03_qubo_sim.py")
        if demo_script.exists():
            subprocess.run([sys.executable, str(demo_script)])
        else:
            print(f"  {C.RED}❌ Could not find DEMOCORE/03_qubo_sim.py{C.RESET}")

    elif choice == "4":
        print(f"\n  {C.GREEN}✅ Saved backend. Exiting.{C.RESET}")

    else:
        print(f"\n  {C.RED}❌ Invalid choice. Exiting.{C.RESET}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    clr()
    print_banner()

    # Check SDK availability cho tất cả backends
    print(f"\n  {C.DIM}Checking SDK availability...{C.RESET}", end="\r")
    statuses = [check_sdk(b) for b in BACKENDS]
    print(" " * 50, end="\r")  # clear the checking line

    # Show backend table
    print_backend_table(statuses)

    # Show choice menu
    print_choice_menu()

    # Get user choice
    selected_backend = select_backend(statuses)

    # Update .env
    print(f"\n  {C.CYAN}📝 Updating .env file...{C.RESET}", end=" ")
    ok = update_env_file(selected_backend)
    print(f"{C.GREEN}Done!{C.RESET}" if ok else f"{C.RED}Failed{C.RESET}")

    # Launch app
    launch_menu(selected_backend)

    # Footer
    print()
    print(f"{C.CYAN}{'═' * 72}{C.RESET}")
    print(f"  {C.GREEN}✨ Thank you for using AML AI Copilot!{C.RESET}")
    print(f"{C.CYAN}{'═' * 72}{C.RESET}")
    print()


if __name__ == "__main__":
    main()
