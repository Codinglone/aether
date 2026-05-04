#!/usr/bin/env python3
"""
Hybrid perception demo: AT-SPI primary + Screenshot/LLM fallback.

Demonstrates the philosophy:
1. Try AT-SPI first (fast, local, accurate)
2. Only if AT-SPI fails, use screenshot + local LLM (slower, fallback)
3. Never use cloud APIs - everything is on-device
"""

import os
import subprocess
import time

os.environ.setdefault("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")

from aether.perception.hybrid import HybridPerceptionAdapter
from aether.brain.local_llm import LocalLLM


def main():
    print("=" * 70)
    print("🧠 AETHER-NATIVE: Hybrid Perception Demo")
    print("=" * 70)
    print("\n   PRIMARY: AT-SPI (fast, local, structured)")
    print("   FALLBACK: Screenshot + Local LLM (when AT-SPI fails)")
    print("   NEVER: Cloud APIs (privacy, speed, cost)")

    # Initialize hybrid adapter with local LLM
    print("\n🔌 Initializing hybrid adapter...")
    try:
        adapter = HybridPerceptionAdapter(llm_model="llama3.2:1b")
        print("   ✅ Local LLM ready (llama3.2:1b)")
    except Exception as e:
        print(f"   ⚠️  LLM not available: {e}")
        print("   Running in AT-SPI-only mode")
        adapter = HybridPerceptionAdapter()

    # Test 1: Find Calculator (AT-SPI should work)
    print("\n" + "=" * 70)
    print("TEST 1: Find Calculator button '2'")
    print("=" * 70)
    print("   Expected: AT-SPI primary path (fast)")

    # Launch calculator
    subprocess.Popen(
        ["gnome-calculator"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2)

    result = adapter.find_element(name="2")
    if result:
        print(f"   ✅ Found: {result.name} (role: {result.role})")
        print(f"   📊 Source: {result.metadata.get('source', 'atspi') if result.metadata else 'atspi'}")
        print(f"   📍 Bounds: {result.bounds}")
    else:
        print("   ❌ Not found")

    # Test 2: Find a non-existent element (forces fallback)
    print("\n" + "=" * 70)
    print("TEST 2: Find non-existent element 'UnicornButton'")
    print("=" * 70)
    print("   Expected: AT-SPI fails → LLM fallback (if available)")

    result = adapter.find_element(name="UnicornButton")
    if result:
        print(f"   ✅ Found: {result.name}")
        print(f"   📊 Source: {result.metadata.get('source', 'unknown') if result.metadata else 'unknown'}")
        print(f"   🎯 Confidence: {result.metadata.get('confidence', 0) if result.metadata else 0}")
        if result.metadata and result.metadata.get('reasoning'):
            print(f"   💭 Reasoning: {result.metadata['reasoning'][:100]}")
    else:
        print("   ❌ Not found (AT-SPI failed, LLM also couldn't find it)")

    # Stats
    print("\n" + "=" * 70)
    print("PERFORMANCE STATS")
    print("=" * 70)
    stats = adapter.get_stats()
    print(f"   Primary (AT-SPI) queries:   {stats['primary_queries']}")
    print(f"   Fallback (LLM) queries:     {stats['fallback_queries']}")
    print(f"   Fallback rate:              {stats['fallback_rate']:.1%}")
    print(f"\n   Goal: Keep fallback rate <5% for most tasks")
    print("   Fallback is for edge cases only (Electron, custom UIs)")
    print("=" * 70)

    # Cleanup
    subprocess.run(["pkill", "-f", "gnome-calculator"], check=False)


if __name__ == "__main__":
    main()
