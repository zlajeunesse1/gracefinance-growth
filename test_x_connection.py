from x_client import verify_x_connection


if __name__ == "__main__":
    try:
        account = verify_x_connection()
        print("X authentication successful")
        print(f"Account: @{account['username']}")
        print(f"Name: {account['name']}")
    except Exception as exc:
        print(f"X authentication failed: {type(exc).__name__}: {exc}")
        raise SystemExit(1)
