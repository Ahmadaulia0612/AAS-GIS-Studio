from collections import deque


class ClusterAnalyzer:

    @staticmethod
    def analyze(gdf):

        spatial = gdf.sindex

        cluster = [-1] * len(gdf)
        cluster_id = 0

        for start in range(len(gdf)):

            if cluster[start] != -1:
                continue

            queue = deque([start])
            cluster[start] = cluster_id

            while queue:

                idx = queue.popleft()

                geom = gdf.geometry.iloc[idx]

                candidates = list(
                    spatial.intersection(
                        geom.bounds
                    )
                )

                for other in candidates:

                    if other == idx:
                        continue

                    if cluster[other] != -1:
                        continue

                    if geom.touches(gdf.geometry.iloc[other]) \
                       or geom.intersects(gdf.geometry.iloc[other]):

                        cluster[other] = cluster_id
                        queue.append(other)

            cluster_id += 1

        gdf["CLUSTER"] = cluster

        sizes = (
            gdf.groupby("CLUSTER")
               .size()
               .to_dict()
        )

        gdf["CLUSTER_SIZE"] = (
            gdf["CLUSTER"]
            .map(sizes)
        )

        return gdf