def generate_face_mill_gcode(
    workpiece_length=100.0,    # Length along X-axis in mm
    workpiece_width=50.0,      # Width along Y-axis in mm
    stock_thickness=5.0,      # Material thickness in mm
    tool_diameter=40.0,        # Face mill diameter in mm
    feed_rate=500.0,          # Feed rate in mm/min
    spindle_speed=2000,       # Spindle speed in RPM
    depth_per_pass=2.0,       # Depth of cut per pass in mm
    safe_height=20.0          # Safe Z height for rapid moves in mm
):
    # Calculate number of passes needed
    num_passes = int(stock_thickness / depth_per_pass) + (stock_thickness % depth_per_pass > 0)
    # print(num_passes)
    
    # Calculate step-over (typically 60-70% of tool diameter)
    step_over = tool_diameter * 0.65
    num_y_steps = int(workpiece_width / step_over) + (workpiece_width % step_over > 0)
    
    # Initialize G-code list
    gcode = []
    
    # Header
    gcode.append("%")  # Program start
    gcode.append("G21")  # Metric units
    gcode.append("G90")  # Absolute positioning
    gcode.append("G17")  # XY plane selection
    gcode.append("M06 T10") # Change Tool to Facemill
    gcode.append(f"M03 S{spindle_speed}")  # Spindle start
    
    # Initial positioning
    gcode.append(f"G00 Z{safe_height:.2f}")  # Move to safe height
    gcode.append("G00 X-5.00 Y0.00")  # Move to starting position (slightly before material)
    
    # Main milling operation
    current_y = 0.0
    direction = 1  # 1 for forward, -1 for reverse
    
    for y_step in range(num_y_steps + 1):
        # Calculate actual Y position
        if current_y > workpiece_width:
            current_y = workpiece_width
            
        for pass_num in range(num_passes):
            # Calculate current depth
            current_depth = -((pass_num + 1) * depth_per_pass)
            if abs(current_depth) > stock_thickness:
                current_depth = -stock_thickness
                
            # Generate cutting moves
            gcode.append(f"G01 Z{current_depth:.2f} F{feed_rate/2:.1f}")  # Plunge at half feed
            
            # Cut in current direction
            if direction == 1:
                gcode.append(f"G01 X{workpiece_length + 5:.2f} Y{current_y:.2f} F{feed_rate:.1f}")
            else:
                gcode.append(f"G01 X-5.00 Y{current_y:.2f} F{feed_rate:.1f}")
            
            # Only change direction if not the last pass of the last Y step
            if not (y_step == num_y_steps and pass_num == num_passes - 1):
                direction *= -1  # Reverse direction
        
        # Move to next Y position if not the last step
        if y_step < num_y_steps:
            current_y += step_over
            if direction == 1:
                gcode.append(f"G00 X{workpiece_length + 5:.2f} Y{current_y:.2f}")
            else:
                gcode.append(f"G00 X-5.00 Y{current_y:.2f}")
    
    # Program end
    gcode.append(f"G00 Z{safe_height:.2f}")  # Return to safe height
    gcode.append("M05")  # Spindle stop
    gcode.append("G00 X0.00 Y0.00")  # Return to home
    gcode.append("M30")  # Program end
    gcode.append("%")  # End of file
    
    return gcode

def save_gcode_to_file(gcode_lines, filename="face_mill.nc"):
    """Save G-code to a file"""
    with open(filename, 'w') as f:
        for line in gcode_lines:
            f.write(line + "\n")
    print(f"G-code saved to {filename}")

# Generate and save the program
if __name__ == "__main__":
    # Customize these parameters as needed
    gcode = generate_face_mill_gcode(
        workpiece_length=150,    # 100mm long workpiece
        workpiece_width=50.0,      # 50mm wide workpiece
        stock_thickness=5.0,      # 10mm thick material
        tool_diameter=40.0,        # 40mm face mill
        feed_rate=500.0,          # 500 mm/min feed rate
        spindle_speed=2000,       # 2000 RPM
        depth_per_pass=2.0,       # 2mm per pass
        safe_height=20.0          # 20mm safe height
    )
    
    # Print the G-code to console
    print("Generated G-code:")
    for line in gcode:
        print(line)
    
    # Save to file
    # save_gcode_to_file(gcode, "face_mill_zigzag_2.nc")