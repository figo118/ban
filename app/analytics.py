from collections import defaultdict
from app.models import Signal, Snapshot


def summarize_signals(signals: list[Signal], snapshots: list[Snapshot], horizon: int = 12) -> list[dict]:
    by_symbol: dict[str, list[Snapshot]] = defaultdict(list)
    for snapshot in sorted(snapshots, key=lambda item: item.created_at):
        by_symbol[snapshot.symbol].append(snapshot)

    results: list[dict] = []
    for signal in signals:
        future = [
            snapshot
            for snapshot in by_symbol.get(signal.symbol, [])
            if snapshot.created_at > signal.created_at
        ][:horizon]
        if not future:
            results.append({"signal_id": signal.id, "symbol": signal.symbol, "status": "pending"})
            continue
        favorable = max((signal.entry_max / row.price - 1) * 100 for row in future)
        adverse = max((row.price / signal.entry_max - 1) * 100 for row in future)
        results.append(
            {
                "signal_id": signal.id,
                "symbol": signal.symbol,
                "status": "tracked",
                "horizon_points": len(future),
                "mfe_pct": round(favorable, 3),
                "mae_pct": round(adverse, 3),
                "last_price": future[-1].price,
            }
        )
    return results
