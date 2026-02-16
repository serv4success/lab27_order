#!/usr/bin/env python3
"""
Load Generator voor Instana Demo
Genereert verschillende load scenarios om monitoring te demonstreren
"""
import requests
import random
import time
import concurrent.futures
import argparse
from datetime import datetime

# Sample data voor realistische orders
CUSTOMERS = [
    "Jan de Vries", "Maria Jansen", "Peter van Dijk", "Anna Bakker",
    "Kees Vermeulen", "Sophie de Jong", "Tom Visser", "Lisa Smit"
]

PRODUCTS = [
    "MacBook Pro", "iPhone 15", "AirPods Pro", "iPad Air",
    "Apple Watch", "Magic Keyboard", "Monitor", "Webcam"
]

class LoadGenerator:
    def __init__(self, base_url, concurrency=5):
        self.base_url = base_url.rstrip('/')
        self.concurrency = concurrency
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'errors': 0
        }
    
    def create_order(self):
        """Creëer een enkele order"""
        order_data = {
            "customer_name": random.choice(CUSTOMERS),
            "product": random.choice(PRODUCTS),
            "amount": round(random.uniform(50.0, 2000.0), 2)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/orders",
                headers={'Content-Type': 'application/json'},
                json=order_data,
                timeout=10
            )
            
            self.stats['total'] += 1
            
            if response.status_code == 201:
                self.stats['success'] += 1
                return True, response.json()
            else:
                self.stats['failed'] += 1
                return False, response.text
                
        except Exception as e:
            self.stats['errors'] += 1
            return False, str(e)
    
    def normal_load(self, duration_minutes=5, rate=5):
        """
        Normale load - steady state traffic
        rate: aantal requests per seconde
        """
        print(f"\n🟢 NORMAL LOAD - {rate} req/sec voor {duration_minutes} minuten")
        print("=" * 60)
        
        end_time = time.time() + (duration_minutes * 60)
        interval = 1.0 / rate
        
        while time.time() < end_time:
            start = time.time()
            success, result = self.create_order()
            
            status = "✓" if success else "✗"
            print(f"{status} Order - Success: {self.stats['success']}, Failed: {self.stats['failed']}, Errors: {self.stats['errors']}")
            
            elapsed = time.time() - start
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)
        
        self.print_stats()
    
    def spike_traffic(self, duration_minutes=2, concurrency=20):
        """
        Traffic spike - plotselinge toename in load
        """
        print(f"\n🔴 SPIKE TRAFFIC - {concurrency} concurrent voor {duration_minutes} minuten")
        print("=" * 60)
        
        end_time = time.time() + (duration_minutes * 60)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            while time.time() < end_time:
                futures = [executor.submit(self.create_order) for _ in range(concurrency)]
                
                for future in concurrent.futures.as_completed(futures):
                    success, result = future.result()
                    status = "✓" if success else "✗"
                    print(f"{status} Order - Success: {self.stats['success']}, Failed: {self.stats['failed']}")
                
                time.sleep(1)
        
        self.print_stats()
    
    def gradual_increase(self, start_rate=2, max_rate=20, step_duration=60):
        """
        Graduele toename van load
        """
        print(f"\n🟡 GRADUAL INCREASE - {start_rate} → {max_rate} req/sec")
        print("=" * 60)
        
        current_rate = start_rate
        
        while current_rate <= max_rate:
            print(f"\n📈 Current rate: {current_rate} req/sec")
            
            end_time = time.time() + step_duration
            interval = 1.0 / current_rate
            
            while time.time() < end_time:
                start = time.time()
                self.create_order()
                
                elapsed = time.time() - start
                sleep_time = max(0, interval - elapsed)
                time.sleep(sleep_time)
            
            current_rate += 2
        
        self.print_stats()
    
    def error_scenario(self, duration_minutes=2):
        """
        Simuleer errors door hoge load + timeouts
        """
        print(f"\n💥 ERROR SCENARIO - High load met errors voor {duration_minutes} minuten")
        print("=" * 60)
        
        self.spike_traffic(duration_minutes=duration_minutes, concurrency=50)
    
    def mixed_scenario(self, duration_minutes=10):
        """
        Mixed scenario - verschillende patronen
        """
        print(f"\n🎭 MIXED SCENARIO - {duration_minutes} minuten")
        print("=" * 60)
        
        scenarios = [
            ("Normal", lambda: self.normal_load(duration_minutes=2, rate=3)),
            ("Spike", lambda: self.spike_traffic(duration_minutes=1, concurrency=15)),
            ("Normal", lambda: self.normal_load(duration_minutes=2, rate=5)),
            ("Spike", lambda: self.spike_traffic(duration_minutes=1, concurrency=25)),
            ("Cool down", lambda: self.normal_load(duration_minutes=2, rate=2))
        ]
        
        for name, scenario_func in scenarios:
            print(f"\n--- Phase: {name} ---")
            scenario_func()
            time.sleep(10)  # Korte pauze tussen scenarios
    
    def print_stats(self):
        """Print statistieken"""
        print("\n" + "=" * 60)
        print("📊 STATISTICS")
        print("=" * 60)
        print(f"Total requests:    {self.stats['total']}")
        print(f"Successful:        {self.stats['success']} ({self.stats['success']/max(self.stats['total'],1)*100:.1f}%)")
        print(f"Failed (payment):  {self.stats['failed']} ({self.stats['failed']/max(self.stats['total'],1)*100:.1f}%)")
        print(f"Errors (timeout):  {self.stats['errors']} ({self.stats['errors']/max(self.stats['total'],1)*100:.1f}%)")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Load Generator voor Instana Demo')
    parser.add_argument('--url', required=True, help='Base URL van frontend service')
    parser.add_argument('--scenario', choices=['normal', 'spike', 'gradual', 'error', 'mixed'], 
                       default='mixed', help='Load scenario')
    parser.add_argument('--duration', type=int, default=10, help='Duration in minutes')
    parser.add_argument('--concurrency', type=int, default=5, help='Concurrent requests')
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║         INSTANA DEMO - LOAD GENERATOR                    ║
╚══════════════════════════════════════════════════════════╝

Target URL: {args.url}
Scenario:   {args.scenario}
Duration:   {args.duration} minutes
Started:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
    
    generator = LoadGenerator(args.url, concurrency=args.concurrency)
    
    try:
        if args.scenario == 'normal':
            generator.normal_load(duration_minutes=args.duration, rate=5)
        elif args.scenario == 'spike':
            generator.spike_traffic(duration_minutes=args.duration, concurrency=args.concurrency)
        elif args.scenario == 'gradual':
            generator.gradual_increase()
        elif args.scenario == 'error':
            generator.error_scenario(duration_minutes=args.duration)
        elif args.scenario == 'mixed':
            generator.mixed_scenario(duration_minutes=args.duration)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Load test interrupted by user")
        generator.print_stats()

if __name__ == '__main__':
    main()
