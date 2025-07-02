import requests

BASE_URL = "https://api.classplusapp.com"

headers = {
    "User-Agent": "ClassplusApp/1.4.39 (Android 11; SDK 30)",
    "Content-Type": "application/json"
}

def send_otp(email):
    url = f"{BASE_URL}/v2/customer/sendAppOtpEmail"
    data = {
        "email": email
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("[+] OTP Sent successfully to email.")
    else:
        print("[-] Failed to send OTP.")
        print(response.text)

def verify_otp(email, otp):
    url = f"{BASE_URL}/v2/customer/verifyAppOtpEmail"
    data = {
        "email": email,
        "otp": otp
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        json_data = response.json()
        token = json_data.get("data", {}).get("accessToken")
        if token:
            print("[+] Token generated successfully:")
            print(token)
            return token
        else:
            print("[-] Token not found in response.")
    else:
        print("[-] OTP Verification Failed.")
        print(response.text)

def main():
    email = input("Enter your email: ")
    send_otp(email)

    otp = input("Enter the OTP sent to your email: ")
    token = verify_otp(email, otp)

    if token:
        with open("classplus_token.txt", "w") as f:
            f.write(token)
        print("[+] Token saved to classplus_token.txt")

if __name__ == "__main__":
    main()
