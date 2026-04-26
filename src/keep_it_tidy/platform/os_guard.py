import platform


def os_guard() -> None:
    system = platform.system()
    if system != "Linux":
        raise RuntimeError(
            f"keep-it-tidy only supports Linux, but detected: {system}"
        )
