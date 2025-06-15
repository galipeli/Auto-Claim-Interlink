import requests
import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class InterlinkAutoClaim:
    def __init__(self):
        self.base_url = "https://prod.interlinklabs.ai/api/v1"
        self.accounts = self.load_accounts()
        self.running = True

    def load_accounts(self):
        """Load accounts from .env file"""
        login_ids = os.getenv('LOGIN_IDS', '').split(',')
        passcodes = os.getenv('PASS_CODES', '').split(',')
        emails = os.getenv('EMAILS', '').split(',')
        
        accounts = []
        for i in range(min(len(login_ids), len(passcodes), len(emails))):
            accounts.append({
                'login_id': login_ids[i].strip(),
                'passcode': passcodes[i].strip(),
                'email': emails[i].strip(),
                'token_file': f'token_{i}.txt'
            })
        return accounts

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_menu(self):
        self.clear_screen()
        print("=== INTERLINK AUTOCLAIM ===")
        print(f"Total Akun: {len(self.accounts)}")
        print("\nMenu:")
        print("1. Dapatkan Token Baru")
        print("2. Jalankan Auto Claim")
        print("3. Cek Saldo Poin")
        print("4. Keluar")
        choice = input("\nPilih menu: ")
        return choice

    def get_token(self, account):
        """Get new token via OTP"""
        print(f"\nMengambil token untuk {account['email']}")
        
        # Send OTP
        otp_url = f"{self.base_url}/auth/send-otp-email-verify-login"
        payload = {
            "loginId": account['login_id'],
            "passcode": account['passcode'],
            "email": account['email']
        }
        response = requests.post(otp_url, json=payload)
        
        if response.status_code != 200:
            print("Gagal mengirim OTP")
            return False

        otp = input("Masukkan OTP dari email: ")
        
        # Verify OTP
        verify_url = f"{self.base_url}/auth/check-otp-email-verify-login"
        payload = {
            "loginId": account['login_id'],
            "otp": otp
        }
        response = requests.post(verify_url, json=payload)
        
        if response.status_code == 200:
            token = response.json()['data']['jwtToken']
            with open(account['token_file'], 'w') as f:
                f.write(token)
            print("Token berhasil disimpan!")
            return True
        else:
            print("OTP tidak valid")
            return False

    def load_token(self, account):
        """Load token from file"""
        try:
            with open(account['token_file'], 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            return None

    def check_claimable(self, token):
        """Check claim status"""
        url = f"{self.base_url}/token/check-is-claimable"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None

    def claim_airdrop(self, token):
        """Claim airdrop"""
        url = f"{self.base_url}/token/claim-airdrop"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(url, headers=headers)
        return response.json()

    def get_points(self, token):
        """Get account points"""
        url = f"{self.base_url}/token/get-token"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else None

    def format_time(self, seconds):
        """Format waktu countdown"""
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def run_auto_claim(self):
        """Main auto claim process"""
        while self.running:
            try:
                print("\n" + "="*50)
                print(f"Memulai proses pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                for account in self.accounts:
                    token = self.load_token(account)
                    if not token:
                        print(f"\nToken tidak ditemukan untuk {account['email']}")
                        continue
                    
                    print(f"\nAkun: {account['email']}")
                    
                    # Check points
                    points_info = self.get_points(token)
                    if points_info:
                        print(f"Poin: {points_info['data']['interlinkGoldTokenAmount']}")
                    
                    # Check claim status
                    claim_status = self.check_claimable(token)
                    if not claim_status:
                        print("Gagal cek status claim")
                        continue
                        
                    if claim_status['data']['isClaimable']:
                        print("Mencoba claim...")
                        result = self.claim_airdrop(token)
                        print(f"Hasil: {result['message']}")
                    else:
                        wait_time = (claim_status['data']['nextFrame'] - int(time.time()*1000)) // 1000
                        print(f"Tunggu {self.format_time(wait_time)} jam lagi")
                
                # Countdown 4 jam
                print("\n" + "="*50)
                print("Menunggu 4 jam untuk claim berikutnya...")
                for remaining in range(14400, 0, -1):
                    print(f"Next claim in: {self.format_time(remaining)}", end='\r')
                    time.sleep(1)
                    if not self.running:
                        break
                        
            except KeyboardInterrupt:
                self.running = False
                print("\nDihentikan oleh user")

    def run(self):
        """Main application loop"""
        while self.running:
            choice = self.show_menu()
            
            if choice == '1':
                self.clear_screen()
                print("== DAPATKAN TOKEN BARU ==\n")
                for i, account in enumerate(self.accounts):
                    print(f"{i+1}. {account['email']}")
                selected = input("\nPilih akun (0 untuk semua): ")
                
                if selected == '0':
                    for account in self.accounts:
                        self.get_token(account)
                else:
                    try:
                        idx = int(selected) - 1
                        if 0 <= idx < len(self.accounts):
                            self.get_token(self.accounts[idx])
                    except ValueError:
                        print("Pilihan tidak valid")
                input("\nTekan Enter untuk kembali...")
                
            elif choice == '2':
                self.run_auto_claim()
                
            elif choice == '3':
                self.clear_screen()
                print("== CEK SALDO POIN ==\n")
                for account in self.accounts:
                    token = self.load_token(account)
                    if token:
                        points_info = self.get_points(token)
                        if points_info:
                            print(f"{account['email']}: {points_info['data']['interlinkGoldTokenAmount']} poin")
                        else:
                            print(f"{account['email']}: Gagal cek poin")
                    else:
                        print(f"{account['email']}: Token tidak ditemukan")
                input("\nTekan Enter untuk kembali...")
                
            elif choice == '4':
                self.running = False
                
            else:
                print("Menu tidak valid")
                time.sleep(1)

if __name__ == "__main__":
    app = InterlinkAutoClaim()
    app.run()
