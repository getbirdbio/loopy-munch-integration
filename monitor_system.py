#!/usr/bin/env python3
"""
Real-Time System Monitor
=======================

Monitor the Loopy-Make.com integration system in real time.
Shows logs, system status, and allows sending test webhooks.
"""

import subprocess
import time
import requests
import json
from datetime import datetime
import os
import threading
from queue import Queue

class SystemMonitor:
    def __init__(self):
        self.base_url = "http://localhost:5008"
        self.domain_url = "https://api.getbird.co.za"
        self.log_file = "service_logs.txt"
        self.running = True
        
    def get_service_status(self):
        """Check if the service is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=2)
            return "🟢 RUNNING" if response.status_code == 200 else "🟡 ISSUES"
        except:
            return "🔴 STOPPED"
    
    def get_domain_status(self):
        """Check if the domain is accessible"""
        try:
            response = requests.get(f"{self.domain_url}/health", timeout=3)
            return "🟢 ONLINE" if response.status_code == 200 else "🟡 ISSUES"
        except:
            return "🔴 OFFLINE"
    
    def tail_logs(self, lines=10):
        """Get recent log entries"""
        try:
            if os.path.exists(self.log_file):
                result = subprocess.run(['tail', f'-{lines}', self.log_file], 
                                      capture_output=True, text=True)
                return result.stdout.strip()
            return "No logs available"
        except:
            return "Error reading logs"
    
    def send_test_webhook(self, webhook_type="enrolled"):
        """Send a test webhook and return response"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        if webhook_type == "enrolled":
            data = {
                "event": "card.enrolled",
                "timestamp": timestamp,
                "card": {
                    "id": f"monitor_test_{int(time.time())}",
                    "totalStampsEarned": 0,
                    "customerDetails": {
                        "Name": "Monitor Test Customer",
                        "Email address": "monitor@test.com"
                    }
                }
            }
            endpoint = f"{self.domain_url}/webhook/loopy/enrolled"
        
        elif webhook_type == "stamp":
            data = {
                "event": "card.stamped", 
                "timestamp": timestamp,
                "card": {
                    "id": f"monitor_stamp_{int(time.time())}",
                    "totalStampsEarned": 7,
                    "customerDetails": {
                        "Name": "Monitor Stamp Test",
                        "Email address": "stamp@test.com"
                    }
                }
            }
            endpoint = f"{self.domain_url}/webhook/loopy/stamp"
        
        try:
            response = requests.post(endpoint, json=data, timeout=5)
            return {
                "status": response.status_code,
                "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "success": 200 <= response.status_code < 300
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def print_status_line(self):
        """Print a single status line"""
        local = self.get_service_status()
        domain = self.get_domain_status()
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        print(f"\r🕐 {timestamp} | Local: {local} | Domain: {domain} | Press Ctrl+C to stop", end="", flush=True)

    def interactive_monitor(self):
        """Interactive monitoring mode"""
        print("🔍 REAL-TIME SYSTEM MONITOR")
        print("=" * 50)
        print("Commands:")
        print("  ENTER  - Refresh status")
        print("  'test' - Send test enrollment webhook") 
        print("  'stamp' - Send test stamp webhook")
        print("  'logs' - Show recent logs")
        print("  'quit' - Exit monitor")
        print("=" * 50)
        
        while self.running:
            try:
                # Show current status
                local_status = self.get_service_status()
                domain_status = self.get_domain_status()
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n🕐 {timestamp}")
                print(f"Local Service:  {local_status}")
                print(f"Domain Access:  {domain_status}")
                
                # Get user input with timeout
                print("\nCommand (or Enter for refresh): ", end="", flush=True)
                
                # Simple input handling
                try:
                    cmd = input().strip().lower()
                    
                    if cmd == 'quit' or cmd == 'q':
                        break
                    elif cmd == 'test':
                        print("\n🧪 Sending test enrollment webhook...")
                        result = self.send_test_webhook("enrolled")
                        if result.get('success'):
                            print(f"✅ Success: {result['status']}")
                            print(f"Response: {json.dumps(result['response'], indent=2)}")
                        else:
                            print(f"❌ Failed: {result}")
                    
                    elif cmd == 'stamp':
                        print("\n📍 Sending test stamp webhook...")
                        result = self.send_test_webhook("stamp")
                        if result.get('success'):
                            print(f"✅ Success: {result['status']}")
                            print(f"Response: {json.dumps(result['response'], indent=2)}")
                        else:
                            print(f"❌ Failed: {result}")
                    
                    elif cmd == 'logs':
                        print("\n📋 Recent Logs:")
                        print("-" * 40)
                        logs = self.tail_logs(15)
                        print(logs)
                        print("-" * 40)
                    
                    elif cmd == '':
                        # Just refresh status
                        continue
                    
                    else:
                        print(f"Unknown command: {cmd}")
                
                except KeyboardInterrupt:
                    break
                    
            except KeyboardInterrupt:
                break
        
        print("\n\n👋 Monitor stopped.")

if __name__ == "__main__":
    monitor = SystemMonitor()
    
    # Quick status check first
    print("🔍 SYSTEM STATUS CHECK")
    print("=" * 30)
    print(f"Local Service:  {monitor.get_service_status()}")
    print(f"Domain Access:  {monitor.get_domain_status()}")
    print()
    
    # Start interactive monitor
    try:
        monitor.interactive_monitor()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!") 