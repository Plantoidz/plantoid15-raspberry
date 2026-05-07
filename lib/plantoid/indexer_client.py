import os
import requests


class IndexerUnavailable(Exception):
    pass


class IndexerClient:
    """
    Talks to the Ponder GraphQL endpoint that indexes Plantoid contracts.
    One instance per network (mainnet / sepolia) 
    """

    def __init__(self, url, plantoid_address, request_timeout=5.0):
        self.url = url.rstrip("/") + "/graphql"
        self.plantoid_address = plantoid_address.lower()
        self.request_timeout = request_timeout
        self.max_processed_token_id = 0 # bumped at boot from minted.db, then in-memory

  

    # --- queries ---

    def _post(self, query, variables):
        try:
            r = requests.post(
                self.url,
                json={"query": query, "variables": variables},
                timeout=self.request_timeout,
            )
        except requests.RequestException as e:
            raise IndexerUnavailable(f"network error: {e}")
        if not r.ok:
            raise IndexerUnavailable(f"http {r.status_code}: {r.text[:200]}")
        body = r.json()
        if "errors" in body:
            raise IndexerUnavailable(f"graphql errors: {body['errors']}")
        return body["data"]


    def fetch_oldest_unprocessed_deposit(self):
      
        query = """
          query NextSeed($plantoidId: String!, $afterTokenId: BigInt!) {
            seeds(
                where: { plantoidId: $plantoidId, amount_not: null, tokenId_gt: $afterTokenId }
                orderBy: "tokenId"
                orderDirection: "asc"
                limit: 1
            ) {
                items { tokenId amount createdAt transactionHash }
            }
          }
        """
        data = self._post(query, {
            "plantoidId": self.plantoid_address,
            "afterTokenId": str(self.max_processed_token_id),
        })
        items = data.get("seeds", {}).get("items", [])
        if not items:
            return None
        it = items[0]
        return {
            "tokenId": str(int(it["tokenId"])),
            "amount": int(it["amount"]),
            "createdAt": int(it["createdAt"]),
            "txHash": it["transactionHash"],
        }

    def fetch_all_token_ids(self):
        """
        Returns a list of every tokenId ever minted on this plantoid, ordered by
        createdAt asc. Used by process_previous_tx for startup catch-up.
        Pages through 1000 at a time.
        """
        out = []
        cursor = "0"
        while True:
            query = """
              query AllSeeds($plantoidId: String!, $since: BigInt!) {
                seeds(
                  where: { plantoidId: $plantoidId, createdAt_gt: $since }
                  orderBy: "createdAt"
                  orderDirection: "asc"
                  limit: 1000
                ) {
                  items { tokenId createdAt }
                }
              }
            """
            data = self._post(query, {
                "plantoidId": self.plantoid_address,
                "since": cursor,
            })
            items = data.get("seeds", {}).get("items", [])
            if not items:
                break
            for it in items:
                out.append(str(int(it["tokenId"])))
            cursor = str(items[-1]["createdAt"])
            if len(items) < 1000:
                break
        return out
