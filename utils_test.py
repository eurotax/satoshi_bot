import asyncio

from utils import fetch_dex_data, filter_signals, format_signals

async def main():
    print("📡 Fetching data from DEXScreener...")
    pairs = await fetch_dex_data()
    print(f"✅ Total pairs fetched: {len(pairs)}")

    filtered = filter_signals(pairs)
    print(f"🧪 Pairs after filtering: {len(filtered)}")

    print("\n📊 Example formatted output:\n")
    output = format_signals(filtered[:3])
    print(output)

if __name__ == "__main__":
    asyncio.run(main())
