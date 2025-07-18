def tool_back(code, z_init_post, safe_tool_distance, tool_diameter):
    code.append(f"G00 Z{(z_init_post):.2f}")  # Move to safe height
    code.append(
        f"G00 X{-safe_tool_distance - (tool_diameter / 2)} Y0.00"
    )  # Move to starting position (slightly before material)


def pause_process(code, spindle_speed):
    code.append("M05")  # Spindle off
    code.append("M00")  # Program stop
    code.append(f"M03 S{spindle_speed}")  # Spindle on after resume


def generate_face_mill_gcode(
    workpiece_long=150.0,  # Long side of material (mm)
    workpiece_short=50.0,  # Short side of material (mm)
    workpiece_thickness=20, # Thickness side of material (mm)
    stock_thickness=5.0,  # Material thickness (mm)
    tool_diameter=40.0,  # Face mill diameter (mm)
    feed_rate=500.0,  # Feed rate (mm/min)
    spindle_speed=2000,  # Spindle speed (RPM)
    depth_of_cut=1.0,  # Depth of cut per pass in adjustment (mm)
    safe_z_distance=20.0,  # Safe Z distance for rapid moves (mm)
    safe_tool_distance=5.0,  # Safe X distance for rapid moves (mm)
    just_clean_fraction=0.1,  # Fraction of stock_thickness for just clean (10% default)
):
    # Calculate just_clean_depth as a fraction of stock_thickness
    just_clean_depth = stock_thickness * just_clean_fraction
    just_clean_depth = max(0.1, min(just_clean_depth, 0.5))  # Limit between 0.1mm and 0.5mm

    # Remaining stock after just clean
    remaining_stock = stock_thickness - just_clean_depth

    # Calculate number of adjustment passes based on remaining stock
    num_passes = int(remaining_stock / depth_of_cut) + (remaining_stock % depth_of_cut > 0)
    print(f"Just clean depth: {just_clean_depth:.2f} mm")
    print(f"Remaining stock: {remaining_stock:.2f} mm")
    print(f"Number of adjustment passes: {num_passes}")

    # Initialize G-code list
    gcode = []

    # Header
    gcode.append("%")  # Program start
    gcode.append("O0131")  # Program Number
    gcode.append("G00 G40 G49 G80")  # Rapid Positioning, Cancel offsets
    gcode.append("G21 G90 G54")  # Metric, Absolute, G54 coordinate system
    gcode.append("(FACEMILL DIA. XX)")
    gcode.append("M06 T10")  # Tool change to face mill
    gcode.append(f"M03 S{spindle_speed}")  # Spindle start

    # Long side Z-position (top of workpiece_short + safe height)
    z_long_init = workpiece_short + safe_z_distance

    # Current Y position and direction for zigzag
    current_y = 0.0
    direction = 1  # 1 for forward, -1 for reverse

    ### JUST CLEAN LONG SIDE ###
    gcode.append("(JUST CLEAN SISI PANJANG)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter)

    # Just clean pass
    gcode.append(f"G01 Z{workpiece_short - just_clean_depth:.2f} F{feed_rate / 2:.1f}")  # Plunge
    gcode.append(f"G01 X{workpiece_long + 5 + (tool_diameter / 2):.2f} Y{workpiece_thickness / 2:.2f} F{feed_rate:.1f}")  # Cut
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter)
    pause_process(gcode, spindle_speed)

    ### ADJUSTMENT LONG SIDE ###
    gcode.append("(ADJUSTMENT SISI PANJANG)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter)

    for pass_num in range(num_passes):
        # Calculate current depth (after just clean)
        current_depth = just_clean_depth + ((pass_num + 1) * depth_of_cut)
        if current_depth > stock_thickness:
            current_depth = stock_thickness  # Cap at stock thickness

        # Generate cutting moves
        gcode.append(f"G01 Z{workpiece_short - current_depth:.2f} F{feed_rate / 2:.1f}")  # Plunge
        if direction == 1:
            gcode.append(f"G01 X{workpiece_long + 5 + (tool_diameter / 2):.2f} Y{workpiece_thickness / 2:.2f} F{feed_rate:.1f}")
            direction = -1
        else:
            gcode.append(f"G01 X{-tool_diameter / 2 - safe_tool_distance:.2f} Y{workpiece_thickness / 2:.2f} F{feed_rate:.1f}")
            direction = 1
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter)
    pause_process(gcode, spindle_speed)

    current_y = 0.0
    direction = 1  # 1 for forward, -1 for reverse
    ### JUST CLEAN SHORT SIDE ###
    z_short_init = workpiece_long + safe_z_distance  # Adjusted for short side
    gcode.append("(JUST CLEAN SISI PENDEK)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter)

    # Just clean pass
    gcode.append(f"G01 Z{workpiece_long - just_clean_depth:.2f} F{feed_rate / 2:.1f}")  # Plunge
    gcode.append(f"G01 X{workpiece_short + 5 + (tool_diameter / 2):.2f} Y{workpiece_thickness / 2:.2f} F{feed_rate:.1f}")  # Cut
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter)
    pause_process(gcode, spindle_speed)

    ### ADJUSTMENT SHORT SIDE ###
    gcode.append("(ADJUSTMENT SISI PENDEK)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter)

    for pass_num in range(num_passes):
        # Calculate current depth (after just clean)
        current_depth = just_clean_depth + ((pass_num + 1) * depth_of_cut)
        if current_depth > stock_thickness:
            current_depth = stock_thickness  # Cap at stock thickness

        # Generate cutting moves
        gcode.append(f"G01 Z{workpiece_long - current_depth:.2f} F{feed_rate / 2:.1f}")  # Plunge
        if direction == 1:
            gcode.append(f"G01 X{workpiece_short + 5 + (tool_diameter / 2):.2f} Y{workpiece_thickness / 2:.2f} F{feed_rate:.1f}")
            direction = -1
        else:
            gcode.append(f"G01 X{-tool_diameter / 2 - safe_tool_distance:.2f} Y{workpiece_thickness / 2:.2f} F{feed_rate:.1f}")
            direction = 1

    # Program end
    gcode.append(f"G00 Z{z_short_init:.2f}")  # Return to safe height
    gcode.append("M05")  # Spindle stop
    gcode.append("G00 X0.00 Y0.00")  # Return to home
    gcode.append("M30")  # Program end
    gcode.append("%")  # End of file

    return gcode


def save_gcode_to_file(gcode_lines, filename="face_mill.nc"):
    """Save G-code to a file"""
    with open(filename, "w") as f:
        for line in gcode_lines:
            f.write(line + "\n")
    print(f"G-code saved to {filename}")


# Generate and save the program
if __name__ == "__main__":
    # Customize these parameters as needed
    gcode = generate_face_mill_gcode(
        workpiece_long=150.0,  # 150mm long workpiece
        workpiece_short=50.0,  # 50mm wide workpiece
        stock_thickness=5.0,  # 5mm thick material
        tool_diameter=40.0,  # 40mm face mill
        feed_rate=500.0,  # 500 mm/min feed rate
        spindle_speed=2000,  # 2000 RPM
        depth_of_cut=1.0,  # 1mm per pass
        safe_z_distance=20.0,  # 20mm safe Z height
        safe_tool_distance=5.0,  # 5mm safe X distance
        just_clean_fraction=0.1,  # 10% of stock thickness for just clean
    )

    # Print the G-code to console
    print("Generated G-code:")
    for line in gcode:
        print(line)

    # Save to file (uncomment to save)
    save_gcode_to_file(gcode, "face_mill_zigzag_adjusted.nc")
