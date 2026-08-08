import os

from whitebox.whitebox_tools import WhiteboxTools


class FillDepression:

    def __init__(self):

        self.wbt = WhiteboxTools()

    def run(self, input_dem, output_dem):

        print("=" * 60)
        print("FILL DEPRESSIONS")
        print("=" * 60)
        print("Input :", input_dem)
        print("Output:", output_dem)
        print("=" * 60)

        os.makedirs(os.path.dirname(output_dem), exist_ok=True)

        self.wbt.fill_depressions(
            dem=input_dem,
            output=output_dem
)

        return output_dem