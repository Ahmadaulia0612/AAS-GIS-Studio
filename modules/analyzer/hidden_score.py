class HiddenScore:

    @staticmethod
    def score(row):

        score = 0

        if row["AREA_HA"] < 0.20:
            score += 25

        if row["TOUCH"] == 0:
            score += 20

        if row["NEAREST_M"] > 30:
            score += 15

        if row["COMPACT"] < 0.25:
            score += 20

        if row["HOLE"] > 0:
            score += 5

        if row["MULTIPART"]:
            score += 10

        if row["INSIDE"]:
            score += 20

        return score