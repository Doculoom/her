import requests

API_URL = "http://localhost:8000"  # Adjust if using a different host/port


def main():
    user_id = input("Enter user ID: ")

    print("\nType your messages below. Type 'quit' or press Ctrl+C to exit.\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            print("Exiting chat.")
            break

        payload = {"user_id": user_id, "text": user_input}

        try:
            response = requests.post(f"{API_URL}/send_message", json=payload)
            response.raise_for_status()
            data = response.json()
            print("Gemini:", data["model_response"])
        except requests.exceptions.RequestException as e:
            print("Error while sending message:", e)
            break


if __name__ == "__main__":
    main()
