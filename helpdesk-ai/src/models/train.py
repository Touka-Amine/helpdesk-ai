"""Training entry point."""

from pathlib import Path


def train(output_dir: str) -> Path:
    """Placeholder training routine."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    model_file = out_path / "model.pkl"
    model_file.write_text("placeholder model")
    return model_file


if __name__ == "__main__":
    train("models")
