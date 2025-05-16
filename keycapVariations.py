# --- Script: Generate Keycap Variants using addNewComponentCopy with Two-Phase Placement ---

import adsk.core, adsk.fusion, traceback

# Variants to create as unique copies of the master keycap
VARIANTS = [
    (1, 1.25), (1, 1),
    (2, 1.75), (2, 1),
    (3, 1.25), (3, 1),
    (4, 1),
]

# Row profile data (user parameter names for height and top angle)
ROW_PROFILES = {
    1: ("row1Height", "row1Angle"),
    2: ("row2Height", "row2Angle"),
    3: ("row3Height", "row3Angle"),
    4: ("row4Height", "row4Angle")
}

U_UNIT_CM = 1.9  # spacing in cm

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        rootComp = design.rootComponent

        if rootComp.occurrences.count == 0:
            ui.messageBox("No subcomponents found in the root component.")
            return

        base_occ = rootComp.occurrences.item(0)
        base_comp = base_occ.component
        base_params = base_comp.modelParameters

        def set_param(params, target, value):
            for p in params:
                if p.name.lower().startswith(target.lower()):
                    try:
                        if isinstance(value, str):
                            p.expression = value
                        else:
                            p.value = float(value)
                        return True
                    except Exception as e:
                        ui.messageBox(f"Failed to set {p.name} with value '{value}': {e}")
                        return False
            ui.messageBox(f"No parameter starting with '{target}' was found in base component.")
            return False

        # Phase 1: Create all variations without placement
        row_offsets = {}
        index = 0
        created_occs = []

        for row, width in VARIANTS:
            height_param, angle_param = ROW_PROFILES.get(row, ("10", "6"))

            # Set parameters on base BEFORE copying
            set_param(base_params, 'uWidth', f"{width} mm")
            set_param(base_params, 'height', height_param)
            set_param(base_params, 'topAngle', angle_param)
            design.computeAll()

            # Use identity transform
            transform = adsk.core.Matrix3D.create()
            new_occ = rootComp.occurrences.addNewComponentCopy(base_comp, transform)
            if not new_occ:
                ui.messageBox("addNewComponentCopy failed.")
                continue

            new_comp = new_occ.component
            new_comp.name = f"keycap_r{row}_w{width:.2f}_{index}"
            created_occs.append((new_occ, row, width))
            index += 1

        # Phase 2: Move all components to final position
        row_offsets = {}
        for occ_data in created_occs:
            occ, row, width = occ_data
            current_offset_u = row_offsets.get(row, 0)
            x_offset_cm = (current_offset_u + width / 2) * U_UNIT_CM
            y_offset_cm = row * U_UNIT_CM

            move = adsk.core.Matrix3D.create()
            move.translation = adsk.core.Vector3D.create(x_offset_cm, y_offset_cm, 0)
            occ.transform = move

            row_offsets[row] = current_offset_u + width

    except:
        if ui:
            ui.messageBox('Failed to create variants:\n{}'.format(traceback.format_exc()))
