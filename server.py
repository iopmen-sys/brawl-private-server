import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from updates.season_update import UpdateConfig, open_box

HOST = "127.0.0.1"
PORT = 8080

config = UpdateConfig()
player_profile = {
    "name": "TestBrawler",
    "trophies": 1250,
    "gems": 200,
    "coins": 1000,
    "power_points": 300,
    "brawlers": ["Shelly", "Colt"],
}


def apply_rewards(rewards: list[dict]) -> None:
    for entry in rewards:
        item = entry["item"]
        amount = entry["amount"]
        if item == "coins":
            player_profile["coins"] += amount
        elif item == "power_points":
            player_profile["power_points"] += amount
        elif item == "gems":
            player_profile["gems"] += amount
        elif item.startswith("brawler_unlock:"):
            brawler = item.split(":", 1)[1]
            if brawler not in player_profile["brawlers"]:
                player_profile["brawlers"].append(brawler)


class PrivateServerHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, payload: dict) -> None:
        raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        if self.path == "/status":
            self._send_json(
                200,
                {
                    "status": "online",
                    "season": config.season_name,
                    "event": config.bonus_event,
                    "shop_offers": config.shop_offers,
                },
            )
        elif self.path == "/profile":
            self._send_json(200, player_profile)
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def do_POST(self) -> None:
        if self.path == "/open-box":
            result = open_box(config)
            apply_rewards(result["rewards"])
            self._send_json(
                200,
                {
                    "box_result": result,
                    "profile": player_profile,
                },
            )
        elif self.path == "/buy-offer":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(body)
            offer_id = data.get("offer_id")

            offer = next((o for o in config.shop_offers if o["id"] == offer_id), None)
            if not offer:
                self._send_json(404, {"error": "Offer not found"})
                return

            cost = offer["cost_gems"]
            if player_profile["gems"] < cost:
                self._send_json(400, {"error": "Not enough gems"})
                return

            player_profile["gems"] -= cost
            if "coins" in offer:
                player_profile["coins"] += offer["coins"]
            if "boxes" in offer:
                for _ in range(offer["boxes"]):
                    box = open_box(config)
                    apply_rewards(box["rewards"])

            self._send_json(
                200,
                {
                    "purchased": offer,
                    "profile": player_profile,
                },
            )
        else:
            self._send_json(404, {"error": "Endpoint not found"})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), PrivateServerHandler)
    print(f"Server running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
      
