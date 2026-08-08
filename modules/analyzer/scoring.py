class RiskScorer:

    @staticmethod
    def score(row):

        score = 0

        if row["TOUCH"] == 0:
            score += 40

        if row["NEAREST_M"] > 100:
            score += 30

        if row["AREA_HA"] < 20:
            score += 15

        if row["OVERLAP"] == 0:
            score += 10

        if row["INSIDE"]:
            score -= 20

        return score