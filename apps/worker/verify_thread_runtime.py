import asyncio
import json
from x_daemon import XDaemon

LONG_TEXT = (
    "🔬 XHive runtime thread test. "
    "Yeni araştırmamızda yapay zeka modellerinin finansal piyasalara etkilerini inceledik. "
    "Ana bulgular: risk analizi hızlandı, sinyal kalitesi arttı, volatilite tahmini iyileşti. "
    "Model tabanlı karar destek altyapısı manuel süreçleri ciddi şekilde azaltıyor. "
    "Bu test thread mekanizmasını doğrulamak içindir. #XHive #AI #Research"
)

async def main():
    daemon = XDaemon()
    daemon.max_retries = 1
    await daemon.start()
    try:
        result = await asyncio.wait_for(daemon.post_tweet(LONG_TEXT), timeout=120)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False, indent=2))
    finally:
        await daemon.stop()

if __name__ == "__main__":
    asyncio.run(main())
