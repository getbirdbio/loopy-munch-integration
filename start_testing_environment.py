#!/usr/bin/env python3
"""
Start Testing Environment
=========================

Prepare the Loopy-Munch integration system for end-to-end testing.
This script ensures all services are running and ready for testing.
"""

import sys
import os
import subprocess
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('production.env')

class TestingEnvironmentManager:
    """Manages the testing environment setup"""
    
    def __init__(self):
        self.munch_base_url = os.getenv('MUNCH_BASE_URL', 'https://api.munch.cloud/api')
        self.munch_api_key = os.getenv('MUNCH_API_KEY')
        self.munch_headers = {
            'Authorization': f'Bearer {self.munch_api_key}',
            'Content-Type': 'application/json'
        }
        
        print("🚀 STARTING TESTING ENVIRONMENT")
        print("=" * 50)
    
    def check_prerequisites(self):
        """Check that all prerequisites are in place"""
        print("🔍 Checking prerequisites...")
        
        prerequisites = []
        
        # Check environment variables
        required_vars = [
            'LOOPY_API_KEY', 'LOOPY_API_SECRET', 'LOOPY_USERNAME',
            'MUNCH_API_KEY', 'MUNCH_ORGANIZATION_ID'
        ]
        
        for var in required_vars:
            if os.getenv(var):
                prerequisites.append(f"✅ {var}")
            else:
                prerequisites.append(f"❌ {var} - Missing")
        
        # Check required files
        required_files = [
            'loopy_munch_bilateral_sync.py',
            'monitor_bilateral_sync.py',
            'end_to_end_test.py',
            'watch_system.py'
        ]
        
        for file in required_files:
            if os.path.exists(file):
                prerequisites.append(f"✅ {file}")
            else:
                prerequisites.append(f"❌ {file} - Missing")
        
        for prereq in prerequisites:
            print(f"   {prereq}")
        
        missing = [p for p in prerequisites if p.startswith('❌')]
        if missing:
            print(f"\n❌ {len(missing)} prerequisites missing. Please fix before continuing.")
            return False
        
        print("\n✅ All prerequisites satisfied!")
        return True
    
    def test_api_connections(self):
        """Test API connections to both Loopy and Munch"""
        print("\n🔗 Testing API connections...")
        
        # Test Munch API
        try:
            response = requests.get(
                f"{self.munch_base_url}/customers",
                headers=self.munch_headers,
                timeout=10
            )
            if response.status_code == 200:
                customers = response.json()
                print(f"✅ Munch API: Connected ({len(customers)} customers)")
            else:
                print(f"⚠️ Munch API: Error {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Munch API: Connection failed - {e}")
            return False
        
        # Test Loopy API (via our sync engine)
        try:
            from loopy_munch_bilateral_sync import LoopyCustomerAPI
            
            loopy_api = LoopyCustomerAPI(
                api_key=os.getenv('LOOPY_API_KEY'),
                api_secret=os.getenv('LOOPY_API_SECRET'),
                username=os.getenv('LOOPY_USERNAME')
            )
            
            if loopy_api.auth_token:
                print("✅ Loopy API: Connected and authenticated")
            else:
                print("❌ Loopy API: Authentication failed")
                return False
                
        except Exception as e:
            print(f"❌ Loopy API: Connection failed - {e}")
            return False
        
        return True
    
    def ensure_sync_service(self):
        """Ensure the bilateral sync service is ready"""
        print("\n🔄 Checking bilateral sync service...")
        
        # Check if database exists
        if not os.path.exists("bilateral_sync_tracker.db"):
            print("📋 Creating sync tracking database...")
            try:
                from loopy_munch_bilateral_sync import SyncTracker
                tracker = SyncTracker()
                print("✅ Sync database created")
            except Exception as e:
                print(f"❌ Failed to create sync database: {e}")
                return False
        else:
            print("✅ Sync database exists")
        
        # Test sync functionality
        try:
            print("🧪 Testing sync functionality...")
            from loopy_munch_bilateral_sync import BilateralSyncEngine
            
            sync_engine = BilateralSyncEngine()
            print("✅ Sync engine initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Sync engine test failed: {e}")
            return False
    
    def start_monitoring(self):
        """Offer to start monitoring"""
        print("\n👁️ Starting system monitoring...")
        
        print("You can now monitor the system in real-time using:")
        print("   python watch_system.py")
        print()
        print("Or run the comprehensive test with:")
        print("   python end_to_end_test.py")
        print()
        
        response = input("Start live monitoring now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            try:
                subprocess.run([sys.executable, 'watch_system.py'], check=True)
            except KeyboardInterrupt:
                print("\nMonitoring stopped.")
            except Exception as e:
                print(f"Error starting monitor: {e}")
    
    def show_testing_instructions(self):
        """Show testing instructions"""
        print("\n📋 TESTING INSTRUCTIONS")
        print("=" * 50)
        print()
        print("🎯 YOUR SYSTEM IS READY FOR TESTING!")
        print()
        print("To test with 12 coffees:")
        print()
        print("1️⃣ Open a second terminal and run the live monitor:")
        print("   python watch_system.py")
        print()
        print("2️⃣ Load 12 coffees onto your Loopy account")
        print("   (This should trigger 1 free coffee = R40 credit)")
        print()
        print("3️⃣ Watch the monitor for:")
        print("   ✅ Customer sync activity")
        print("   ✅ Credit application (R40)")
        print("   ✅ Munch balance update")
        print()
        print("4️⃣ Run comprehensive test to validate:")
        print("   python end_to_end_test.py --customer YOUR_CUSTOMER_CODE")
        print()
        print("5️⃣ Test transaction flow:")
        print("   - Customer scans loyalty code at POS")
        print("   - R40 credit should be applied")
        print("   - Coffee becomes FREE!")
        print()
        print("🚨 EXPECTED BEHAVIOR:")
        print("   12 coffees → 1 free coffee → R40 Munch credit")
        print("   When customer buys coffee → Credit applied → FREE!")
        print()
        print("✅ Everything is configured and ready to go!")
    
    def run(self):
        """Run the full environment setup"""
        if not self.check_prerequisites():
            return False
        
        if not self.test_api_connections():
            return False
        
        if not self.ensure_sync_service():
            return False
        
        self.show_testing_instructions()
        
        # Offer to start monitoring
        self.start_monitoring()
        
        return True

def main():
    """Main function"""
    manager = TestingEnvironmentManager()
    
    success = manager.run()
    
    if success:
        print("\n🎉 Testing environment ready!")
        print("Load your 12 coffees and let's see the magic happen!")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 