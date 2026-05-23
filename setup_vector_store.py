"""
setup_vector_store.py
---------------------
Creates an Azure OpenAI vector store from Margie's Travel brochures
and writes the resulting VECTOR_STORE_ID to the .env file.

Run this script once before launching travel_assistant.py.
"""

import os
import glob
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv, set_key

load_dotenv()

BROCHURES_DIR = Path(__file__).parent / "brochures"
ENV_FILE = Path(__file__).parent / ".env"


def normalize_endpoint(endpoint: str) -> str:
    """Strip the /openai/v1 path suffix added by some Foundry endpoint URLs."""
    for suffix in ("/openai/v1", "/openai/v1/"):
        if endpoint.endswith(suffix):
            return endpoint[: -len(suffix)]
    return endpoint.rstrip("/")


def get_client() -> AzureOpenAI:
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()

    if not endpoint or not api_key:
        raise ValueError(
            "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set in .env"
        )

    return AzureOpenAI(
        azure_endpoint=normalize_endpoint(endpoint),
        api_key=api_key,
        api_version="2025-04-01-preview",
    )


def upload_brochures(client: AzureOpenAI) -> list[str]:
    """Upload all .txt brochure files and return their file IDs."""
    brochure_paths = glob.glob(str(BROCHURES_DIR / "*.txt"))

    if not brochure_paths:
        raise FileNotFoundError(f"No .txt brochure files found in {BROCHURES_DIR}")

    file_ids = []
    for path in brochure_paths:
        print(f"  Uploading {Path(path).name}...")
        with open(path, "rb") as f:
            response = client.files.create(file=f, purpose="assistants")
        file_ids.append(response.id)
        print(f"    -> File ID: {response.id}")

    return file_ids


def create_vector_store(client: AzureOpenAI, file_ids: list[str]) -> str:
    """Create a vector store, attach the uploaded files, and return the store ID."""
    print("\nCreating vector store...")
    vector_store = client.vector_stores.create(
        name="Margies Travel Brochures",
        file_ids=file_ids,
    )
    print(f"  Vector Store ID: {vector_store.id}")
    print(f"  Status: {vector_store.status}")
    return vector_store.id


def save_vector_store_id(vector_store_id: str) -> None:
    """Persist the vector store ID to .env so travel_assistant.py can read it."""
    set_key(str(ENV_FILE), "VECTOR_STORE_ID", vector_store_id)
    print(f"\nVECTOR_STORE_ID saved to {ENV_FILE}")


def main() -> None:
    print("=" * 55)
    print("  Margie's Travel — Vector Store Setup")
    print("=" * 55)

    # Check if a vector store ID already exists
    existing_id = os.environ.get("VECTOR_STORE_ID", "").strip()
    if existing_id:
        print(f"\nExisting VECTOR_STORE_ID found: {existing_id}")
        answer = input("Create a new vector store anyway? [y/N]: ").strip().lower()
        if answer != "y":
            print("Setup skipped. Using existing vector store.")
            return

    client = get_client()

    print(f"\nUploading brochures from: {BROCHURES_DIR}")
    file_ids = upload_brochures(client)
    print(f"\nUploaded {len(file_ids)} file(s).")

    vector_store_id = create_vector_store(client, file_ids)
    save_vector_store_id(vector_store_id)

    print("\nSetup complete! You can now run travel_assistant.py.")


if __name__ == "__main__":
    main()
