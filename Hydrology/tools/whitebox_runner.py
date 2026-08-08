from whitebox.whitebox_tools import WhiteboxTools


class WhiteboxRunner:

    def __init__(self):
        self.wbt = WhiteboxTools()

    # -----------------------------------------------------
    # Fill Depressions
    # -----------------------------------------------------
    def fill_depressions(self, input_dem, output_dem):

        return self.wbt.fill_depressions(
            i=input_dem,
            output=output_dem
        )

    # -----------------------------------------------------
    # D8 Pointer
    # -----------------------------------------------------
    def d8_pointer(self, input_dem, output_pointer):

        return self.wbt.d8_pointer(
            i=input_dem,
            output=output_pointer
        )

    # -----------------------------------------------------
    # D8 Flow Accumulation
    # -----------------------------------------------------
    def d8_flow_accumulation(self, pointer, output_acc):

        return self.wbt.d8_flow_accumulation(
            i=pointer,
            output=output_acc,
            out_type="cells"
        )

    # -----------------------------------------------------
    # Snap Pour Point
    # -----------------------------------------------------
    def snap_pour_points(
        self,
        pour_points,
        flow_accumulation,
        output_points,
        snap_distance
    ):

        return self.wbt.snap_pour_points(
            pour_pts=pour_points,
            flow_accum=flow_accumulation,
            output=output_points,
            snap_dist=snap_distance
        )

    # -----------------------------------------------------
    # Watershed
    # -----------------------------------------------------
    def watershed(
        self,
        pointer,
        pour_points,
        output_watershed
    ):

        return self.wbt.watershed(
            d8_pntr=pointer,
            pour_pts=pour_points,
            output=output_watershed
        )