from app.brain.rules import determine_market_state
from app.templates.posts import build_posts


class GrowthEngine:

    def generate(self, snapshot):

        state = determine_market_state(snapshot)

        return build_posts(snapshot, state)
