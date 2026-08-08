class VisibilityPredictor:

    @staticmethod
    def predict(r):

        score = 0

        if not r["VALID"]:
            score += 40

        if r["REPAIRED"]:
            score += 20

        if r["AREA_HA"] < 0.002:
            score += 15

        if r["COMPACT"] < 0.15:
            score += 10

        if r["ISLAND"]:
            score += 5

        if r["HOLE"] > 0:
            score += 10

        if score >= 50:
            return "LIKELY_HIDDEN"

        return "VISIBLE"