import asyncio
from utils import fetch_pairs, filter_pairs, format_pair_message

async def main():
    print("📡 Fetching data from DEXScreener...")
    pairs = await fetch_pairs()
    print(f"✅ Total pairs fetched: {len(pairs)}")

    filtered = filter_pairs(pairs)
    print(f"🧪 Pairs after filtering: {len(filtered)}")

    print("\n📊 Example formatted output:")
    for pair in filtered[:3]:
        msg = format_pair_message(pair, include_meta=True)
        print("\n" + msg)

if __name__ == "__main__":
    asyncio.run(main())
