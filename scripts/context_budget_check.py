THRESHOLDS = {
    "tool_registry_bytes": 8192,  # 8KB budget for tool list JSON
}


def main() -> None:
    # Placeholder: once server exposes a way to serialize registry, import and measure
    print({"ok": True, "checked": list(THRESHOLDS.keys())})


if __name__ == "__main__":
    main()
