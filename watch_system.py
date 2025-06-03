#!/usr/bin/env python3
"""
Real-Time System Monitor for Loopy-Munch Integration
====================================================

Watch the system in real-time while testing with 12 coffees.
This script shows live updates of:
- Customer sync status
- Credit applications
- System health
- Recent activity

Perfect to run while loading 12 coffees to see everything happen live!
"""

import sys
import os
import time
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List
import requests
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv('production.env')

class LiveSystemMonitor:
    """Real-time monitoring of the Loopy-Munch integration system"""
    
    def __init__(self):
        self.munch_base_url = os.getenv('MUNCH_BASE_URL', 'https://api.munch.cloud/api')
        self.munch_api_key = os.getenv('MUNCH_API_KEY')
        self.munch_headers = {
            'Authorization': f'Bearer {self.munch_api_key}',
            'Content-Type': 'application/json'
        }
        
        print("👁️ LIVE SYSTEM MONITOR STARTED")
        print("=" * 50)
        print("Monitoring Loopy-Munch integration in real-time...")
        print("Press Ctrl+C to stop monitoring")
        print()
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_sync_stats(self):
        """Get current sync statistics"""
        try:
            if not os.path.exists("bilateral_sync_tracker.db"):
                return None
                
            conn = sqlite3.connect("bilateral_sync_tracker.db")
            cursor = conn.cursor()
            
            # Get total customers synced
            cursor.execute("SELECT COUNT(*) FROM customer_sync")
            total_customers = cursor.fetchone()[0]
            
            # Get total credits applied
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(credit_amount), 0) FROM credit_sync")
            credit_count, credit_total = cursor.fetchone()
            
            # Get last sync time
            cursor.execute("SELECT MAX(completed_at) FROM sync_history WHERE status = 'completed'")
            last_sync = cursor.fetchone()[0]
            
            # Get recent activity (last 10 minutes)
            ten_minutes_ago = (datetime.now() - timedelta(minutes=10)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM credit_sync 
                WHERE applied_at > ?
            """, (ten_minutes_ago,))
            recent_credits = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_customers': total_customers,
                'credit_count': credit_count,
                'credit_total': credit_total,
                'last_sync': last_sync,
                'recent_credits': recent_credits
            }
        except Exception as e:
            return None
    
    def get_munch_stats(self):
        """Get current Munch system statistics"""
        try:
            # Use the working POST endpoint instead of GET
            munch_headers = {
                'Authorization': f'Bearer {self.munch_api_key}',
                'Authorization-Type': 'internal',
                'Content-Type': 'application/json',
                'Locale': 'en',
                'Munch-Platform': 'cloud.munch.portal',
                'Munch-Timezone': 'Africa/Johannesburg',
                'Munch-Version': '2.20.1',
                'Munch-Employee': '28c5e780-3707-11ec-bb31-dde416ab9f61',
                'Munch-Organisation': '1476d7a5-b7b2-4b18-85c6-33730cf37a12'
            }
            
            payload = {
                "id": "3e92a480-5f21-11ec-b43f-dde416ab9f61",
                "timezone": "Africa/Johannesburg"
            }
            
            response = requests.post(
                f"{self.munch_base_url}/account/retrieve-users",
                headers=munch_headers,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                users = response.json()
                total_customers = len(users)
                total_balance = sum(user.get('accounts', [{}])[0].get('accountUser', {}).get('balance', 0) / 100 for user in users if user.get('accounts'))
                customers_with_balance = len([u for u in users if u.get('accounts') and u['accounts'][0].get('accountUser', {}).get('balance', 0) > 0])
                
                return {
                    'total_customers': total_customers,
                    'total_balance': total_balance,
                    'customers_with_balance': customers_with_balance,
                    'api_status': 'connected'
                }
            else:
                return {'api_status': 'error', 'status_code': response.status_code}
        except Exception as e:
            return {'api_status': 'disconnected', 'error': str(e)}
    
    def get_recent_activity(self):
        """Get recent system activity"""
        try:
            if not os.path.exists("bilateral_sync_tracker.db"):
                return []
                
            conn = sqlite3.connect("bilateral_sync_tracker.db")
            cursor = conn.cursor()
            
            # Get recent credits (last 5)
            cursor.execute("""
                SELECT loyalty_code, credit_amount, reference, applied_at
                FROM credit_sync 
                ORDER BY applied_at DESC
                LIMIT 5
            """)
            
            recent_credits = []
            for row in cursor.fetchall():
                loyalty_code, amount, reference, applied = row
                recent_credits.append({
                    'type': 'credit',
                    'loyalty_code': loyalty_code,
                    'amount': amount,
                    'time': applied
                })
            
            # Get recent customer syncs (last 5)
            cursor.execute("""
                SELECT loyalty_code, customer_name, last_synced
                FROM customer_sync 
                ORDER BY last_synced DESC
                LIMIT 5
            """)
            
            recent_syncs = []
            for row in cursor.fetchall():
                loyalty_code, name, synced = row
                recent_syncs.append({
                    'type': 'sync',
                    'loyalty_code': loyalty_code,
                    'name': name,
                    'time': synced
                })
            
            conn.close()
            
            # Combine and sort by time
            all_activity = recent_credits + recent_syncs
            all_activity.sort(key=lambda x: x['time'], reverse=True)
            
            return all_activity[:10]
            
        except Exception as e:
            return []
    
    def check_service_status(self):
        """Check if bilateral sync service is running"""
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and 'bilateral_sync' in ' '.join(proc.info['cmdline']):
                        return {'status': 'running', 'pid': proc.info['pid']}
                except:
                    continue
            return {'status': 'not_running'}
        except ImportError:
            # If psutil not available, try checking log file modification time
            try:
                if os.path.exists('bilateral_sync.log'):
                    mod_time = os.path.getmtime('bilateral_sync.log')
                    if time.time() - mod_time < 300:  # Modified in last 5 minutes
                        return {'status': 'possibly_running'}
                return {'status': 'unknown'}
            except:
                return {'status': 'unknown'}
    
    def display_status(self):
        """Display current system status"""
        self.clear_screen()
        
        now = datetime.now().strftime("%H:%M:%S")
        
        print("👁️ LIVE LOOPY-MUNCH SYSTEM MONITOR")
        print("=" * 60)
        print(f"🕐 Last Update: {now}")
        print()
        
        # Service Status
        service_status = self.check_service_status()
        print("🔧 SERVICE STATUS:")
        print("-" * 20)
        if service_status['status'] == 'running':
            print(f"✅ Bilateral Sync: Running (PID: {service_status['pid']})")
        elif service_status['status'] == 'possibly_running':
            print("🟡 Bilateral Sync: Possibly running (recent log activity)")
        else:
            print("❌ Bilateral Sync: Not detected")
        print()
        
        # Sync Statistics
        sync_stats = self.get_sync_stats()
        print("📊 SYNC STATISTICS:")
        print("-" * 20)
        if sync_stats:
            print(f"👥 Total Customers: {sync_stats['total_customers']}")
            print(f"💰 Credits Applied: {sync_stats['credit_count']}")
            print(f"💵 Total Credit Amount: R{sync_stats['credit_total']:.2f}")
            print(f"⚡ Recent Credits (10min): {sync_stats['recent_credits']}")
            if sync_stats['last_sync']:
                last_sync_time = sync_stats['last_sync'][:19]
                print(f"🔄 Last Sync: {last_sync_time}")
            else:
                print("🔄 Last Sync: Never")
        else:
            print("❌ No sync data available")
        print()
        
        # Munch API Status
        munch_stats = self.get_munch_stats()
        print("💳 MUNCH SYSTEM:")
        print("-" * 20)
        if munch_stats['api_status'] == 'connected':
            print(f"✅ API Status: Connected")
            print(f"👥 Total Customers: {munch_stats['total_customers']}")
            print(f"💰 Total Balances: R{munch_stats['total_balance']:.2f}")
            print(f"🎁 Customers with Credits: {munch_stats['customers_with_balance']}")
        elif munch_stats['api_status'] == 'error':
            print(f"⚠️ API Status: Error ({munch_stats['status_code']})")
        else:
            print(f"❌ API Status: Disconnected")
        print()
        
        # Recent Activity
        recent_activity = self.get_recent_activity()
        print("📝 RECENT ACTIVITY:")
        print("-" * 20)
        if recent_activity:
            for activity in recent_activity[:5]:
                time_str = activity['time'][:19] if activity['time'] else 'Unknown'
                if activity['type'] == 'credit':
                    print(f"💰 {time_str}: R{activity['amount']:.2f} credit → {activity['loyalty_code']}")
                elif activity['type'] == 'sync':
                    name = activity['name'][:20] if activity['name'] else 'Unknown'
                    print(f"🔄 {time_str}: Synced {name} ({activity['loyalty_code']})")
        else:
            print("ℹ️ No recent activity")
        print()
        
        print("💡 WATCHING FOR YOUR 12 COFFEES...")
        print("When you load 12 coffees, you should see:")
        print("  ✅ Customer sync activity")
        print("  ✅ R40 credit application")
        print("  ✅ Balance update in Munch")
        print()
        print("Press Ctrl+C to stop monitoring")
    
    def run(self, refresh_interval=5):
        """Run the live monitor"""
        try:
            while True:
                self.display_status()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print("\n\n👋 Live monitoring stopped.")
            print("System continues running in background.")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Live System Monitor for Loopy-Munch Integration')
    parser.add_argument('--interval', '-i', type=int, default=5, help='Refresh interval in seconds (default: 5)')
    parser.add_argument('--once', action='store_true', help='Show status once and exit')
    
    args = parser.parse_args()
    
    monitor = LiveSystemMonitor()
    
    if args.once:
        monitor.display_status()
    else:
        monitor.run(args.interval)

if __name__ == "__main__":
    main() 