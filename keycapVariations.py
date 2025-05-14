# --- Script: Generate Keycap Variants using addNewComponentCopy (Paste New Equivalent) ---

import adsk.core, adsk.fusion, traceback

# Variants to create as unique copies of the master keycap
VARIANTS = [
    (1, 1),
    (1, 1.25),
    (2, 1),
    (2, 1.25),
]

# Row profile data (height in mm, top angle in deg)
ROW_PROFILES = {
    1: (11, 2),
    2: (14, 9),
    3: (18, 15),
    4: (18, 15)
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
                        if 'mm' in value or 'deg' in value:
                            p.expression = value
                        else:
                            p.value = float(value)
                        return True
                    except Exception as e:
                        ui.messageBox(f"Failed to set {p.name} with value '{value}': {e}")
                        return False
            ui.messageBox(f"No parameter starting with '{target}' was found in base component.")
            return False

        # Track cumulative width per row in U
        row_offsets = {}
        index = 0

        for row, width in VARIANTS:
            height, angle = ROW_PROFILES.get(row, (10, 6))

            # Determine placement offset BEFORE modifying the base component
            current_offset_u = row_offsets.get(row, 0)
            x_offset_cm = (current_offset_u + width / 2) * U_UNIT_CM
            y_offset_cm = row * U_UNIT_CM

            # Ensure new transform object each loop
            transform = adsk.core.Matrix3D.create()
            translation = adsk.core.Vector3D.create(x_offset_cm, y_offset_cm, 0)
            transform.translation = translation

            # Debug placement info
            ui.messageBox(f"Placement for keycap_r{row}_w{width:.2f}_{index} at ({x_offset_cm}, {y_offset_cm}, 0)\nVector: {translation.x}, {translation.y}, {translation.z}")

            # 1. Set the parameters on the original component
            set_param(base_params, 'uWidth', f"{width} mm")
            set_param(base_params, 'height', f"{height} mm")
            set_param(base_params, 'topAngle', f"{angle} deg")
            design.computeAll()

            # 2. Create a copy using addNewComponentCopy
            new_occ = rootComp.occurrences.addNewComponentCopy(base_comp, transform)

            if not new_occ:
                ui.messageBox("addNewComponentCopy failed.")
                continue

            new_comp = new_occ.component

            # 3. Rename the newly created component
            variant_name = f"keycap_r{row}_w{width:.2f}_{index}"
            new_comp.name = variant_name
            index += 1

            # Update offset
            row_offsets[row] = current_offset_u + width

    except:
        if ui:
            ui.messageBox('Failed to create variants:\n{}'.format(traceback.format_exc()))
