"""
travel_assistant.py
--------------------
Margie's Travel AI-Powered Virtual Assistant — CLI interface.

Run setup_vector_store.py first to create the vector store, then:
    python travel_assistant.py
"""

from core import (
    DEPLOYMENT,
    SYSTEM_PROMPT,
    VECTOR_STORE_ID,
    build_tools,
    get_sync_client,
)


# ---------------------------------------------------------------------------
# Main conversation loop
# ---------------------------------------------------------------------------
def run_assistant() -> None:
    client = get_sync_client()
    tools = build_tools()

    print()
    print("=" * 60)
    print("  Welcome to Margie's Travel Assistant! ✈")
    print("=" * 60)
    print(
        "Ask me anything about destinations, hotels, activities,\n"
        "or travel packages. Type 'quit' or 'exit' to leave.\n"
    )
    if VECTOR_STORE_ID:
        print(f"[Brochure search active — Vector Store: {VECTOR_STORE_ID}]")
    print("[Web search active — real-time information enabled]")
    print()

    previous_response_id: str | None = None

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nThank you for choosing Margie's Travel. Bon voyage!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit", "q", "bye"}:
            print("\nThank you for choosing Margie's Travel. Bon voyage!")
            break

        try:
            # Build request parameters
            params: dict = {
                "model": DEPLOYMENT,
                "instructions": SYSTEM_PROMPT,
                "input": user_input,
                "tools": tools,
            }

            # Attach the previous response ID to maintain conversation context
            if previous_response_id:
                params["previous_response_id"] = previous_response_id

            response = client.responses.create(**params)

            # Update conversation context for the next turn
            previous_response_id = response.id

            reply = response.output_text or "(no response)"
            print(f"\nAssistant: {reply}\n")

        except Exception as exc:  # noqa: BLE001
            print(f"\n[Error] {exc}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_assistant()
