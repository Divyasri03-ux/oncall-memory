"""
Hindsight Memory Client Integration for Northwind Pay OnCall Memory.
Strictly communicates with the live Hindsight API via the official hindsight-client SDK
for retain, recall, reflect, and memory bank management.
Supports dynamic loop-bound client creation for asyncio & FastAPI compatibility.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.config import (
    HINDSIGHT_BASE_URL,
    HINDSIGHT_API_KEY,
    HINDSIGHT_BANK_ID,
    is_hindsight_configured
)
from hindsight_client import Hindsight

logger = logging.getLogger(__name__)


class HindsightMemoryManager:
    def __init__(self):
        if not is_hindsight_configured():
            raise RuntimeError("HINDSIGHT_API_KEY or HINDSIGHT_BASE_URL is not configured in .env")

        self.bank_id = HINDSIGHT_BANK_ID
        self.base_url = HINDSIGHT_BASE_URL
        self.api_key = HINDSIGHT_API_KEY
        self.is_connected = True
        logger.info(f"Live Hindsight Memory client ready for {self.base_url}, bank '{self.bank_id}'")

    def _get_client(self) -> Hindsight:
        """Returns a Hindsight client bound to the current running event loop."""
        return Hindsight(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=60.0
        )

    def _format_incident_for_retention(self, inc: Dict[str, Any]) -> str:
        """Formats an incident into an optimal semantic memory unit for Hindsight retain."""
        text = (
            f"Production Incident [{inc['id']}] on {inc['date']} in service '{inc['service']}': {inc['title']}.\n"
            f"Error Logs & Stack Traces:\n{inc['error_logs']}\n"
            f"Diagnosed Root Cause:\n{inc['root_cause']}\n"
            f"Remediation Runbook:\n{inc['fix_steps']}\n"
            f"Outcome: Fix status is {inc['fix_status']}. "
            f"Time-to-resolve (MTTR): {inc['time_to_resolve']}. "
            f"Resolved by engineer: {inc['who_fixed_it']}.\n"
        )
        if inc.get("failed_reason"):
            text += f"CRITICAL TRAP / FAILED FIX ATTEMPT:\n{inc['failed_reason']}\n"
        return text

    async def aretain_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Async retention of a single incident into live Hindsight bank."""
        content = self._format_incident_for_retention(incident)
        metadata = {
            "incident_id": str(incident.get("id", f"INC-{int(datetime.now().timestamp())}")),
            "service": str(incident.get("service", "general")),
            "date": str(incident.get("date", datetime.now().strftime("%Y-%m-%d %H:%M UTC"))),
            "who_fixed_it": str(incident.get("who_fixed_it", "On-Call Engineer")),
            "time_to_resolve": str(incident.get("time_to_resolve", "Live Run")),
            "fix_status": str(incident.get("fix_status", "SUCCESS")),
            "title": str(incident.get("title", "Production Incident"))[:120]
        }

        client = self._get_client()
        try:
            res = await client.aretain(
                bank_id=self.bank_id,
                content=content,
                context=f"service:{metadata['service']}",
                metadata=metadata,
                retain_async=False
            )
            logger.info(f"Live Hindsight aretain succeeded for {metadata['incident_id']}")
            return {
                "status": "success",
                "mode": "hindsight_live",
                "id": metadata["incident_id"],
                "bank_id": self.bank_id
            }
        finally:
            await client.aclose()

    def retain_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous retain wrapper for standalone scripts."""
        content = self._format_incident_for_retention(incident)
        metadata = {
            "incident_id": str(incident.get("id", f"INC-{int(datetime.now().timestamp())}")),
            "service": str(incident.get("service", "general")),
            "date": str(incident.get("date", datetime.now().strftime("%Y-%m-%d %H:%M UTC"))),
            "who_fixed_it": str(incident.get("who_fixed_it", "On-Call Engineer")),
            "time_to_resolve": str(incident.get("time_to_resolve", "Live Run")),
            "fix_status": str(incident.get("fix_status", "SUCCESS")),
            "title": str(incident.get("title", "Production Incident"))[:120]
        }
        client = self._get_client()
        try:
            res = client.retain(
                bank_id=self.bank_id,
                content=content,
                context=f"service:{metadata['service']}",
                metadata=metadata,
                retain_async=False
            )
            return {
                "status": "success",
                "mode": "hindsight_live",
                "id": metadata["incident_id"],
                "bank_id": self.bank_id
            }
        finally:
            client.close()

    async def arecall_memories(self, query: str, budget: str = "high") -> List[Dict[str, Any]]:
        """Recalls relevant memories from live Hindsight bank asynchronously."""
        client = self._get_client()
        try:
            logger.info(f"Calling live Hindsight arecall (budget={budget})...")
            response = await client.arecall(
                bank_id=self.bank_id,
                query=query,
                budget=budget,
                max_tokens=4096
            )
            results = []
            items = getattr(response, "results", []) or []
            for item in items:
                text = getattr(item, "text", str(item))
                meta = getattr(item, "metadata", {}) or {}
                fact_type = getattr(item, "type", "experience")
                item_id = getattr(item, "id", "")

                inc_id = meta.get("incident_id") or item_id
                date = meta.get("date") or getattr(item, "occurred_start", "Historical")
                who = meta.get("who_fixed_it") or "SRE Team"
                status = meta.get("fix_status") or ("FAILED" if "FAILED" in text else "SUCCESS")
                title = meta.get("title") or text[:60] + "..."

                results.append({
                    "id": item_id,
                    "text": text,
                    "type": fact_type,
                    "metadata": meta,
                    "incident_id": inc_id,
                    "date": date,
                    "who_fixed_it": who,
                    "fix_status": status,
                    "title": title,
                    "time_to_resolve": meta.get("time_to_resolve", "30 mins"),
                    "failed_reason": meta.get("failed_reason", ""),
                    "score": getattr(item, "score", 0.95)
                })
            logger.info(f"Live Hindsight recalled {len(results)} memories.")
            return results
        finally:
            await client.aclose()

    async def areflect_insights(self, query: str = "What patterns keep causing our incidents and what should we fix permanently?") -> Dict[str, Any]:
        """Uses live Hindsight Reflect to synthesize long-term systemic insights."""
        client = self._get_client()
        try:
            logger.info(f"Calling live Hindsight areflect (budget=high)...")
            answer = await client.areflect(
                bank_id=self.bank_id,
                query=query,
                budget="high"
            )
            text = getattr(answer, "text", str(answer))
            logger.info(f"Live Hindsight reflect succeeded ({len(text)} chars).")
            return {
                "status": "success",
                "source": "hindsight_reflect_live",
                "reflection": text,
                "bank_id": self.bank_id
            }
        finally:
            await client.aclose()

    async def aget_memory_stats(self) -> Dict[str, Any]:
        """Queries live Hindsight bank for memory unit statistics asynchronously."""
        client = self._get_client()
        try:
            res = await client.alist_memories(bank_id=self.bank_id, limit=1)
            total = getattr(res, "total", 0)
            return {
                "bank_id": self.bank_id,
                "total_memories": total,
                "hindsight_connected": True,
                "base_url": HINDSIGHT_BASE_URL,
                "mode": "Hindsight Cloud Live (Active)"
            }
        finally:
            await client.aclose()

    async def alist_all_memories(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Queries live Hindsight bank for memory unit listings asynchronously."""
        client = self._get_client()
        try:
            res = await client.alist_memories(bank_id=self.bank_id, limit=limit)
            items = getattr(res, "items", [])
            output = []
            for item in items:
                meta = getattr(item, "metadata", {}) or {}
                output.append({
                    "id": getattr(item, "id", "")[:12],
                    "service": meta.get("service") or getattr(item, "context", "service").replace("service:", ""),
                    "date": meta.get("date", "Recent"),
                    "fix_status": meta.get("fix_status") or ("FAILED" if "FAILED" in getattr(item, "text", "") else "SUCCESS"),
                    "who_fixed_it": meta.get("who_fixed_it", "SRE"),
                    "title": meta.get("title") or getattr(item, "text", "")[:70] + "..."
                })
            return output
        finally:
            await client.aclose()

    def get_memory_stats(self) -> Dict[str, Any]:
        """Synchronous wrapper for get_memory_stats."""
        client = self._get_client()
        try:
            res = client.list_memories(bank_id=self.bank_id, limit=1)
            total = getattr(res, "total", 0)
            return {
                "bank_id": self.bank_id,
                "total_memories": total,
                "hindsight_connected": True,
                "base_url": HINDSIGHT_BASE_URL,
                "mode": "Hindsight Cloud Live (Active)"
            }
        finally:
            client.close()


# Singleton instance
memory_manager = HindsightMemoryManager()
