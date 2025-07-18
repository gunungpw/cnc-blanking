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
    workpiece_long=100.0,  # Long side of material (mm)
    workpiece_short=50.0,  # Short side of material (mm)
    workpiece_thick=20.0,  # Thick side of material (mm)
    parallel_block_long=0.0,  # Parallel block for long side (mm)
    parallel_block_short=0.0, # Parallel block for short side (mm)
    long_stock_thickness=5.0,  # Long material thickness (mm)
    short_stock_thickness=3.0,  # Short material thickness (mm)
    tool_diameter=50.0,  # Face mill diameter (mm)
    feed_rate=500.0,  # Feed rate (mm/min)
    spindle_speed=2000,  # Spindle speed (RPM)
    depth_of_cut=1.0,  # Depth of cut per pass in adjustment (mm)
    safe_z_distance=20.0,  # Safe Z distance for rapid moves (mm)
    safe_tool_distance=5.0,  # Safe X distance for rapid moves (mm)
    just_clean_fraction=0.1,  # Fraction of stock_thickness for just clean (10% default)
):
    # Calculate just_clean_depth as a fraction of stock_thickness
    just_clean_depth = long_stock_thickness * just_clean_fraction
    just_clean_depth = max(
        0.1, min(just_clean_depth, 0.5)
    )  # Limit between 0.1mm and 0.5mm

    # Remaining stock after just clean
    remaining_stock = long_stock_thickness - just_clean_depth

    # Calculate number of adjustment passes based on remaining stock
    num_passes = int(remaining_stock / depth_of_cut) + (
        remaining_stock % depth_of_cut > 0
    )
    print("Long Cut")
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
    gcode.append("G91 G30 X0.0")
    gcode.append("G91 G28 Y0.0")
    gcode.append("G91 G30 Z0 ")
    gcode.append("(FACEMILL DIA. 63)")
    gcode.append("M06 T10")  # Tool change to face mill
    gcode.append(f"M03 S{spindle_speed}")  # Spindle start

    # Long side Z-position (top of workpiece_short + safe height)
    z_long_init = workpiece_short + safe_z_distance + parallel_block_long

    # Current Y position and direction for zigzag
    current_y = 0.0
    direction = 1  # 1 for forward, -1 for reverse

    ### JUST CLEAN LONG SIDE ###
    gcode.append("(JUST CLEAN SISI PANJANG)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter)

    # Just clean pass
    gcode.append("M08")
    gcode.append(
        f"G01 Z{workpiece_short + parallel_block_long - just_clean_depth:.2f} F{feed_rate / 2:.1f}"
    )  # Plunge
    gcode.append(
        f"G01 X{workpiece_long + 5 + (tool_diameter / 2):.2f} Y{workpiece_thick / 2:.2f} F{feed_rate / 2:.1f}"
    )  # Cut
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter)
    gcode.append("M09")
    pause_process(gcode, spindle_speed)

    ### ADJUSTMENT LONG SIDE ###
    gcode.append("(ADJUSTMENT SISI PANJANG)")
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter)
    gcode.append("M08")
    for pass_num in range(num_passes):
        # Calculate current depth (after just clean)
        current_depth = just_clean_depth + ((pass_num + 1) * depth_of_cut)
        if current_depth > long_stock_thickness:
            current_depth = long_stock_thickness  # Cap at long stock thickness

        # Generate cutting moves
        gcode.append(
            f"G01 Z{workpiece_short + parallel_block_long - current_depth:.2f} F{feed_rate / 2:.1f}"
        )  # Plunge
        if direction == 1:
            adjustment_feed_rate = (
                feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            )
            gcode.append(
                f"G01 X{workpiece_long + 5 + (tool_diameter / 2):.2f} Y{workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = -1
        else:
            adjustment_feed_rate = (
                feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            )
            gcode.append(
                f"G01 X{-tool_diameter / 2 - safe_tool_distance:.2f} Y{workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = 1
    tool_back(gcode, z_long_init, safe_tool_distance, tool_diameter)
    gcode.append("M09")
    pause_process(gcode, spindle_speed)

    # Calculate just_clean_depth as a fraction of stock_thickness
    just_clean_depth = short_stock_thickness * just_clean_fraction
    just_clean_depth = max(
        0.1, min(just_clean_depth, 0.5)
    )  # Limit between 0.1mm and 0.5mm

    # Remaining stock after just clean
    remaining_stock = short_stock_thickness - just_clean_depth

    # Calculate number of adjustment passes based on remaining stock
    num_passes = int(remaining_stock / depth_of_cut) + (
        remaining_stock % depth_of_cut > 0
    )
    print("Short Cut")
    print(f"Just clean depth: {just_clean_depth:.2f} mm")
    print(f"Remaining stock: {remaining_stock:.2f} mm")
    print(f"Number of adjustment passes: {num_passes}")

    current_y = 0.0
    direction = 1  # 1 for forward, -1 for reverse
    ### JUST CLEAN SHORT SIDE ###
    z_short_init = workpiece_long + safe_z_distance + parallel_block_long # Adjusted for short side
    gcode.append("(JUST CLEAN SISI PENDEK)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter)

    # Just clean pass
    gcode.append("M08")
    gcode.append(
        f"G01 Z{workpiece_long + parallel_block_short - just_clean_depth:.2f} F{feed_rate / 2:.1f}"
    )  # Plunge
    gcode.append(
        f"G01 X{workpiece_short + 5 + (tool_diameter / 2):.2f} Y{workpiece_thick / 2:.2f} F{feed_rate / 2:.1f}"
    )  # Cut
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter)
    gcode.append("M09")
    pause_process(gcode, spindle_speed)

    ### ADJUSTMENT SHORT SIDE ###
    gcode.append("(ADJUSTMENT SISI PENDEK)")
    tool_back(gcode, z_short_init, safe_tool_distance, tool_diameter)
    gcode.append("M08")
    for pass_num in range(num_passes):
        # Calculate current depth (after just clean)
        current_depth = just_clean_depth + ((pass_num + 1) * depth_of_cut)
        if current_depth > short_stock_thickness:
            current_depth = short_stock_thickness  # Cap at short stock thickness

        # Generate cutting moves
        gcode.append(
            f"G01 Z{workpiece_long + parallel_block_short - current_depth:.2f} F{feed_rate / 2:.1f}"
        )  # Plunge
        if direction == 1:
            adjustment_feed_rate = (
                feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            )
            gcode.append(
                f"G01 X{workpiece_short + 5 + (tool_diameter / 2):.2f} Y{workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = -1
        else:
            adjustment_feed_rate = (
                feed_rate / 2 if num_passes - 1 == pass_num else feed_rate
            )
            gcode.append(
                f"G01 X{-tool_diameter / 2 - safe_tool_distance:.2f} Y{workpiece_thick / 2:.2f} F{adjustment_feed_rate:.1f}"
            )
            direction = 1
    # Program end
    gcode.append(f"G00 Z{z_short_init:.2f}")  # Return to safe height
    gcode.append("M09")
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


import tkinter as tk
from tkinter import messagebox, ttk

# [Your existing functions remain unchanged: tool_back, pause_process, generate_face_mill_gcode, save_gcode_to_file]


class GCodeGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Automatic Facemill Blanking NC Generator")
        self.root.geometry("400x600")

        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Parameters and their default values
        self.parameters = {
            "workpiece_long": 150.0,
            "workpiece_short": 50.0,
            "workpiece_thick": 20.0,
            "parallel_block_long": 0.0,
            "parallel_block_short": 0.0,
            "long_stock_thickness": 5.0,
            "short_stock_thickness": 3.0,
            "tool_diameter": 50.0,
            "feed_rate": 500.0,
            "spindle_speed": 2000.0,
            "depth_of_cut": 1.0,
            "safe_z_distance": 20.0,
            "safe_tool_distance": 5.0,
            "just_clean_fraction": 0.1,
        }

        # Labels and entry fields
        row = 0
        self.entries = {}
        for param, default in self.parameters.items():
            # Convert parameter name to readable label
            label_text = param.replace("_", " ").title()
            ttk.Label(main_frame, text=f"{label_text}:").grid(
                row=row, column=0, sticky=tk.W, pady=2
            )

            self.entries[param] = ttk.Entry(main_frame)
            self.entries[param].grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
            self.entries[param].insert(0, str(default))

            # Add units
            units = "mm" if "fraction" not in param else "%"
            if param == "feed_rate":
                units = "mm/min"
            elif param == "spindle_speed":
                units = "RPM"
            ttk.Label(main_frame, text=units).grid(
                row=row, column=2, sticky=tk.W, pady=2
            )

            row += 1

        # Filename entry
        ttk.Label(main_frame, text="Output Filename:").grid(
            row=row, column=0, sticky=tk.W, pady=2
        )
        self.filename_entry = ttk.Entry(main_frame)
        self.filename_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        self.filename_entry.insert(0, "face_mill_zigzag_adjusted.nc")
        ttk.Label(main_frame, text=".nc").grid(row=row, column=2, sticky=tk.W, pady=2)
        row += 1

        # Generate button
        self.generate_btn = ttk.Button(
            main_frame, text="Generate G-code", command=self.generate_gcode
        )
        self.generate_btn.grid(row=row, column=0, columnspan=3, pady=10)

        # Status label
        self.status_label = ttk.Label(main_frame, text="")
        self.status_label.grid(row=row + 1, column=0, columnspan=3)

        # Configure column weights
        main_frame.columnconfigure(1, weight=1)

    def generate_gcode(self):
        try:
            # Get parameters from entries
            params = {}
            for param in self.parameters:
                value = float(self.entries[param].get())
                if value < 0 and param[:8] == "parallel":
                    raise ValueError(
                        f"{param.replace('_', ' ').title()} must be positive or greater than zero"
                    )
                elif value <= 0 and param[:8] != "parallel":
                    raise ValueError(
                        f"{param.replace('_', ' ').title()} must be positive"
                    )
                params[param] = value

            # Generate G-code
            gcode = generate_face_mill_gcode(**params)

            # Save to file
            filename = self.filename_entry.get()
            if not filename.endswith(".nc"):
                filename += ".nc"
            save_gcode_to_file(gcode, filename)

            # Show generated G-code in a new window
            self.show_gcode_window(gcode)

            self.status_label.config(text=f"G-code generated and saved to {filename}")

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def show_gcode_window(self, gcode):
        # Create new window for G-code preview
        preview_window = tk.Toplevel(self.root)
        preview_window.title(f"G-code Preview {self.filename_entry.get()}")
        preview_window.geometry("400x500")

        # Text widget with scrollbar
        text_frame = ttk.Frame(preview_window, padding="5")
        text_frame.pack(fill=tk.BOTH, expand=True)

        text_widget = tk.Text(text_frame, wrap=tk.NONE)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=text_widget.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Insert G-code
        for line in gcode:
            text_widget.insert(tk.END, line + "\n")
        text_widget.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = GCodeGeneratorGUI(root)
    root.mainloop()

# Generate and save the program
# if __name__ == "__main__":
#     # Customize these parameters as needed
#     gcode = generate_face_mill_gcode(
#         workpiece_long=150.0,  # 150mm long workpiece
#         workpiece_short=50.0,  # 50mm wide workpiece
#         workpiece_thick=20.0,  # 20mm thick workpiece
#         short_stock_thickness=3.0,  # 5mm thick material
#         long_stock_thickness=5.0,  # 3mm thick material
#         tool_diameter=50,  # 50mm face mill
#         feed_rate=500.0,  # 500 mm/min feed rate
#         spindle_speed=2000,  # 2000 RPM
#         depth_of_cut=1.0,  # 1mm per pass
#         safe_z_distance=20.0,  # 20mm safe Z height
#         safe_tool_distance=5.0,  # 5mm safe X distance
#         just_clean_fraction=0.1,  # 10% of stock thickness for just clean
#     )

#     # Print the G-code to console
#     print("Generated G-code:")
#     for line in gcode:
#         print(line)

#     # Save to file (uncomment to save)
#     save_gcode_to_file(gcode, "face_mill_zigzag_adjusted.nc")
